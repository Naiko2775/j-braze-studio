import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useProject } from "../shared/context/ProjectContext";
import { API_BASE } from "../shared/constants";

const STATUS_LABELS = {
  active: { label: "Actif", cls: "badge-success" },
  completed: { label: "Termine", cls: "badge-info" },
  archived: { label: "Archive", cls: "badge-neutral" },
};

const ACTIVITY_ICONS = {
  analysis: "\uD83D\uDCCA",
  generation: "\uD83C\uDFA8",
  migration: "\uD83D\uDE80",
};

const ACTIVITY_LABELS = {
  analysis: "Analyse",
  generation: "Generation",
  migration: "Migration",
};

function formatDate(iso) {
  if (!iso) return "\u2014";
  const d = new Date(iso);
  return d.toLocaleDateString("fr-FR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export default function ProjectPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { projects, currentProject, setCurrentProject, refreshProjects } = useProject();

  const [project, setProject] = useState(null);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [saving, setSaving] = useState(false);

  const fetchProject = useCallback(async (projectId) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/projects/${projectId}`);
      if (res.ok) {
        const data = await res.json();
        setProject(data);
      }
    } catch { /* ignore */ }
    try {
      const res = await fetch(`${API_BASE}/projects/${projectId}/activity`);
      if (res.ok) {
        const data = await res.json();
        setActivity(data);
      }
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (id) {
      fetchProject(id);
    }
  }, [id, fetchProject]);

  // If no id param, show project list
  if (!id) {
    return <ProjectListView projects={projects} navigate={navigate} />;
  }

  if (loading && !project) {
    return (
      <div style={{ textAlign: "center", padding: 60 }}>
        <div className="spinner" style={{ margin: "0 auto 16px" }} />
        <p className="text-sm text-secondary">Chargement du projet...</p>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="card" style={{ textAlign: "center", padding: "48px 24px" }}>
        <p className="text-sm text-muted">Projet non trouve.</p>
        <button className="btn btn-secondary" style={{ marginTop: 16 }} onClick={() => navigate("/projects")}>
          Retour aux projets
        </button>
      </div>
    );
  }

  const statusInfo = STATUS_LABELS[project.status] || STATUS_LABELS.active;

  const handleEdit = () => {
    setEditForm({
      name: project.name || "",
      client_name: project.client_name || "",
      description: project.description || "",
      braze_instance: project.braze_instance || "",
      status: project.status || "active",
    });
    setEditing(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE}/projects/${project.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editForm),
      });
      if (res.ok) {
        const updated = await res.json();
        setProject({ ...project, ...updated });
        setEditing(false);
        refreshProjects();
        if (currentProject?.id === project.id) {
          setCurrentProject(updated);
        }
      }
    } catch { /* ignore */ }
    setSaving(false);
  };

  const handleArchive = async () => {
    try {
      const res = await fetch(`${API_BASE}/projects/${project.id}`, { method: "DELETE" });
      if (res.ok) {
        refreshProjects();
        if (currentProject?.id === project.id) {
          setCurrentProject(null);
        }
        navigate("/projects");
      }
    } catch { /* ignore */ }
  };

  return (
    <div>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
        <div>
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => navigate("/projects")}
            style={{ marginBottom: 8, color: "var(--color-text-muted)" }}
          >
            &larr; Tous les projets
          </button>
          <h1 style={{ color: "var(--color-navy)", fontSize: 24, fontWeight: 700 }}>
            {project.name}
          </h1>
          {project.client_name && (
            <p className="text-sm text-secondary" style={{ marginTop: 4 }}>
              Client : {project.client_name}
              {project.braze_instance && ` \u2022 Instance : ${project.braze_instance}`}
            </p>
          )}
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span className={`badge ${statusInfo.cls}`}>
            <span className="badge-dot" />
            {statusInfo.label}
          </span>
          <button className="btn btn-secondary btn-sm" onClick={handleEdit}>Modifier</button>
          {project.status !== "archived" && (
            <button className="btn btn-ghost btn-sm" style={{ color: "var(--color-error)" }} onClick={handleArchive}>
              Archiver
            </button>
          )}
        </div>
      </div>

      {/* Description */}
      {project.description && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-body">
            <span className="text-xs text-muted font-semibold" style={{ display: "block", marginBottom: 6 }}>Description</span>
            <p className="text-sm" style={{ lineHeight: 1.6 }}>{project.description}</p>
          </div>
        </div>
      )}

      {/* Counters */}
      {project.counts && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 24 }}>
          <CounterCard label="Analyses" value={project.counts.analyses} color="var(--color-navy)" />
          <CounterCard label="Generations" value={project.counts.generations} color="var(--color-red)" />
          <CounterCard label="Migrations" value={project.counts.migrations} color="var(--color-info)" />
        </div>
      )}

      {/* Activity Timeline */}
      <div className="card">
        <div className="card-header">
          <span style={{ fontWeight: 700, color: "var(--color-navy)" }}>Timeline d'activite</span>
        </div>
        <div className="card-body">
          {activity.length === 0 ? (
            <p className="text-sm text-muted" style={{ textAlign: "center", padding: 24 }}>
              Aucune activite pour ce projet.
            </p>
          ) : (
            <div>
              {activity.map((item, i) => (
                <div
                  key={`${item.type}-${item.id}`}
                  style={{
                    display: "flex",
                    gap: 14,
                    padding: "12px 0",
                    borderBottom: i < activity.length - 1 ? "1px solid var(--color-border-light)" : "none",
                    alignItems: "flex-start",
                  }}
                >
                  <span style={{ fontSize: "1.2rem", lineHeight: 1 }}>
                    {ACTIVITY_ICONS[item.type] || "\u2022"}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--color-navy)" }}>
                        {ACTIVITY_LABELS[item.type] || item.type}
                      </span>
                      <span className="text-xs text-muted">{formatDate(item.created_at)}</span>
                    </div>
                    <p className="text-sm text-secondary" style={{ marginTop: 2 }}>
                      {item.summary}
                    </p>
                    {item.status && (
                      <span className="text-xs text-muted" style={{ marginTop: 2, display: "inline-block" }}>
                        Statut : {item.status}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Edit Modal */}
      {editing && (
        <EditProjectModal
          form={editForm}
          onChange={setEditForm}
          onSave={handleSave}
          onClose={() => setEditing(false)}
          saving={saving}
        />
      )}
    </div>
  );
}

function ProjectListView({ projects, navigate }) {
  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ color: "var(--color-navy)", fontSize: 24, fontWeight: 700 }}>Projets</h1>
        <p className="text-sm text-secondary" style={{ marginTop: 4 }}>
          Tous les projets clients actifs.
        </p>
      </div>

      {projects.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "48px 24px" }}>
          <p className="text-sm text-muted">Aucun projet. Creez-en un via le selecteur dans la barre de navigation.</p>
        </div>
      ) : (
        <div style={{ display: "grid", gap: 12 }}>
          {projects.map((p) => (
            <div
              key={p.id}
              className="card"
              style={{ cursor: "pointer", transition: "box-shadow 0.15s" }}
              onClick={() => navigate(`/projects/${p.id}`)}
              onMouseEnter={(e) => e.currentTarget.style.boxShadow = "var(--shadow-md)"}
              onMouseLeave={(e) => e.currentTarget.style.boxShadow = ""}
            >
              <div className="card-body" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ fontWeight: 700, color: "var(--color-navy)", fontSize: "1rem" }}>{p.name}</div>
                  {p.client_name && (
                    <div className="text-sm text-muted" style={{ marginTop: 2 }}>
                      {p.client_name}
                      {p.braze_instance && ` \u2022 ${p.braze_instance}`}
                    </div>
                  )}
                  {p.description && (
                    <div className="text-xs text-secondary" style={{ marginTop: 4 }}>
                      {p.description.length > 120 ? p.description.slice(0, 120) + "..." : p.description}
                    </div>
                  )}
                </div>
                <div style={{ textAlign: "right", flexShrink: 0, marginLeft: 16 }}>
                  <span className={`badge ${(STATUS_LABELS[p.status] || STATUS_LABELS.active).cls}`}>
                    <span className="badge-dot" />
                    {(STATUS_LABELS[p.status] || STATUS_LABELS.active).label}
                  </span>
                  <div className="text-xs text-muted" style={{ marginTop: 6 }}>
                    {formatDate(p.updated_at)}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function CounterCard({ label, value, color }) {
  return (
    <div className="card" style={{ textAlign: "center" }}>
      <div className="card-body">
        <div style={{ fontSize: "2rem", fontWeight: 700, color }}>{value}</div>
        <div className="text-sm text-muted" style={{ marginTop: 4, fontWeight: 600 }}>{label}</div>
      </div>
    </div>
  );
}

const BRAZE_INSTANCES = [
  "US-01", "US-02", "US-03", "US-04", "US-05", "US-06", "US-07", "US-08", "US-09",
  "EU-01", "EU-02", "EU-03",
];

function EditProjectModal({ form, onChange, onSave, onClose, saving }) {
  const update = (field, value) => onChange({ ...form, [field]: value });

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)",
        display: "flex", alignItems: "center", justifyContent: "center",
        zIndex: 2000, padding: 24,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="card"
        style={{ maxWidth: 480, width: "100%" }}
      >
        <div className="card-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontWeight: 700, color: "var(--color-navy)" }}>Modifier le projet</span>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>Fermer</button>
        </div>
        <div className="card-body">
          <div className="form-group">
            <label className="label">Nom du projet</label>
            <input className="input" value={form.name} onChange={(e) => update("name", e.target.value)} disabled={saving} />
          </div>
          <div className="form-group">
            <label className="label">Client</label>
            <input className="input" value={form.client_name} onChange={(e) => update("client_name", e.target.value)} disabled={saving} />
          </div>
          <div className="form-group">
            <label className="label">Description</label>
            <textarea className="textarea" value={form.description} onChange={(e) => update("description", e.target.value)} disabled={saving} style={{ minHeight: 80 }} />
          </div>
          <div className="form-group">
            <label className="label">Instance Braze</label>
            <select className="select" value={form.braze_instance} onChange={(e) => update("braze_instance", e.target.value)} disabled={saving}>
              <option value="">-- Selectionner --</option>
              {BRAZE_INSTANCES.map((inst) => (
                <option key={inst} value={inst}>{inst}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="label">Statut</label>
            <select className="select" value={form.status} onChange={(e) => update("status", e.target.value)} disabled={saving}>
              <option value="active">Actif</option>
              <option value="completed">Termine</option>
              <option value="archived">Archive</option>
            </select>
          </div>
          <button className="btn btn-danger btn-lg w-full" onClick={onSave} disabled={saving || !form.name?.trim()}>
            {saving ? "Enregistrement..." : "Enregistrer"}
          </button>
        </div>
      </div>
    </div>
  );
}
