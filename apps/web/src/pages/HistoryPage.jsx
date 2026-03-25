import { useState, useEffect, useMemo, useCallback } from "react";
import { useApi } from "../shared/hooks/useApi";
import { useProject } from "../shared/context/ProjectContext";
import { API_BASE } from "../shared/constants";
import CodeBlock from "../shared/components/CodeBlock";
import ExportButton from "../shared/components/ExportButton";

/* ── Constantes ── */

const TABS = [
  { id: "analyses", label: "Analyses", endpoint: "/data-model/history" },
  { id: "generations", label: "Generations", endpoint: "/liquid/history" },
  { id: "migrations", label: "Migrations", endpoint: "/migration/history" },
];

const MIGRATION_STATUS = {
  pending:   { label: "En attente",  cls: "badge-neutral" },
  running:   { label: "En cours",    cls: "badge-info" },
  completed: { label: "Termine",     cls: "badge-success" },
  failed:    { label: "Echoue",      cls: "badge-error" },
  stopped:   { label: "Arrete",      cls: "badge-warning" },
};

/* ── Helpers ── */

function formatDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function truncate(text, max = 80) {
  if (!text) return "—";
  return text.length > max ? text.slice(0, max) + "..." : text;
}

function summarize(tab, entry) {
  if (tab === "analyses") return truncate(entry.use_case, 100);
  if (tab === "generations") return truncate(entry.brief, 100);
  if (tab === "migrations") {
    const platform = entry.platform || "—";
    const mode = entry.mode || "";
    const status = entry.status || "";
    return `${platform} / ${mode} — ${status}`;
  }
  return "—";
}

function projectName(entry) {
  return entry.project_name || "—";
}

function entryDate(entry) {
  return entry.created_at || entry.started_at || null;
}

/* ── StatusBadge ── */

function StatusBadge({ status }) {
  const s = MIGRATION_STATUS[status] || { label: status, cls: "badge-neutral" };
  return (
    <span className={`badge ${s.cls}`}>
      <span className="badge-dot" />
      {s.label}
    </span>
  );
}

/* ── Detail modal ── */

function DetailModal({ entry, tab, onClose }) {
  if (!entry) return null;

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
        zIndex: 1000,
        padding: 24,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="card"
        style={{
          maxWidth: 720,
          width: "100%",
          maxHeight: "80vh",
          overflowY: "auto",
        }}
      >
        <div className="card-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span>Detail — {projectName(entry)}</span>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>
            Fermer
          </button>
        </div>
        <div className="card-body">
          {/* Metadata */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 16, marginBottom: 16, fontSize: "0.82rem" }}>
            <div>
              <span className="text-xs text-muted font-semibold" style={{ display: "block" }}>Date</span>
              {formatDate(entryDate(entry))}
            </div>
            <div>
              <span className="text-xs text-muted font-semibold" style={{ display: "block" }}>Projet</span>
              {projectName(entry)}
            </div>
            {entry.model_used && (
              <div>
                <span className="text-xs text-muted font-semibold" style={{ display: "block" }}>Modele</span>
                {entry.model_used}
              </div>
            )}
            {tab === "migrations" && entry.status && (
              <div>
                <span className="text-xs text-muted font-semibold" style={{ display: "block" }}>Statut</span>
                <StatusBadge status={entry.status} />
              </div>
            )}
            {tab === "migrations" && entry.platform && (
              <div>
                <span className="text-xs text-muted font-semibold" style={{ display: "block" }}>Plateforme</span>
                {entry.platform}
              </div>
            )}
            {tab === "migrations" && entry.mode && (
              <div>
                <span className="text-xs text-muted font-semibold" style={{ display: "block" }}>Mode</span>
                <span className="tag tag-navy">{entry.mode}</span>
              </div>
            )}
            {tab === "generations" && entry.template_type && (
              <div>
                <span className="text-xs text-muted font-semibold" style={{ display: "block" }}>Template</span>
                {entry.template_type}
              </div>
            )}
            {tab === "generations" && entry.channel && (
              <div>
                <span className="text-xs text-muted font-semibold" style={{ display: "block" }}>Canal</span>
                {entry.channel}
              </div>
            )}
          </div>

          {/* Content */}
          {tab === "analyses" && entry.use_case && (
            <div style={{ marginBottom: 16 }}>
              <span className="text-xs text-muted font-semibold" style={{ display: "block", marginBottom: 4 }}>Use case</span>
              <p className="text-sm" style={{ lineHeight: 1.6 }}>{entry.use_case}</p>
            </div>
          )}
          {tab === "generations" && entry.brief && (
            <div style={{ marginBottom: 16 }}>
              <span className="text-xs text-muted font-semibold" style={{ display: "block", marginBottom: 4 }}>Brief</span>
              <p className="text-sm" style={{ lineHeight: 1.6 }}>{entry.brief}</p>
            </div>
          )}

          {/* Result JSON */}
          {entry.result && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <span className="text-xs text-muted font-semibold">Resultat</span>
                <ExportButton
                  data={entry.result}
                  filename={`${tab}-${entry.id || "export"}.json`}
                  label="Exporter JSON"
                />
              </div>
              <CodeBlock
                code={typeof entry.result === "string" ? entry.result : JSON.stringify(entry.result, null, 2)}
                language="json"
                maxHeight={300}
              />
            </div>
          )}

          {/* Error log for migrations */}
          {tab === "migrations" && entry.error_log && (
            <div style={{ marginTop: 16 }}>
              <span className="text-xs text-muted font-semibold" style={{ display: "block", marginBottom: 4 }}>Erreurs</span>
              <CodeBlock
                code={JSON.stringify(entry.error_log, null, 2)}
                language="json"
                maxHeight={200}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Page principale ── */

export default function HistoryPage() {
  const [activeTab, setActiveTab] = useState("analyses");
  const [filterProject, setFilterProject] = useState("");
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const { currentProject } = useProject();

  // Un hook par endpoint
  const analysesApi = useApi();
  const generationsApi = useApi();
  const migrationsApi = useApi();

  const apiMap = useMemo(
    () => ({
      analyses: analysesApi,
      generations: generationsApi,
      migrations: migrationsApi,
    }),
    [analysesApi, generationsApi, migrationsApi],
  );

  // Chargement au montage
  useEffect(() => {
    analysesApi.call("/data-model/history").catch(() => {});
    generationsApi.call("/liquid/history").catch(() => {});
    migrationsApi.call("/migration/history").catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const currentApi = apiMap[activeTab];
  const rawEntries = Array.isArray(currentApi.data) ? currentApi.data : [];

  // Filtrage + tri par date decroissante
  const entries = useMemo(() => {
    let list = rawEntries;
    // Filtre par projet selectionne (via project_id ou project_name)
    if (currentProject) {
      list = list.filter((e) =>
        e.project_id === currentProject.id ||
        (!e.project_id && (e.project_name || "").toLowerCase() === currentProject.name.toLowerCase())
      );
    }
    if (filterProject.trim()) {
      const q = filterProject.trim().toLowerCase();
      list = list.filter((e) =>
        (e.project_name || "").toLowerCase().includes(q),
      );
    }
    return [...list].sort((a, b) => {
      const da = new Date(entryDate(a) || 0);
      const db = new Date(entryDate(b) || 0);
      return db - da;
    });
  }, [rawEntries, filterProject, currentProject]);

  // Compteurs par onglet
  const counts = useMemo(
    () => ({
      analyses: Array.isArray(analysesApi.data) ? analysesApi.data.length : 0,
      generations: Array.isArray(generationsApi.data) ? generationsApi.data.length : 0,
      migrations: Array.isArray(migrationsApi.data) ? migrationsApi.data.length : 0,
    }),
    [analysesApi.data, generationsApi.data, migrationsApi.data],
  );

  const handleRefresh = useCallback(() => {
    const tab = TABS.find((t) => t.id === activeTab);
    if (tab) apiMap[activeTab].call(tab.endpoint).catch(() => {});
  }, [activeTab, apiMap]);

  // Fetch detail (with result field) before opening the modal
  const DETAIL_ENDPOINTS = {
    analyses: "/data-model/history",
    generations: "/liquid/history",
    migrations: "/migration/history",
  };

  const handleSelectEntry = useCallback(async (entry, tab) => {
    if (!entry.id) {
      setSelectedEntry(entry);
      return;
    }
    const base = DETAIL_ENDPOINTS[tab];
    if (!base) {
      setSelectedEntry(entry);
      return;
    }
    setDetailLoading(true);
    try {
      const res = await fetch(`${API_BASE}${base}/${entry.id}`, {
        headers: { "Content-Type": "application/json" },
      });
      if (res.ok) {
        const detail = await res.json();
        setSelectedEntry(detail);
      } else {
        // Fallback to entry without result
        setSelectedEntry(entry);
      }
    } catch {
      setSelectedEntry(entry);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ color: "var(--color-navy)", fontSize: 24, fontWeight: 700 }}>
          Historique
        </h1>
        <p className="text-sm text-secondary" style={{ marginTop: 4 }}>
          Vue globale des analyses, generations et migrations passees.
        </p>
      </div>

      {/* Tabs */}
      <div className="tabs" style={{ marginBottom: 16 }}>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
            {counts[tab.id] > 0 && (
              <span
                style={{
                  marginLeft: 6,
                  background: activeTab === tab.id ? "var(--color-navy)" : "rgba(0,0,0,0.08)",
                  color: activeTab === tab.id ? "#fff" : "var(--color-text-muted)",
                  padding: "1px 7px",
                  borderRadius: 10,
                  fontSize: "0.7rem",
                  fontWeight: 700,
                }}
              >
                {counts[tab.id]}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Toolbar: filtre projet + refresh */}
      <div style={{ display: "flex", gap: 12, marginBottom: 16, alignItems: "center", flexWrap: "wrap" }}>
        <div style={{ flex: 1, minWidth: 200, maxWidth: 320 }}>
          <input
            className="input"
            type="text"
            placeholder="Filtrer par nom de projet..."
            value={filterProject}
            onChange={(e) => setFilterProject(e.target.value)}
          />
        </div>
        <button className="btn btn-secondary btn-sm" onClick={handleRefresh} disabled={currentApi.loading}>
          {currentApi.loading ? "Chargement..." : "Rafraichir"}
        </button>
        <span className="text-xs text-muted">
          {entries.length} entree{entries.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Contenu */}
      {currentApi.loading && entries.length === 0 ? (
        <div style={{ textAlign: "center", padding: 60 }}>
          <div className="spinner" style={{ margin: "0 auto 16px" }} />
          <p className="text-sm text-secondary">Chargement de l'historique...</p>
        </div>
      ) : currentApi.error ? (
        <div
          style={{
            background: "#FFF5F5",
            border: "1px solid #FED7D7",
            borderRadius: "var(--radius-md)",
            padding: "16px 20px",
            fontSize: "0.85rem",
            color: "#C53030",
          }}
        >
          Erreur : {currentApi.error}
        </div>
      ) : entries.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "48px 24px" }}>
          <div style={{ fontSize: "2rem", marginBottom: 8, opacity: 0.3 }}>
            {activeTab === "analyses" ? "\uD83D\uDCCA" : activeTab === "generations" ? "\uD83C\uDFA8" : "\uD83D\uDE80"}
          </div>
          <p className="text-sm text-muted">
            Aucune entree dans l'historique{filterProject.trim() ? ` pour "${filterProject}"` : ""}.
          </p>
        </div>
      ) : (
        <div className="card">
          {/* Table header */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: activeTab === "migrations" ? "140px 1fr 120px 100px" : "140px 120px 1fr",
              gap: 12,
              padding: "10px 20px",
              borderBottom: "1px solid var(--color-border-light)",
              fontSize: "0.75rem",
              fontWeight: 700,
              color: "var(--color-text-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.04em",
            }}
          >
            <span>Date</span>
            {activeTab === "migrations" ? (
              <>
                <span>Projet / Resume</span>
                <span>Plateforme</span>
                <span>Statut</span>
              </>
            ) : (
              <>
                <span>Projet</span>
                <span>Resume</span>
              </>
            )}
          </div>

          {/* Rows */}
          {entries.map((entry, i) => (
            <div
              key={entry.id || i}
              onClick={() => handleSelectEntry(entry, activeTab)}
              style={{
                display: "grid",
                gridTemplateColumns: activeTab === "migrations" ? "140px 1fr 120px 100px" : "140px 120px 1fr",
                gap: 12,
                padding: "12px 20px",
                borderBottom: i < entries.length - 1 ? "1px solid var(--color-border-light)" : "none",
                cursor: "pointer",
                transition: "background 0.1s",
                fontSize: "0.82rem",
                alignItems: "center",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(4,0,102,0.02)")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            >
              <span className="text-xs text-muted">{formatDate(entryDate(entry))}</span>
              {activeTab === "migrations" ? (
                <>
                  <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    <strong style={{ color: "var(--color-navy)" }}>{projectName(entry)}</strong>
                    {entry.mode && <span className="text-muted"> / {entry.mode}</span>}
                  </span>
                  <span>
                    <span className="tag tag-gray" style={{ fontSize: "0.7rem" }}>{entry.platform || "—"}</span>
                  </span>
                  <span>
                    <StatusBadge status={entry.status} />
                  </span>
                </>
              ) : (
                <>
                  <span style={{ fontWeight: 600, color: "var(--color-navy)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {projectName(entry)}
                  </span>
                  <span className="text-secondary" style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {summarize(activeTab, entry)}
                  </span>
                </>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Detail modal */}
      {selectedEntry && (
        <DetailModal
          entry={selectedEntry}
          tab={activeTab}
          onClose={() => setSelectedEntry(null)}
        />
      )}
    </div>
  );
}
