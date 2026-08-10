import TaskBrowser from "./components/TaskBrowser";

export default function Home() {
  return (
    <main>
      <h1>Production Hub</h1>
      <p>
        Iconik · ftrack · Houdini — read-only ftrack browser backed by the shared Python integration
        layer. Publish and Iconik linking run from Houdini, MCP, or <code>POST /publish</code>.
      </p>
      <TaskBrowser />
    </main>
  );
}
