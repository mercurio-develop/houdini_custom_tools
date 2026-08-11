"""
Houdini MCP Server - Socket-based server running inside Houdini

This server listens on localhost:9876 and processes commands from the MCP bridge.
It executes commands within Houdini's environment and returns results.
"""

import json
import socket
import threading
import sys
import io
import os
import base64
from contextlib import redirect_stdout, redirect_stderr

import hou
from PySide6 import QtCore

# Import asset folder scanner
try:
    import sys
    import os
    # Add parent directory to path for module imports
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    from modules.asset_folder_scanner import scan_asset_folder
    SCANNER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: asset_folder_scanner module not found: {e}")
    scan_asset_folder = None
    SCANNER_AVAILABLE = False

try:
    from tools.lops_asset_builder_v3.lops_asset_builder_cli import build_asset_from_file
    from tools.lops_asset_builder_v3.material_validator import validate_materials
    ASSET_BUILDER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: lops_asset_builder_v3 modules not found: {e}")
    build_asset_from_file = None
    validate_materials = None
    ASSET_BUILDER_AVAILABLE = False

try:
    import custom_utils
    CUSTOM_UTILS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: custom_utils module not found: {e}")
    custom_utils = None
    CUSTOM_UTILS_AVAILABLE = False

try:
    from tools.psx_tools.psx_asset_builder import run_psx_asset_build
    from tools.psx_tools.psx_config import PSXAssetConfig, PSXBuildConfig
    PSX_TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: psx_tools modules not found: {e}")
    run_psx_asset_build = None
    PSXAssetConfig = None
    PSXBuildConfig = None
    PSX_TOOLS_AVAILABLE = False

try:
    from tools.lop_network_organizer import organize_current_stage
    LOP_ORGANIZER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: lop_network_organizer module not found: {e}")
    organize_current_stage = None
    LOP_ORGANIZER_AVAILABLE = False

try:
    from HMCP.handler_registry import HANDLER_REGISTRY
except ImportError as e:
    print(f"Warning: HMCP handler_registry not found: {e}")
    HANDLER_REGISTRY = {}

COMMAND_TIMEOUT_SECONDS = 600
RECV_BUFFER_SIZE = 65536


class HoudiniMCPServer:
    """
    TCP server that runs inside Houdini and processes MCP commands.

    Uses Qt timers to avoid threading issues with Houdini's main thread.
    Communicates via JSON messages over TCP socket.
    """

    def __init__(self, host='localhost', port=9876):
        """
        Initialize the Houdini MCP server.

        Args:
            host (str): Host to bind to (default: localhost)
            port (int): Port to listen on (default: 9876)
        """
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.is_running = False
        self.timer = None
        self.command_timeout = COMMAND_TIMEOUT_SECONDS

        # Command registry
        self.commands = {
            'get_scene_info': self.handle_get_scene_info,
            'get_stage_summary': self.handle_get_stage_summary,
            'create_node': self.handle_create_node,
            'modify_node': self.handle_modify_node,
            'delete_node': self.handle_delete_node,
            'get_node_info': self.handle_get_node_info,
            'execute_code': self.handle_execute_code,
            'set_material': self.handle_set_material,
            'scan_asset_folder': self.handle_scan_asset_folder,
            'run_lops_asset_builder': self.handle_run_lops_asset_builder,
            'run_psx_asset_build': self.handle_run_psx_asset_build,
            'validate_asset_folder': self.handle_validate_asset_folder,
            'reload_custom_tools': self.handle_reload_custom_tools,
            'cook_node': self.handle_cook_node,
            'organize_lop_network': self.handle_organize_lop_network,
            # Extended handlers (HMCP/handlers/)
            **{name: self._make_registry_handler(name) for name in HANDLER_REGISTRY},
        }

        # Start the server
        self._start()

    def _make_registry_handler(self, command_name):
        fn = HANDLER_REGISTRY[command_name]

        def _handler(params):
            return fn(params)

        _handler.__name__ = f"handle_{command_name}"
        return _handler

    def _start(self):
        """Start the TCP server and begin listening for connections."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            self.is_running = True

            print(f"Houdini MCP Server listening on {self.host}:{self.port} (waiting for MCP agent)")

            # Start listening thread
            self.listen_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.listen_thread.start()

        except Exception as e:
            print(f"Failed to start Houdini MCP Server: {e}")
            self.is_running = False
            # Clean up socket if it was created
            if self.server_socket:
                try:
                    self.server_socket.close()
                except:
                    pass
                self.server_socket = None

    def _accept_connections(self):
        """Accept incoming client connections (runs in separate thread)."""
        while self.is_running:
            try:
                self.client_socket, addr = self.server_socket.accept()
                print(f"MCP agent connected from {addr}")

                # Start receiving messages
                self._receive_messages()

            except Exception as e:
                if self.is_running:
                    print(f"Connection error: {e}")

    def _receive_messages(self):
        """Receive and process messages from client."""
        buffer = ""

        while self.is_running and self.client_socket:
            try:
                data = self.client_socket.recv(RECV_BUFFER_SIZE).decode('utf-8')
                if not data:
                    break

                buffer += data

                # Process complete JSON messages
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    if message.strip():
                        self._process_message(message.strip())

            except Exception as e:
                print(f"Error receiving message: {e}")
                break

        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            print("MCP agent disconnected")

    def _process_message(self, message):
        """
        Process a received JSON message.

        Args:
            message (str): JSON-encoded command message
        """
        try:
            command_data = json.loads(message)
            command = command_data.get('command')
            params = command_data.get('params', {})
            request_id = command_data.get('id')

            if command in self.commands:
                result = self._dispatch_command(command, params)
                response = {
                    'id': request_id,
                    'status': 'success',
                    'result': result,
                }
            else:
                response = {
                    'id': request_id,
                    'status': 'error',
                    'error': f'Unknown command: {command}',
                }

            self._send_response(response)

        except Exception as e:
            error_response = {
                'id': request_id if 'request_id' in locals() else None,
                'status': 'error',
                'error': str(e)
            }
            self._send_response(error_response)

    def _run_on_main_thread(self, func, params):
        """Execute hou.* work on Houdini's main thread; block socket thread until done."""
        result_holder = {}
        event = threading.Event()

        def _execute():
            try:
                result_holder['result'] = func(params)
            except Exception as exc:
                result_holder['error'] = exc
            finally:
                event.set()

        deferred = getattr(getattr(hou, "ui", None), "executeDeferred", None)
        if callable(deferred):
            deferred(_execute)
        else:
            try:
                import hdefereval

                hdefereval.executeDeferred(_execute)
            except ImportError:
                QtCore.QTimer.singleShot(0, _execute)

        if not event.wait(timeout=self.command_timeout):
            raise TimeoutError(f"Command timed out after {self.command_timeout}s")
        if 'error' in result_holder:
            raise result_holder['error']
        return result_holder.get('result')

    def _dispatch_command(self, command, params):
        handler = self.commands[command]
        return self._run_on_main_thread(handler, params)

    def _send_response(self, response):
        """
        Send a JSON response to the client.

        Args:
            response (dict): Response data to send
        """
        if self.client_socket:
            try:
                message = json.dumps(response) + '\n'
                self.client_socket.sendall(message.encode('utf-8'))
            except Exception as e:
                print(f"Error sending response: {e}")

    # =========================================================================
    # Command Handlers
    # =========================================================================

    def handle_get_scene_info(self, params):
        """Get information about the current Houdini scene."""
        hip_file = hou.hipFile.path()
        hip_name = hou.hipFile.basename()
        include_all = params.get('include_all_nodes', False)
        context_path = params.get('context_path')
        node_type = params.get('node_type')
        max_nodes = int(params.get('max_nodes', 200))

        nodes = []
        truncated = False

        if include_all or context_path:
            root = hou.node(context_path) if context_path else hou.node('/')
            if root is None:
                raise ValueError(f"Context node not found: {context_path}")
            iterable = root.allSubChildren() if context_path else hou.node('/').allSubChildren()
            for node in iterable:
                if node_type and node.type().name() != node_type:
                    continue
                nodes.append({
                    'path': node.path(),
                    'type': node.type().name(),
                    'name': node.name(),
                })
                if len(nodes) >= max_nodes:
                    truncated = True
                    break

        selected = []
        for node in hou.selectedNodes():
            selected.append({'path': node.path(), 'type': node.type().name(), 'name': node.name()})

        return {
            'hip_file': hip_file,
            'hip_name': hip_name,
            'frame': hou.frame(),
            'fps': hou.fps(),
            'node_count': len(nodes),
            'nodes_truncated': truncated,
            'nodes': nodes,
            'selected_nodes': selected,
        }

    def handle_get_stage_summary(self, params):
        """Lightweight summary of /stage LOP network."""
        stage_path = params.get('stage_path', '/stage')
        stage = hou.node(stage_path)
        if stage is None:
            raise ValueError(f"Stage node not found: {stage_path}")

        children = []
        for child in stage.children():
            children.append({
                'path': child.path(),
                'type': child.type().name(),
                'name': child.name(),
            })

        component_outputs = []
        for node in stage.allSubChildren():
            if node.type().name() == 'componentoutput':
                component_outputs.append({
                    'path': node.path(),
                    'name': node.name(),
                    'rootprim': node.evalParm('rootprim') if node.parm('rootprim') else None,
                })

        return {
            'stage_path': stage.path(),
            'child_count': len(children),
            'children': children,
            'component_outputs': component_outputs,
            'selected_nodes': [
                {'path': n.path(), 'type': n.type().name()} for n in hou.selectedNodes()
            ],
            'hip_name': hou.hipFile.basename(),
            'frame': hou.frame(),
        }

    def handle_create_node(self, params):
        """
        Create a new node in Houdini.

        Args:
            params (dict): Contains 'parent_path', 'node_type', and optional 'node_name'

        Returns:
            dict: Information about the created node
        """
        parent_path = params.get('parent_path', '/obj')
        node_type = params.get('node_type')
        node_name = params.get('node_name')

        parent = hou.node(parent_path)
        if not parent:
            raise ValueError(f"Parent node not found: {parent_path}")

        # Create the node
        if node_name:
            node = parent.createNode(node_type, node_name)
        else:
            node = parent.createNode(node_type)

        # Set parameters if provided
        if 'parameters' in params:
            for parm_name, parm_value in params['parameters'].items():
                try:
                    node.parm(parm_name).set(parm_value)
                except:
                    pass

        return {
            'path': node.path(),
            'name': node.name(),
            'type': node.type().name()
        }

    def handle_modify_node(self, params):
        """
        Modify parameters of an existing node.

        Args:
            params (dict): Contains 'node_path' and 'parameters'

        Returns:
            dict: Status of the modification
        """
        node_path = params.get('node_path')
        parameters = params.get('parameters', {})

        node = hou.node(node_path)
        if not node:
            raise ValueError(f"Node not found: {node_path}")

        # Set parameters
        modified = []
        for parm_name, parm_value in parameters.items():
            try:
                node.parm(parm_name).set(parm_value)
                modified.append(parm_name)
            except Exception as e:
                print(f"Failed to set {parm_name}: {e}")

        return {
            'node_path': node_path,
            'modified_parameters': modified
        }

    def handle_delete_node(self, params):
        """
        Delete a node from the scene.

        Args:
            params (dict): Contains 'node_path'

        Returns:
            dict: Status of deletion
        """
        node_path = params.get('node_path')

        node = hou.node(node_path)
        if not node:
            raise ValueError(f"Node not found: {node_path}")

        node.destroy()

        return {
            'deleted': node_path
        }

    def handle_get_node_info(self, params):
        """
        Get detailed information about a node.

        Args:
            params (dict): Contains 'node_path'

        Returns:
            dict: Node information including parameters and connections
        """
        node_path = params.get('node_path')

        node = hou.node(node_path)
        if not node:
            raise ValueError(f"Node not found: {node_path}")

        # Get parameters
        parms = {}
        for parm in node.parms():
            try:
                parms[parm.name()] = parm.eval()
            except:
                pass

        # Get inputs and outputs
        inputs = [inp.path() if inp else None for inp in node.inputs()]
        outputs = [out.path() for out in node.outputs()]

        return {
            'path': node.path(),
            'name': node.name(),
            'type': node.type().name(),
            'parameters': parms,
            'inputs': inputs,
            'outputs': outputs
        }

    def handle_execute_code(self, params):
        """
        Execute Python code within Houdini's environment.

        Args:
            params (dict): Contains 'code' string to execute

        Returns:
            dict: Execution result with stdout and stderr
        """
        code = params.get('code', '')
        return_expr = params.get('return_expr')

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        result = None
        error = None
        return_value = None

        exec_globals = {'hou': hou, '__builtins__': __builtins__}
        if CUSTOM_UTILS_AVAILABLE:
            exec_globals['custom_utils'] = custom_utils
        try:
            from pxr import Usd
            exec_globals['Usd'] = Usd
        except ImportError:
            pass

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                with hou.undos.group("MCP execute_code"):
                    exec(code, exec_globals)
                    if return_expr:
                        return_value = eval(return_expr, exec_globals)
                result = "Code executed successfully"
        except Exception as e:
            error = str(e)

        response = {
            'result': result,
            'error': error,
            'stdout': stdout_capture.getvalue(),
            'stderr': stderr_capture.getvalue(),
        }
        if return_expr is not None:
            response['return_value'] = repr(return_value) if return_value is not None else None
        return response

    def handle_set_material(self, params):
        """
        Create and assign a material to geometry.

        Args:
            params (dict): Contains 'geo_path', 'material_name', and material properties

        Returns:
            dict: Material creation status
        """
        geo_path = params.get('geo_path')
        material_name = params.get('material_name', 'material')

        geo_node = hou.node(geo_path)
        if not geo_node:
            raise ValueError(f"Geometry node not found: {geo_path}")

        # Create material network if it doesn't exist
        mat_context = hou.node('/mat')
        if not mat_context:
            mat_context = hou.node('/').createNode('matnet', 'mat')

        # Create a principled shader
        shader = mat_context.createNode('principledshader', material_name)

        # Set material properties if provided
        if 'diffuse_color' in params:
            shader.parm('basecolor').set(params['diffuse_color'])

        # Assign to geometry (simplified - would need material node in between)
        return {
            'material_path': shader.path(),
            'assigned_to': geo_path
        }

    def handle_scan_asset_folder(self, params):
        """
        Scan an asset folder and identify main assets, variants, and textures.

        Args:
            params (dict): Contains 'folder_path' and optional 'geo_subfolder', 'tex_subfolder'

        Returns:
            dict: Scan results with main_asset, asset_variants, main_textures, material_variants
        """
        if not SCANNER_AVAILABLE:
            return {
                'error': 'Asset folder scanner module not available',
                'status': 'error'
            }

        folder_path = params.get('folder_path')
        if not folder_path:
            raise ValueError("No folder_path provided")

        # Expand Houdini environment variables
        folder_path = hou.text.expandString(folder_path)

        # Optional subfolder names
        geo_subfolder = params.get('geo_subfolder', 'geo')
        tex_subfolder = params.get('tex_subfolder', 'tex')

        try:
            # Scan the folder
            result = scan_asset_folder(folder_path, geo_subfolder, tex_subfolder)

            # Return the scan results
            return {
                'status': 'success',
                'folder_path': folder_path,
                'scan_result': result
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'folder_path': folder_path
            }

    def _validation_result_to_dict(self, result):
        """Serialize MaterialValidationResult for JSON responses."""
        return {
            'materials_expected': sorted(result.materials_expected),
            'materials_available': sorted(result.materials_available),
            'materials_missing': sorted(result.materials_missing),
            'has_warnings': result.has_warnings,
            'warnings': result.warnings,
            'info': result.info,
            'summary': result.get_summary(),
        }

    def _build_result_to_dict(self, result):
        """Serialize BuildResult for JSON responses."""
        output_path = None
        if result.output_node:
            try:
                output_path = result.output_node.path()
            except hou.ObjectWasDeleted:
                output_path = None
        return {
            'success': result.success,
            'message': result.message,
            'duration': result.duration,
            'error': str(result.error) if result.error else None,
            'output_node': output_path,
        }

    def handle_run_lops_asset_builder(self, params):
        """
        Run LOPS Asset Builder v3 from a JSON config file or inline config dict.

        Args:
            params (dict): config_filepath and/or config, optional verbose flag

        Returns:
            dict: Build result summary
        """
        if not ASSET_BUILDER_AVAILABLE:
            return {'status': 'error', 'error': 'LOPS Asset Builder modules not available'}

        config_filepath = params.get('config_filepath')
        config_dict = params.get('config')
        verbose = params.get('verbose', True)

        if config_filepath:
            config_filepath = hou.text.expandString(config_filepath)
            result = build_asset_from_file(config_filepath, verbose=verbose)
        elif config_dict:
            from tools.lops_asset_builder_v3.lops_asset_builder_cli import build_asset
            result = build_asset(config_dict)
        else:
            raise ValueError("Provide config_filepath or config")

        return {
            'status': 'success' if result.success else 'error',
            'build_result': self._build_result_to_dict(result),
        }

    def handle_validate_asset_folder(self, params):
        """
        Validate materials for an asset folder or explicit geometry/texture paths.

        Args:
            params (dict): folder_path OR main_asset_file_path + folder_textures

        Returns:
            dict: Validation results
        """
        if not ASSET_BUILDER_AVAILABLE:
            return {'status': 'error', 'error': 'Material validator not available'}

        folder_path = params.get('folder_path')
        geo_subfolder = params.get('geo_subfolder', 'geo')
        tex_subfolder = params.get('tex_subfolder', 'tex')
        lowercase = params.get('lowercase', False)

        if folder_path:
            if not SCANNER_AVAILABLE:
                return {'status': 'error', 'error': 'Asset folder scanner not available'}
            folder_path = hou.text.expandString(folder_path)
            scan = scan_asset_folder(folder_path, geo_subfolder, tex_subfolder)
            main_asset = scan.get('main_asset')
            folder_textures = scan.get('main_textures')
            asset_variants = scan.get('asset_variants') or []
            mtl_variants = scan.get('material_variants') or []
            if not main_asset or not folder_textures:
                return {
                    'status': 'error',
                    'error': 'Scan did not find main asset and texture folder',
                    'scan_result': scan,
                }
        else:
            main_asset = params.get('main_asset_file_path')
            folder_textures = params.get('folder_textures')
            asset_variants = params.get('asset_variants') or []
            mtl_variants = params.get('mtl_variants') or []
            scan = None
            if main_asset:
                main_asset = hou.text.expandString(main_asset)
            if folder_textures:
                folder_textures = hou.text.expandString(folder_textures)
            asset_variants = [hou.text.expandString(p) for p in asset_variants]
            mtl_variants = [hou.text.expandString(p) for p in mtl_variants]

        if not main_asset or not folder_textures:
            raise ValueError(
                "Provide folder_path or both main_asset_file_path and folder_textures"
            )

        asset_paths = [main_asset] + list(asset_variants)
        validation = validate_materials(
            asset_paths=asset_paths,
            texture_folder=folder_textures,
            texture_variants=mtl_variants or None,
            lowercase=lowercase,
        )

        response = {
            'status': 'success',
            'main_asset_file_path': main_asset,
            'folder_textures': folder_textures,
            'asset_variants': asset_variants,
            'mtl_variants': mtl_variants,
            'validation': self._validation_result_to_dict(validation),
        }
        if scan is not None:
            response['scan_result'] = scan
        if folder_path:
            response['folder_path'] = folder_path
        return response

    def handle_reload_custom_tools(self, params):
        """
        Reload the custom_tools Houdini package and Python modules.

        Args:
            params (dict): optional reload_modules (default True)

        Returns:
            dict: Reload status
        """
        if not CUSTOM_UTILS_AVAILABLE:
            return {'status': 'error', 'error': 'custom_utils module not available'}

        reload_modules = params.get('reload_modules', True)
        kwargs = {'altclick': reload_modules}
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                custom_utils.reload_packages(kwargs)
            return {
                'status': 'success',
                'reload_modules': reload_modules,
                'stdout': stdout_capture.getvalue(),
                'stderr': stderr_capture.getvalue(),
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'stdout': stdout_capture.getvalue(),
                'stderr': stderr_capture.getvalue(),
            }

    def handle_run_psx_asset_build(self, params):
        """Run PSX preprocessing + LOPs Asset Builder pipeline."""
        if not PSX_TOOLS_AVAILABLE:
            return {'status': 'error', 'error': 'PSX tools modules not available'}

        psx_dict = params.get('psx') or {}
        psx_cfg = PSXAssetConfig.from_dict(psx_dict) if isinstance(psx_dict, dict) else PSXAssetConfig()

        main_asset = hou.text.expandString(params.get('main_asset_file_path', ''))
        folder_textures = hou.text.expandString(params.get('folder_textures', ''))
        asset_name = params.get('asset_name', '')

        build = PSXBuildConfig(
            main_asset_file_path=main_asset,
            folder_textures=folder_textures,
            asset_name=asset_name,
            psx=psx_cfg,
            run_lops_asset_builder=params.get('run_lops_asset_builder', True),
            stage_context_path=params.get('stage_context_path', '/stage'),
        )

        success = run_psx_asset_build(build)
        return {
            'status': 'success' if success else 'error',
            'success': success,
            'main_asset_file_path': main_asset,
            'folder_textures': folder_textures,
        }

    def handle_cook_node(self, params):
        """Cook a LOP/SOP node and return basic stage stats."""
        node_path = params.get('node_path')
        if not node_path:
            raise ValueError("node_path is required")

        node = hou.node(node_path)
        if node is None:
            raise ValueError(f"Node not found: {node_path}")

        force = params.get('force', True)
        node.cook(force=force)

        stage = None
        prim_count = 0
        if hasattr(node, 'stage'):
            try:
                stage = node.stage()
                if stage is not None:
                    prim_count = sum(1 for _ in stage.Traverse())
            except Exception:
                pass

        return {
            'path': node.path(),
            'type': node.type().name(),
            'cooked': True,
            'has_stage': stage is not None,
            'prim_count': prim_count,
        }

    def handle_organize_lop_network(self, params):
        """Organize the current LOP/stage network."""
        if not LOP_ORGANIZER_AVAILABLE:
            return {'status': 'error', 'error': 'lop_network_organizer module not available'}

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                organize_current_stage(
                    merge=params.get('merge', True),
                    layout=params.get('layout', True),
                    boxes=params.get('boxes', False),
                )
            return {
                'status': 'success',
                'stdout': stdout_capture.getvalue(),
                'stderr': stderr_capture.getvalue(),
            }
        except Exception as exc:
            return {
                'status': 'error',
                'error': str(exc),
                'stdout': stdout_capture.getvalue(),
                'stderr': stderr_capture.getvalue(),
            }

    # =========================================================================
    # Server Control
    # =========================================================================

    def shutdown(self):
        """Shutdown the server and close all connections."""
        self.is_running = False

        if self.client_socket:
            self.client_socket.close()

        if self.server_socket:
            self.server_socket.close()

        print("Houdini MCP Server shutdown")
