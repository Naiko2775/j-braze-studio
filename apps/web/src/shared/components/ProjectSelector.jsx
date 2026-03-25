import { useState, useRef, useEffect } from "react";
import { useProject } from "../context/ProjectContext";
import { API_BASE } from "../constants";

const BRAZE_INSTANCES = [
  "US-01", "US-02", "US-03", "US-04", "US-05", "US-06", "US-07", "US-08", "US-09",
  "EU-01", "EU-02", "EU-03",
];

export default function ProjectSelector() {
  const { projects, currentProject, setCurrentProject, refreshProjects } = useProject();
  const [open, setOpen] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClick(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  const handleSelect = (project) => {
    setCurrentProject(project);
    setOpen(false);
  };

  const handleClear = () => {
    setCurrentProject(null);
    setOpen(false);
  };

  return (
    <>
      <div ref={dropdownRef} style={{ position: "relative" }}>
        <button
          type="button"
          onClick={() => setOpen(!open)}
          style={{
            background: currentProject ? "rgba(255,255,255,0.12)" : "rgba(255,255,255,0.06)",
            border: "1px solid rgba(255,255,255,0.15)",
            borderRadius: 8,
            padding: "5px 12px",
            color: currentProject ? "#fff" : "rgba(255,255,255,0.6)",
            fontSize: "0.78rem",
            fontWeight: 600,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontFamily: "var(--font-family)",
            maxWidth: 220,
            transition: "all 0.15s",
          }}
        >
          <span style={{
            width: 6, height: 6, borderRadius: "50%",
            background: currentProject ? "var(--color-success)" : "rgba(255,255,255,0.3)",
            flexShrink: 0,
          }} />
          <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {currentProject ? currentProject.name : "Tous les projets"}
          </span>
          <span style={{ fontSize: 10, opacity: 0.6, flexShrink: 0 }}>
            {open ? "\u25B2" : "\u25BC"}
          </span>
        </button>

        {open && (
          <div style={{
            position: "absolute",
            top: "calc(100% + 6px)",
            right: 0,
            background: "#fff",
            borderRadius: 10,
            boxShadow: "0 8px 30px rgba(0,0,0,0.18)",
            border: "1px solid var(--color-border)",
            minWidth: 260,
            maxHeight: 360,
            overflowY: "auto",
            zIndex: 1000,
          }}>
            {/* All projects option */}
            <button
              type="button"
              onClick={handleClear}
              style={{
                width: "100%",
                padding: "10px 16px",
                background: !currentProject ? "rgba(4,0,102,0.04)" : "transparent",
                border: "none",
                borderBottom: "1px solid var(--color-border-light)",
                cursor: "pointer",
                textAlign: "left",
                fontFamily: "var(--font-family)",
                fontSize: "0.82rem",
                fontWeight: !currentProject ? 700 : 500,
                color: "var(--color-navy)",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              Tous les projets
            </button>

            {/* Project list */}
            {projects.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => handleSelect(p)}
                style={{
                  width: "100%",
                  padding: "10px 16px",
                  background: currentProject?.id === p.id ? "rgba(4,0,102,0.04)" : "transparent",
                  border: "none",
                  borderBottom: "1px solid var(--color-border-light)",
                  cursor: "pointer",
                  textAlign: "left",
                  fontFamily: "var(--font-family)",
                  fontSize: "0.82rem",
                  color: "var(--color-text)",
                  display: "block",
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = "rgba(4,0,102,0.03)"}
                onMouseLeave={(e) => e.currentTarget.style.background =
                  currentProject?.id === p.id ? "rgba(4,0,102,0.04)" : "transparent"
                }
              >
                <div style={{ fontWeight: 600, color: "var(--color-navy)" }}>{p.name}</div>
                {p.client_name && (
                  <div style={{ fontSize: "0.72rem", color: "var(--color-text-muted)", marginTop: 2 }}>
                    {p.client_name}
                    {p.braze_instance && ` \u2022 ${p.braze_instance}`}
                  </div>
                )}
              </button>
            ))}

            {/* New project button */}
            <button
              type="button"
              onClick={() => { setOpen(false); setShowModal(true); }}
              style={{
                width: "100%",
                padding: "10px 16px",
                background: "transparent",
                border: "none",
                cursor: "pointer",
                textAlign: "left",
                fontFamily: "var(--font-family)",
                fontSize: "0.82rem",
                fontWeight: 600,
                color: "var(--color-red)",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = "rgba(240,10,10,0.04)"}
              onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
            >
              + Nouveau projet...
            </button>
          </div>
        )}
      </div>

      {showModal && (
        <CreateProjectModal
          onClose={() => setShowModal(false)}
          onCreated={(project) => {
            refreshProjects();
            setCurrentProject(project);
            setShowModal(false);
          }}
        />
      )}
    </>
  );
}

function CreateProjectModal({ onClose, onCreated }) {
  const [name, setName] = useState("");
  const [clientName, setClientName] = useState("");
  const [description, setDescription] = useState("");
  const [brazeInstance, setBrazeInstance] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    setSaving(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          client_name: clientName.trim() || null,
          description: description.trim() || null,
          braze_instance: brazeInstance || null,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erreur HTTP ${res.status}`);
      }
      const project = await res.json();
      onCreated(project);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.4)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 2000,
        padding: 24,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="card"
        style={{ maxWidth: 480, width: "100%" }}
      >
        <div className="card-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontWeight: 700, color: "var(--color-navy)" }}>Nouveau projet</span>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>Fermer</button>
        </div>
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="label" htmlFor="proj-name">Nom du projet *</label>
              <input
                id="proj-name"
                className="input"
                type="text"
                placeholder="Ex: Migration Carrefour"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={saving}
                autoFocus
              />
            </div>

            <div className="form-group">
              <label className="label" htmlFor="proj-client">Nom du client</label>
              <input
                id="proj-client"
                className="input"
                type="text"
                placeholder="Ex: Carrefour"
                value={clientName}
                onChange={(e) => setClientName(e.target.value)}
                disabled={saving}
              />
            </div>

            <div className="form-group">
              <label className="label" htmlFor="proj-desc">Description</label>
              <textarea
                id="proj-desc"
                className="textarea"
                placeholder="Description libre du projet..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={saving}
                style={{ minHeight: 80 }}
              />
            </div>

            <div className="form-group">
              <label className="label" htmlFor="proj-instance">Instance Braze</label>
              <select
                id="proj-instance"
                className="select"
                value={brazeInstance}
                onChange={(e) => setBrazeInstance(e.target.value)}
                disabled={saving}
              >
                <option value="">-- Selectionner --</option>
                {BRAZE_INSTANCES.map((inst) => (
                  <option key={inst} value={inst}>{inst}</option>
                ))}
              </select>
            </div>

            {error && (
              <div style={{
                background: "#FFF5F5",
                border: "1px solid #FED7D7",
                borderRadius: "var(--radius-md)",
                padding: "10px 14px",
                marginBottom: 16,
                fontSize: "0.82rem",
                color: "#C53030",
              }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              className="btn btn-danger btn-lg w-full"
              disabled={saving || !name.trim()}
            >
              {saving ? "Creation..." : "Creer le projet"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
