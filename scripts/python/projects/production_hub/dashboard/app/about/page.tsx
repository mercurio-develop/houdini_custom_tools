export default function AboutPage() {
  return (
    <main>
      <h1>VFX pipeline</h1>
      <p>
        <strong>Houdini</strong> — artists build or reference USD (LOPS / KB3D library) and publish via
        Production Hub PySide UI.
      </p>
      <p>
        <strong>ftrack</strong> — tasks and published asset versions (system of record for production
        tracking).
      </p>
      <p>
        <strong>Iconik</strong> — MAM metadata linked to ftrack task IDs, USD paths, and optional KB3D
        asset codes.
      </p>
      <h2>Repository docs</h2>
      <ul>
        <li>
          <code>projects/production_hub/VFX_PIPELINE.md</code> — full flow and demo script
        </li>
        <li>
          <code>PORTFOLIO.md</code> — portfolio overview at python repo root
        </li>
        <li>
          <code>integrations/workflows/publish_usd_deliverable.py</code> — single publish orchestrator
        </li>
      </ul>
      <h2>Run locally</h2>
      <pre style={{ background: "#f4f4f4", padding: "1rem", overflow: "auto" }}>
        {`cd "$CUSTOM_TOOLS/scripts/python"
export PYTHONPATH=.
uvicorn integrations.http_api:app --port 8765

cd projects/production_hub/dashboard
npm run dev`}
      </pre>
    </main>
  );
}
