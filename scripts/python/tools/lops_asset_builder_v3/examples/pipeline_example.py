"""
Example pipeline script demonstrating command-line LOPS Asset Builder usage.
This can be run from Houdini's Python Shell, hython, or integrated into a pipeline.
"""

import hou
from tools.lops_asset_builder_v3 import lops_asset_builder_cli

# ============================================================================
# EXAMPLE 1: Simple quick build
# ============================================================================
def example_quick_build():
    """Minimal configuration for quick testing."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Quick Build")
    print("="*60 + "\n")

    result = lops_asset_builder_cli.quick_build(
        asset_path="$JOB/assets/prop.abc",
        textures_path="$JOB/textures",
        asset_name="MyProp",
        create_lookdev=False
    )

    if result.success:
        print(f"✓ Success! Output node: {result.output_node.path()}")
    else:
        print(f"✗ Failed: {result.message}")

    return result


# ============================================================================
# EXAMPLE 2: Build from dictionary configuration
# ============================================================================
def example_dict_config():
    """Build asset using dictionary configuration."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Dictionary Configuration")
    print("="*60 + "\n")

    config = {
        "main_asset_file_path": "$JOB/assets/character.abc",
        "folder_textures": "$JOB/textures/character",
        "asset_name": "Character",
        "asset_variants": [
            "$JOB/assets/character_lod1.abc",
            "$JOB/assets/character_lod2.abc"
        ],
        "asset_vset_name": "lod",
        "create_lookdev": True,
        "create_light_rig": True,
        "enable_env_lights": True,
        "env_light_paths": [
            "$JOB/hdri/studio.exr",
            "$JOB/hdri/outdoor.exr"
        ]
    }

    result = lops_asset_builder_cli.build_asset(config)
    print(f"Result: {result}")
    return result


# ============================================================================
# EXAMPLE 3: Build from JSON config file
# ============================================================================
def example_json_config():
    """Build asset using JSON configuration file."""
    print("\n" + "="*60)
    print("EXAMPLE 3: JSON Configuration File")
    print("="*60 + "\n")

    # Path to JSON config file
    config_path = "$CUSTOM_TOOLS/scripts/python/tools/lops_asset_builder_v3/examples/full_config.json"
    config_path = hou.text.expandString(config_path)

    result = lops_asset_builder_cli.build_asset_from_file(config_path, verbose=True)
    print(f"Result: {result}")
    return result


# ============================================================================
# EXAMPLE 4: Batch processing multiple assets
# ============================================================================
def example_batch_build():
    """Build multiple assets in batch mode."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Batch Processing")
    print("="*60 + "\n")

    configs = [
        {
            "main_asset_file_path": "$JOB/assets/prop1.abc",
            "folder_textures": "$JOB/textures/prop1",
            "asset_name": "Prop1",
            "create_lookdev": False
        },
        {
            "main_asset_file_path": "$JOB/assets/prop2.abc",
            "folder_textures": "$JOB/textures/prop2",
            "asset_name": "Prop2",
            "create_lookdev": False
        },
        {
            "main_asset_file_path": "$JOB/assets/hero_asset.abc",
            "folder_textures": "$JOB/textures/hero",
            "asset_name": "HeroAsset",
            "create_lookdev": True,
            "create_light_rig": True
        }
    ]

    results = lops_asset_builder_cli.build_assets_batch(configs, verbose=True)

    # Print summary
    for i, result in enumerate(results, 1):
        status = "✓" if result.success else "✗"
        print(f"{status} Asset {i}: {result.message}")

    return results


# ============================================================================
# EXAMPLE 5: Error handling and validation
# ============================================================================
def example_error_handling():
    """Demonstrate error handling for invalid configurations."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Error Handling")
    print("="*60 + "\n")

    # Invalid config (missing required fields)
    invalid_config = {
        "asset_name": "InvalidAsset"
        # Missing main_asset_file_path and folder_textures
    }

    try:
        result = lops_asset_builder_cli.build_asset(invalid_config)
        print(f"Result: {result}")
    except Exception as e:
        print(f"✓ Caught expected error: {e}")

    # Invalid file path
    invalid_path_config = {
        "main_asset_file_path": "/nonexistent/path/model.abc",
        "folder_textures": "/nonexistent/textures"
    }

    try:
        result = lops_asset_builder_cli.build_asset(invalid_path_config)
        print(f"Result: {result}")
    except Exception as e:
        print(f"✓ Caught expected error: {e}")


# ============================================================================
# EXAMPLE 6: Create and save configuration programmatically
# ============================================================================
def example_create_save_config():
    """Create configuration object and save to JSON file."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Create and Save Configuration")
    print("="*60 + "\n")

    # Create config object
    config = lops_asset_builder_cli.AssetBuilderConfig(
        main_asset_file_path="$JOB/assets/building.abc",
        folder_textures="$JOB/textures/building",
        asset_name="Building",
        asset_variants=[
            "$JOB/assets/building_winter.abc",
            "$JOB/assets/building_damaged.abc"
        ],
        mtl_variants=[
            "$JOB/textures/building/clean",
            "$JOB/textures/building/weathered"
        ],
        create_lookdev=True
    )

    # Save to file
    output_path = "/tmp/building_config.json"
    config.to_json_file(output_path)
    print(f"✓ Configuration saved to: {output_path}")

    # Load it back
    loaded_config = lops_asset_builder_cli.AssetBuilderConfig.from_json_file(output_path)
    print(f"✓ Configuration loaded: {loaded_config.asset_name}")

    return config


# ============================================================================
# EXAMPLE 7: Integration with existing pipeline
# ============================================================================
def example_pipeline_integration():
    """Example of integrating with a production pipeline."""
    print("\n" + "="*60)
    print("EXAMPLE 7: Pipeline Integration")
    print("="*60 + "\n")

    # Simulate getting asset info from a pipeline database/system
    asset_info = {
        "asset_id": "CHAR_001",
        "asset_type": "character",
        "asset_name": "MainCharacter",
        "geo_path": "$JOB/publish/characters/main/main_character_v003.abc",
        "texture_path": "$JOB/publish/characters/main/textures/v002",
        "variants": {
            "geo": [
                "$JOB/publish/characters/main/main_character_v003_proxy.abc"
            ],
            "mtl": [
                "$JOB/publish/characters/main/textures/v002_damaged",
                "$JOB/publish/characters/main/textures/v002_clean"
            ]
        },
        "lookdev_enabled": True,
        "hdri_set": "studio_standard"
    }

    # Convert pipeline data to builder config
    config = {
        "main_asset_file_path": asset_info["geo_path"],
        "folder_textures": asset_info["texture_path"],
        "asset_name": asset_info["asset_name"],
        "asset_variants": asset_info["variants"]["geo"],
        "mtl_variants": asset_info["variants"]["mtl"],
        "create_lookdev": asset_info["lookdev_enabled"],
        "create_light_rig": True,
        "enable_env_lights": True,
        "env_light_paths": [
            f"$JOB/hdri/{asset_info['hdri_set']}_01.exr",
            f"$JOB/hdri/{asset_info['hdri_set']}_02.exr"
        ]
    }

    print(f"Building asset: {asset_info['asset_id']} - {asset_info['asset_name']}")
    result = lops_asset_builder_cli.build_asset(config)

    if result.success:
        print(f"✓ Asset built successfully in {result.duration:.2f}s")
        print(f"  Output node: {result.output_node.path()}")

        # Could now register the output in pipeline database, send notifications, etc.
        # pipeline_db.register_asset(asset_info['asset_id'], result.output_node.path())

    else:
        print(f"✗ Build failed: {result.message}")
        # Could send error notification to pipeline monitoring system
        # pipeline_monitor.report_error(asset_info['asset_id'], result.error)

    return result


# ============================================================================
# EXAMPLE 8: Generate example config file
# ============================================================================
def example_generate_config():
    """Generate an example configuration file for reference."""
    print("\n" + "="*60)
    print("EXAMPLE 8: Generate Example Configuration")
    print("="*60 + "\n")

    output_path = "/tmp/example_asset_config.json"
    created_path = lops_asset_builder_cli.create_example_config(output_path)
    print(f"✓ Example configuration created at: {created_path}")
    print("  Edit this file with your asset paths and use it as a template.")


# ============================================================================
# MAIN: Run all examples
# ============================================================================
def run_all_examples():
    """Run all examples in sequence."""
    print("\n" + "="*80)
    print(" LOPS ASSET BUILDER CLI - PIPELINE EXAMPLES")
    print("="*80)

    # Note: Most examples will fail without actual asset files
    # These are templates showing how to use the CLI interface

    examples = [
        ("Quick Build", example_quick_build),
        ("Dictionary Config", example_dict_config),
        ("JSON Config File", example_json_config),
        ("Batch Processing", example_batch_build),
        ("Error Handling", example_error_handling),
        ("Create/Save Config", example_create_save_config),
        ("Pipeline Integration", example_pipeline_integration),
        ("Generate Config", example_generate_config)
    ]

    for name, func in examples:
        try:
            print(f"\n{'='*80}")
            print(f" Running: {name}")
            print(f"{'='*80}")
            func()
        except Exception as e:
            print(f"\n✗ Example '{name}' failed (expected if assets don't exist): {e}")

    print("\n" + "="*80)
    print(" Examples Complete")
    print("="*80 + "\n")


# To run from Houdini Python Shell:
# from tools.lops_asset_builder_v3.examples import pipeline_example
# pipeline_example.example_quick_build()
# pipeline_example.run_all_examples()
