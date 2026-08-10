# Production Hub — Portfolio overview

**VFX pipeline integration:** **Houdini** (artist UI) · **ftrack** (tracking/versions) · **Iconik** (MAM metadata).

## What this demonstrates

- **Pipeline design:** One Python integration layer used by DCC UI, MCP, and a Next.js dashboard.
- **USD deliverables:** Publish library or LOPS-built USD to ftrack; mirror IDs and paths in Iconik.
- **TD tooling:** PySide6 Production Hub in Houdini (Connection → Task → Build → Publish).

Deep dive: [VFX_PIPELINE.md](projects/production_hub/VFX_PIPELINE.md).

## Quick start (public integration layer)

```bash
cd "$CUSTOM_TOOLS/scripts/python"
pip install -r requirements-integrations.txt
export PYTHONPATH=.

# API
uvicorn integrations.http_api:app --port 8765

# Dashboard (separate terminal)
cd projects/production_hub/dashboard && npm install && npm run dev
```

Configure ftrack + Iconik: [projects/production_hub/README.md](projects/production_hub/README.md).

## Prior experience (summary)

Media distribution and MAM-adjacent systems at Northshore Automation: metadata platforms (Akomi-style), ISCI delivery orchestration (Distro Hub patterns), and ops portals (Django/React). This repo focuses on **VFX/post** integration patterns relevant to Backlight and similar studios.

## Local-only (not required on GitHub)

- `config/integrations.json` and `config/projects_config.json` — studio credentials and paths (copy from the `*.example.json` templates in-repo)

The LOPs builder, kb3d toolkit, HMCP, and Production Hub all ship in this repo; see [ARCHITECTURE.md](ARCHITECTURE.md).

Demo video can show KB3D library → Houdini publish → ftrack/Iconik; the repo ships a [minimal sample USD](projects/production_hub/samples/sample_assembly.usda) for sandbox publish tests.
