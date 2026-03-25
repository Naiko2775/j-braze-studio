import { useState, useEffect, useMemo } from "react";
import { useApi } from "../../shared/hooks/useApi";

/* ── Metadata par categorie ── */
const CATEGORY_META = {
  core: { icon: "\uD83D\uDC64", label: "Core", color: "#040066" },
  user_data: { icon: "\uD83D\uDCCA", label: "User Data", color: "#22C55E" },
  messaging: { icon: "\u2709\uFE0F", label: "Messaging", color: "#f00a0a" },
  segmentation: { icon: "\uD83C\uDFAF", label: "Segmentation", color: "#7C3AED" },
  content: { icon: "\uD83D\uDCDD", label: "Content", color: "#0891B2" },
  analytics: { icon: "\uD83D\uDCC8", label: "Analytics", color: "#E53E3E" },
  data_export: { icon: "\uD83D\uDCE6", label: "Data Export", color: "#78716C" },
};

const ALL_CATEGORIES = ["core", "user_data", "messaging", "segmentation", "content", "analytics", "data_export"];

export default function EntityExplorer({ onBack }) {
  const { data: entities, loading, error, call } = useApi();
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    call("/data-model/entities");
  }, [call]);

  /* ── Entites groupees par categorie ── */
  const entityMap = useMemo(() => {
    if (!entities || typeof entities !== "object") return {};
    // Handle both array and dict formats
    if (Array.isArray(entities)) {
      const map = {};
      for (const e of entities) {
        map[e.name || e.entity_name] = e;
      }
      return map;
    }
    return entities;
  }, [entities]);

  const filteredEntities = useMemo(() => {
    const entries = Object.entries(entityMap);
    return entries.filter(([name, ent]) => {
      const matchesCat = !selectedCategory || ent.category === selectedCategory;
      const matchesSearch =
        !search.trim() ||
        name.toLowerCase().includes(search.toLowerCase()) ||
        (ent.description || "").toLowerCase().includes(search.toLowerCase());
      return matchesCat && matchesSearch;
    });
  }, [entityMap, selectedCategory, search]);

  const selectedEntityData = selectedEntity ? entityMap[selectedEntity] : null;

  /* ── Category counts ── */
  const categoryCounts = useMemo(() => {
    const counts = {};
    for (const [, ent] of Object.entries(entityMap)) {
      const cat = ent.category || "other";
      counts[cat] = (counts[cat] || 0) + 1;
    }
    return counts;
  }, [entityMap]);

  /* ── Loading state ── */
  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 60 }}>
        <div className="spinner" style={{ margin: "0 auto 16px" }} />
        <p className="text-secondary text-sm">Chargement du referentiel Braze...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        {onBack && (
          <button className="btn btn-secondary btn-sm mb-md" onClick={onBack}>
            &larr; Retour
          </button>
        )}
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
          Erreur lors du chargement : {error}
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {onBack && (
            <button className="btn btn-secondary btn-sm" onClick={onBack}>
              &larr; Retour
            </button>
          )}
          <div>
            <h2 style={{ color: "var(--color-navy)", fontSize: "1.15rem", fontWeight: 700 }}>
              Explorateur Braze
            </h2>
            <span className="text-xs text-muted">
              {Object.keys(entityMap).length} entites dans le referentiel
            </span>
          </div>
        </div>

        {/* Search */}
        <div style={{ minWidth: 240, maxWidth: 320, flex: 1 }}>
          <input
            className="input"
            type="text"
            placeholder="Rechercher une entite..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Main layout: categories + list | detail */}
      <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: 20, alignItems: "start" }}>
        {/* Left panel */}
        <div>
          {/* Category buttons */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-body" style={{ padding: 12 }}>
              <div className="text-xs text-muted font-semibold" style={{ marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Categories
              </div>
              <button
                onClick={() => { setSelectedCategory(null); setSelectedEntity(null); }}
                style={{
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  padding: "8px 12px",
                  borderRadius: "var(--radius-sm)",
                  border: "none",
                  background: !selectedCategory ? "rgba(4,0,102,0.06)" : "transparent",
                  color: !selectedCategory ? "var(--color-navy)" : "var(--color-text-secondary)",
                  fontWeight: 600,
                  fontSize: "0.82rem",
                  cursor: "pointer",
                  fontFamily: "var(--font-family)",
                  transition: "all 0.1s",
                  marginBottom: 2,
                }}
              >
                Toutes ({Object.keys(entityMap).length})
              </button>
              {ALL_CATEGORIES.map((cat) => {
                const meta = CATEGORY_META[cat] || {};
                const count = categoryCounts[cat] || 0;
                if (count === 0) return null;
                const isActive = selectedCategory === cat;
                return (
                  <button
                    key={cat}
                    onClick={() => { setSelectedCategory(cat); setSelectedEntity(null); }}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      width: "100%",
                      textAlign: "left",
                      padding: "8px 12px",
                      borderRadius: "var(--radius-sm)",
                      border: "none",
                      background: isActive ? `${meta.color}10` : "transparent",
                      color: isActive ? meta.color : "var(--color-text-secondary)",
                      fontWeight: 600,
                      fontSize: "0.82rem",
                      cursor: "pointer",
                      fontFamily: "var(--font-family)",
                      transition: "all 0.1s",
                      marginBottom: 2,
                    }}
                  >
                    <span style={{ fontSize: "0.9rem" }}>{meta.icon}</span>
                    <span style={{ flex: 1 }}>{meta.label}</span>
                    <span className="text-xs text-muted">{count}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Entity list */}
          <div className="card">
            <div className="card-body" style={{ padding: 8, maxHeight: 400, overflowY: "auto" }}>
              {filteredEntities.length === 0 ? (
                <p className="text-sm text-muted" style={{ padding: 12 }}>
                  Aucune entite trouvee.
                </p>
              ) : (
                filteredEntities.map(([name, ent]) => {
                  const isActive = selectedEntity === name;
                  const catMeta = CATEGORY_META[ent.category] || {};
                  return (
                    <button
                      key={name}
                      onClick={() => setSelectedEntity(name)}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 10,
                        width: "100%",
                        textAlign: "left",
                        padding: "10px 12px",
                        borderRadius: "var(--radius-sm)",
                        border: "none",
                        background: isActive ? "rgba(4,0,102,0.06)" : "transparent",
                        cursor: "pointer",
                        fontFamily: "var(--font-family)",
                        transition: "all 0.1s",
                        marginBottom: 1,
                      }}
                    >
                      <span
                        style={{
                          width: 30,
                          height: 30,
                          borderRadius: 7,
                          background: `${catMeta.color || "#6B7280"}12`,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: "0.8rem",
                          flexShrink: 0,
                        }}
                      >
                        {catMeta.icon || "\uD83D\uDCC4"}
                      </span>
                      <div style={{ minWidth: 0 }}>
                        <div
                          style={{
                            fontWeight: 600,
                            fontSize: "0.82rem",
                            color: isActive ? "var(--color-navy)" : "var(--color-text)",
                            lineHeight: 1.2,
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {name}
                        </div>
                        <div className="text-xs text-muted" style={{ lineHeight: 1.2, marginTop: 1 }}>
                          {ent.category || ""}
                        </div>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Right panel: entity detail */}
        <div>
          {selectedEntityData ? (
            <EntityDetail name={selectedEntity} entity={selectedEntityData} />
          ) : (
            <div className="card" style={{ textAlign: "center", padding: "60px 24px" }}>
              <div style={{ fontSize: "2rem", marginBottom: 8, opacity: 0.3 }}>{"\uD83D\uDCC4"}</div>
              <h3 style={{ color: "var(--color-navy)", fontSize: "1rem", fontWeight: 700, marginBottom: 4 }}>
                Selectionnez une entite
              </h3>
              <p className="text-sm text-muted">
                Cliquez sur une entite dans la liste pour voir ses details, attributs et relations.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Composant detail d'une entite ── */

function EntityDetail({ name, entity }) {
  const catMeta = CATEGORY_META[entity.category] || {};
  const attributes = entity.attributes || {};

  return (
    <div className="card">
      <div className="card-body">
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: "var(--radius-md)",
              background: `${catMeta.color || "#6B7280"}12`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.3rem",
              flexShrink: 0,
            }}
          >
            {catMeta.icon || "\uD83D\uDCC4"}
          </div>
          <div>
            <h3 style={{ color: "var(--color-navy)", fontSize: "1.1rem", fontWeight: 700, margin: 0 }}>
              {name}
            </h3>
            <span className="tag tag-navy" style={{ marginTop: 4, display: "inline-block" }}>
              {entity.category || "uncategorized"}
            </span>
          </div>
        </div>

        {/* Description */}
        {entity.description && (
          <p className="text-sm text-secondary" style={{ marginBottom: 16, lineHeight: 1.6 }}>
            {entity.description}
          </p>
        )}

        {/* Parent */}
        {entity.parent && (
          <div style={{ marginBottom: 12 }}>
            <span className="text-xs font-semibold text-muted" style={{ textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Parent
            </span>
            <div style={{ marginTop: 4 }}>
              <span className="tag tag-navy">{entity.parent}</span>
            </div>
          </div>
        )}

        {/* Children */}
        {entity.children?.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <span className="text-xs font-semibold text-muted" style={{ textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Enfants
            </span>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
              {entity.children.map((child) => (
                <span key={child} className="tag tag-navy">{child}</span>
              ))}
            </div>
          </div>
        )}

        {/* Attributes */}
        {Object.keys(attributes).length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <span className="text-xs font-semibold text-muted" style={{ textTransform: "uppercase", letterSpacing: "0.05em", display: "block", marginBottom: 8 }}>
              Attributs ({Object.keys(attributes).length})
            </span>
            <div>
              {Object.entries(attributes).map(([attrName, attrDesc]) => (
                <div
                  key={attrName}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "baseline",
                    padding: "6px 0",
                    borderBottom: "1px solid var(--color-border-light)",
                    gap: 12,
                  }}
                >
                  <code
                    style={{
                      color: "var(--color-navy)",
                      fontWeight: 700,
                      fontSize: "0.82rem",
                      whiteSpace: "nowrap",
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {attrName}
                  </code>
                  <span className="text-xs text-secondary" style={{ textAlign: "right" }}>
                    {attrDesc}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Examples */}
        {entity.examples?.length > 0 && (
          <div>
            <span className="text-xs font-semibold text-muted" style={{ textTransform: "uppercase", letterSpacing: "0.05em", display: "block", marginBottom: 8 }}>
              Exemples
            </span>
            <ul style={{ paddingLeft: 18, fontSize: "0.82rem", color: "var(--color-text-secondary)" }}>
              {entity.examples.map((ex, i) => (
                <li key={i} style={{ marginBottom: 4 }}>{ex}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
