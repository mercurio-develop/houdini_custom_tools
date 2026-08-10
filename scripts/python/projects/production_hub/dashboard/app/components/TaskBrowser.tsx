"use client";

import { useCallback, useEffect, useState } from "react";

type Project = { id: string; name: string };
type Task = {
  id: string;
  name: string;
  status: string;
  parent_name: string;
  link?: string;
};
type TaskContext = {
  id: string;
  name: string;
  status: string;
  project_name: string;
  parent_name: string;
  parent_type: string | null;
  link: string;
};

function apiBase() {
  return "/api";
}

export default function TaskBrowser() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [context, setContext] = useState<TaskContext | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const loadProjects = useCallback(async () => {
    const res = await fetch(`${apiBase()}/ftrack/projects`, { cache: "no-store" });
    if (!res.ok) throw new Error(await res.text());
    const data: Project[] = await res.json();
    setProjects(data);
    if (data.length && !projectId) setProjectId(data[0].id);
  }, [projectId]);

  const loadTasks = useCallback(async (pid: string) => {
    if (!pid) return;
    const res = await fetch(`${apiBase()}/ftrack/projects/${pid}/tasks`, { cache: "no-store" });
    if (!res.ok) throw new Error(await res.text());
    const data: Task[] = await res.json();
    setTasks(data);
    setSelectedId("");
    setContext(null);
  }, []);

  const loadContext = useCallback(async (taskId: string) => {
    const res = await fetch(`${apiBase()}/ftrack/tasks/${taskId}`, { cache: "no-store" });
    if (!res.ok) throw new Error(await res.text());
    setContext(await res.json());
  }, []);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        await loadProjects();
        setError("");
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, [loadProjects]);

  useEffect(() => {
    if (!projectId) return;
    (async () => {
      try {
        await loadTasks(projectId);
        setError("");
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    })();
  }, [projectId, loadTasks]);

  useEffect(() => {
    if (!selectedId) return;
    (async () => {
      try {
        await loadContext(selectedId);
        setError("");
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    })();
  }, [selectedId, loadContext]);

  if (loading) return <p>Loading ftrack projects…</p>;

  if (error && !projects.length) {
    return (
      <section style={{ color: "#a33" }}>
        <h2>API unavailable</h2>
        <pre>{error}</pre>
        <p>
          Start: <code>uvicorn integrations.http_api:app --port 8765</code>
        </p>
      </section>
    );
  }

  return (
    <section>
      <label>
        Project{" "}
        <select
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
          style={{ marginLeft: 8, minWidth: 240 }}
        >
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </label>

      {error && (
        <p style={{ color: "#a33", marginTop: "1rem" }}>
          <small>{error}</small>
        </p>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginTop: "1.5rem" }}>
        <div>
          <h2>Tasks ({tasks.length})</h2>
          <ul style={{ listStyle: "none", padding: 0, maxHeight: 420, overflow: "auto" }}>
            {tasks.map((t) => (
              <li key={t.id} style={{ marginBottom: 6 }}>
                <button
                  type="button"
                  onClick={() => setSelectedId(t.id)}
                  style={{
                    width: "100%",
                    textAlign: "left",
                    padding: "8px 10px",
                    cursor: "pointer",
                    background: selectedId === t.id ? "#eef4ff" : "#f7f7f7",
                    border: "1px solid #ddd",
                    borderRadius: 4,
                  }}
                >
                  <strong>{t.name}</strong>
                  <br />
                  <small>
                    {t.status} · {t.parent_name}
                  </small>
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h2>Task detail</h2>
          {!context && <p>Select a task to load ftrack context for publish/MCP.</p>}
          {context && (
            <dl style={{ lineHeight: 1.6 }}>
              <dt>Name</dt>
              <dd>{context.name}</dd>
              <dt>Status</dt>
              <dd>{context.status}</dd>
              <dt>Project</dt>
              <dd>{context.project_name}</dd>
              <dt>Parent</dt>
              <dd>
                {context.parent_name} ({context.parent_type || "—"})
              </dd>
              <dt>Task ID</dt>
              <dd>
                <code>{context.id}</code>
              </dd>
              <dt>Iconik search hint</dt>
              <dd>
                <code>ftrack_task_id:{context.id}</code>
              </dd>
            </dl>
          )}
        </div>
      </div>
    </section>
  );
}
