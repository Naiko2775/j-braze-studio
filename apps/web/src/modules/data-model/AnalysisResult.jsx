import { useState } from "react";
import { useApi } from "../../shared/hooks/useApi";
import ResultTabs from "../../shared/components/ResultTabs";
import CodeBlock from "../../shared/components/CodeBlock";
import ExportButton from "../../shared/components/ExportButton";
import DownloadButton from "../../shared/components/DownloadButton";

/* ── Couleurs par type de compteur ── */
const COUNTER_COLORS = [
  { key: "entities", label: "Entites", color: "var(--color-navy)", bg: "rgba(4,0,102,0.06)" },
  { key: "custom_attributes", label: "Custom Attributes", color: "var(--color-red)", bg: "rgba(240,10,10,0.06)" },
  { key: "segments", label: "Segments", color: "#7C3AED", bg: "rgba(124,58,237,0.06)" },
  { key: "channels", label: "Canaux", color: "var(--color-success)", bg: "rgba(34,197,94,0.06)" },
];

/* ── Helpers ── */

function countEntities(results) {
  const analyses = results.use_case_analysis || [];
  let entities = 0;
  let customAttrs = 0;
  let segments = 0;
  const channelsSet = new Set();

  for (const a of analyses) {
    for (const d of a.required_data || []) {
      entities++;
      customAttrs += (d.custom_fields || []).length;
    }
    segments += (a.segments || []).length;
    for (const ch of (a.messaging?.channels || [])) {
      channelsSet.add(ch);
    }
  }

  return { entities, custom_attributes: customAttrs, segments, channels: channelsSet.size };
}

function formatResultsText(results) {
  const lines = ["=== Braze Data Model Analysis ===\n"];
  for (const a of results.use_case_analysis || []) {
    lines.push(`\n--- Use Case: ${a.use_case} ---`);
    lines.push(a.description || "");
    for (const d of a.required_data || []) {
      lines.push(`\n  Entite: ${d.entity}`);
      lines.push(`  Usage: ${d.purpose || ""}`);
      if (d.attributes?.length) lines.push(`  Attributs: ${d.attributes.join(", ")}`);
      if (d.custom_fields?.length) lines.push(`  Custom fields: ${d.custom_fields.map((f) => f.name).join(", ")}`);
    }
    if (a.segments?.length) {
      lines.push("\n  Segments:");
      for (const s of a.segments) {
        lines.push(`    - ${s.name}: ${(s.filters || []).join(" + ")}`);
      }
    }
    if (a.messaging) {
      lines.push(`\n  Canaux: ${(a.messaging.channels || []).join(", ")}`);
      lines.push(`  Trigger: ${a.messaging.trigger_type || ""} - ${a.messaging.trigger_details || ""}`);
    }
  }
  return lines.join("\n");
}

/* ── Sous-composants ── */

function CounterCards({ counts }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12, marginBottom: 24 }}>
      {COUNTER_COLORS.map((c) => (
        <div
          key={c.key}
          style={{
            background: c.bg,
            borderRadius: "var(--radius-md)",
            padding: "16px 18px",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: "1.75rem", fontWeight: 900, color: c.color, lineHeight: 1 }}>
            {counts[c.key] || 0}
          </div>
          <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--color-text-secondary)", marginTop: 4 }}>
            {c.label}
          </div>
        </div>
      ))}
    </div>
  );
}

function EntityCard({ data }) {
  return (
    <div className="card" style={{ marginBottom: 12 }}>
      <div className="card-body" style={{ padding: "16px 18px" }}>
        <h4 style={{ color: "var(--color-navy)", fontSize: "0.9rem", fontWeight: 700, marginBottom: 4 }}>
          {data.entity}
        </h4>
        {data.purpose && (
          <p className="text-sm text-secondary" style={{ marginBottom: 8 }}>
            {data.purpose}
          </p>
        )}

        {/* Attributes tags */}
        {data.attributes?.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 6 }}>
            {data.attributes.slice(0, 6).map((attr) => (
              <span key={attr} className="tag tag-navy">{attr}</span>
            ))}
            {data.attributes.length > 6 && (
              <span className="tag tag-gray">+{data.attributes.length - 6}</span>
            )}
          </div>
        )}

        {/* Custom fields */}
        {data.custom_fields?.length > 0 && (
          <div style={{ marginTop: 6 }}>
            <span style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--color-red)" }}>
              Custom fields :
            </span>{" "}
            {data.custom_fields.map((cf) => (
              <span key={cf.name} className="tag tag-red" style={{ marginLeft: 4 }}>{cf.name}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SegmentCard({ segment }) {
  return (
    <div className="card" style={{ marginBottom: 10 }}>
      <div className="card-body" style={{ padding: "14px 18px" }}>
        <h4 style={{ color: "var(--color-navy)", fontSize: "0.88rem", fontWeight: 700, marginBottom: 4 }}>
          {segment.name}
        </h4>
        {segment.filters?.length > 0 && (
          <ul style={{ fontSize: "0.78rem", color: "var(--color-text-secondary)", paddingLeft: 18, margin: "3px 0" }}>
            {segment.filters.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function MessagingCard({ messaging }) {
  if (!messaging) return null;
  return (
    <div className="card" style={{ marginBottom: 10 }}>
      <div className="card-body" style={{ padding: "14px 18px" }}>
        <h4 style={{ color: "var(--color-navy)", fontSize: "0.88rem", fontWeight: 700, marginBottom: 8 }}>
          Configuration Messaging
        </h4>
        {messaging.channels?.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 8 }}>
            {messaging.channels.map((ch) => (
              <span key={ch} className="tag tag-green">{ch}</span>
            ))}
          </div>
        )}
        {messaging.trigger_type && (
          <p className="text-sm text-secondary">
            <strong>Declenchement :</strong> {messaging.trigger_type}
            {messaging.trigger_details && <><br />{messaging.trigger_details}</>}
          </p>
        )}
      </div>
    </div>
  );
}

/* ── Tab content: Donnees Requises ── */

function DataTab({ results }) {
  const analyses = results.use_case_analysis || [];
  const counts = countEntities(results);

  return (
    <div>
      <CounterCards counts={counts} />

      {analyses.map((analysis, idx) => (
        <div key={idx} style={{ marginBottom: 28 }}>
          <h3 style={{ color: "var(--color-navy)", fontSize: "1rem", fontWeight: 700, marginBottom: 4 }}>
            {analysis.use_case}
          </h3>
          {analysis.description && (
            <p className="text-sm text-secondary" style={{ marginBottom: 14, lineHeight: 1.5 }}>
              {analysis.description}
            </p>
          )}

          {/* Entities */}
          {(analysis.required_data || []).map((data, dIdx) => (
            <EntityCard key={dIdx} data={data} />
          ))}

          {/* Segments */}
          {analysis.segments?.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <h4 style={{ fontSize: "0.88rem", fontWeight: 700, marginBottom: 8, color: "var(--color-text)" }}>
                Segments a creer
              </h4>
              {analysis.segments.map((seg, sIdx) => (
                <SegmentCard key={sIdx} segment={seg} />
              ))}
            </div>
          )}

          {/* Messaging */}
          {analysis.messaging && (
            <div style={{ marginTop: 16 }}>
              <MessagingCard messaging={analysis.messaging} />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

/* ── Tab content: Hierarchie ── */

function HierarchyTab({ results }) {
  const mermaid = results.mermaid_diagram || results.mermaid || "";
  const hierarchy = results.data_hierarchy || [];

  return (
    <div>
      {mermaid ? (
        <>
          <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--color-navy)", marginBottom: 12 }}>
            Diagramme du Data Model
          </h3>
          <CodeBlock code={mermaid} language="mermaid" maxHeight={500} />
        </>
      ) : (
        <p className="text-secondary text-sm">Aucun diagramme Mermaid disponible pour cette analyse.</p>
      )}

      {hierarchy.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--color-navy)", marginBottom: 12 }}>
            Arbre des entites
          </h3>
          {hierarchy.map((root, idx) => (
            <HierarchyNode key={idx} node={root} indent={0} />
          ))}
        </div>
      )}
    </div>
  );
}

function HierarchyNode({ node, indent }) {
  const entity = node.entity || node.name || "?";
  const attrs = node.attributes_used || [];
  const attrDisplay =
    attrs.length > 0
      ? ` (${attrs.slice(0, 3).join(", ")}${attrs.length > 3 ? "..." : ""})`
      : "";
  const hasChildren = node.children?.length > 0;

  return (
    <div style={{ paddingLeft: indent * 24 }}>
      <div
        style={{
          padding: "6px 10px",
          fontSize: "0.85rem",
          display: "flex",
          alignItems: "center",
          gap: 6,
          borderLeft: indent > 0 ? "2px solid var(--color-border)" : "none",
        }}
      >
        <span style={{ opacity: 0.5 }}>{hasChildren ? "\uD83D\uDCC1" : "\uD83D\uDCC4"}</span>
        <strong style={{ color: "var(--color-navy)" }}>{entity}</strong>
        {attrDisplay && (
          <span className="text-xs text-muted font-mono">{attrDisplay}</span>
        )}
      </div>
      {(node.children || []).map((child, idx) => (
        <HierarchyNode key={idx} node={child} indent={indent + 1} />
      ))}
    </div>
  );
}

/* ── Tab content: JSON ── */

function JsonTab({ results }) {
  const json = JSON.stringify(results, null, 2);
  return (
    <div>
      <CodeBlock code={json} language="json" maxHeight={600} />
    </div>
  );
}

/* ── Helpers pour Data Points ── */

const MAU_PRESETS = [
  { label: "10K", value: 10000 },
  { label: "50K", value: 50000 },
  { label: "100K", value: 100000 },
  { label: "500K", value: 500000 },
  { label: "1M", value: 1000000 },
];

const FREQUENCY_OPTIONS = [
  { value: "once", label: "Une seule fois" },
  { value: "monthly", label: "Mensuelle" },
  { value: "weekly", label: "Hebdomadaire" },
  { value: "daily", label: "Quotidienne" },
];

function formatDataPoints(n) {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

function formatDataPointsFull(n) {
  return new Intl.NumberFormat("fr-FR").format(n);
}

function getCostColor(monthlyDp) {
  if (monthlyDp === 0) return "#22C55E";
  if (monthlyDp < 100_000) return "#F59E0B";
  return "#EF4444";
}

function getRowBg(monthlyDp, isFree) {
  if (isFree) return "rgba(34,197,94,0.06)";
  if (monthlyDp >= 1_000_000) return "rgba(239,68,68,0.04)";
  if (monthlyDp >= 100_000) return "rgba(245,158,11,0.04)";
  return "transparent";
}

/* ── Tab content: Data Points ── */

function DataPointsTab({ results }) {
  const { loading, error, call } = useApi();
  const [userVolume, setUserVolume] = useState(100000);
  const [frequencies, setFrequencies] = useState({
    profile: "monthly",
    behavior: "weekly",
    purchase: "weekly",
  });
  const [estimation, setEstimation] = useState(null);

  const handleEstimate = async () => {
    try {
      const response = await call("/data-model/estimate-data-points", {
        method: "POST",
        body: JSON.stringify({
          analysis_result: results,
          user_volume: userVolume,
          update_frequencies: frequencies,
        }),
      });
      setEstimation(response);
    } catch {
      // error handled by useApi
    }
  };

  const handleFreqChange = (key, value) => {
    setFrequencies((prev) => ({ ...prev, [key]: value }));
    setEstimation(null);
  };

  return (
    <div>
      {/* Formulaire de parametres */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-body" style={{ padding: "20px 24px" }}>
          <h3 style={{ color: "var(--color-navy)", fontSize: "1rem", fontWeight: 700, marginBottom: 16 }}>
            Parametres d'estimation
          </h3>

          {/* MAU Input */}
          <div style={{ marginBottom: 16 }}>
            <label className="label" style={{ marginBottom: 6, display: "block" }}>
              Utilisateurs actifs mensuels (MAU)
            </label>
            <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
              <input
                type="number"
                className="input"
                value={userVolume}
                onChange={(e) => {
                  setUserVolume(Math.max(1, parseInt(e.target.value) || 1));
                  setEstimation(null);
                }}
                style={{ width: 180 }}
                min="1"
              />
              <div style={{ display: "flex", gap: 6 }}>
                {MAU_PRESETS.map((p) => (
                  <button
                    key={p.value}
                    type="button"
                    onClick={() => { setUserVolume(p.value); setEstimation(null); }}
                    style={{
                      background: userVolume === p.value ? "var(--color-navy)" : "var(--color-bg)",
                      color: userVolume === p.value ? "#fff" : "var(--color-text-secondary)",
                      border: `1px solid ${userVolume === p.value ? "var(--color-navy)" : "var(--color-border)"}`,
                      borderRadius: "var(--radius-full)",
                      padding: "4px 14px",
                      fontSize: "0.78rem",
                      fontWeight: 600,
                      cursor: "pointer",
                      fontFamily: "var(--font-family)",
                      transition: "all 0.15s",
                    }}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Frequency selectors */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginBottom: 20 }}>
            {[
              { key: "profile", label: "Attributs Profil", desc: "tier, date inscription..." },
              { key: "behavior", label: "Attributs Comportement", desc: "panier, session, navigation..." },
              { key: "purchase", label: "Attributs Achat", desc: "points, revenus, historique..." },
            ].map((cat) => (
              <div key={cat.key}>
                <label className="label" style={{ marginBottom: 4, display: "block", fontSize: "0.8rem" }}>
                  {cat.label}
                </label>
                <span className="text-xs text-muted" style={{ display: "block", marginBottom: 6 }}>
                  {cat.desc}
                </span>
                <select
                  className="input"
                  value={frequencies[cat.key]}
                  onChange={(e) => handleFreqChange(cat.key, e.target.value)}
                  style={{ width: "100%" }}
                >
                  {FREQUENCY_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            ))}
          </div>

          {/* Bouton calculer */}
          <button
            className="btn btn-danger btn-lg"
            onClick={handleEstimate}
            disabled={loading}
            style={{ minWidth: 240 }}
          >
            {loading ? (
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span className="spinner spinner-sm" />
                Calcul en cours...
              </span>
            ) : (
              "Calculer l'estimation"
            )}
          </button>

          {error && (
            <div style={{
              background: "#FFF5F5", border: "1px solid #FED7D7", borderRadius: "var(--radius-md)",
              padding: "10px 14px", marginTop: 12, fontSize: "0.82rem", color: "#C53030",
            }}>
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Resultats de l'estimation */}
      {estimation && <DataPointsResult estimation={estimation} userVolume={userVolume} results={results} />}
    </div>
  );
}

function DataPointsResult({ estimation, userVolume, results }) {
  const { summary, breakdown, recommendations, cost_estimate: costEstimate } = estimation;
  const totalMonthly = summary.total_monthly_data_points;
  const freeCount = summary.free_attributes_count;
  const paidAttrCount = summary.custom_attributes_count;
  const eventsCount = summary.custom_events_count;
  const totalAttrs = freeCount + paidAttrCount;
  const freeRatio = totalAttrs > 0 ? (freeCount / totalAttrs) * 100 : 0;

  return (
    <div>
      {/* Hero: total mensuel */}
      <div
        className="card"
        style={{
          marginBottom: 20,
          background: "linear-gradient(135deg, #040066 0%, #1a1a8e 100%)",
          color: "#fff",
        }}
      >
        <div className="card-body" style={{ padding: "28px 32px", textAlign: "center" }}>
          <div style={{ fontSize: "0.8rem", fontWeight: 600, opacity: 0.7, marginBottom: 4, textTransform: "uppercase", letterSpacing: 1 }}>
            Estimation mensuelle
          </div>
          <div style={{ fontSize: "3rem", fontWeight: 900, lineHeight: 1.1, marginBottom: 4 }}>
            ~{formatDataPoints(totalMonthly)}
          </div>
          <div style={{ fontSize: "1rem", opacity: 0.8 }}>
            data points / mois
          </div>
          <div style={{ fontSize: "0.82rem", opacity: 0.6, marginTop: 8 }}>
            {formatDataPointsFull(totalMonthly)} data points/mois | {formatDataPointsFull(summary.total_yearly_data_points)} data points/an
          </div>
          <div style={{ fontSize: "0.78rem", opacity: 0.5, marginTop: 4 }}>
            Pour {formatDataPointsFull(userVolume)} MAU
          </div>
        </div>
      </div>

      {/* Compteurs */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 12, marginBottom: 24 }}>
        <div style={{ background: "rgba(34,197,94,0.08)", borderRadius: "var(--radius-md)", padding: "14px 16px", textAlign: "center" }}>
          <div style={{ fontSize: "1.6rem", fontWeight: 900, color: "#22C55E" }}>{freeCount}</div>
          <div style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--color-text-secondary)" }}>Attributs gratuits</div>
        </div>
        <div style={{ background: "rgba(245,158,11,0.08)", borderRadius: "var(--radius-md)", padding: "14px 16px", textAlign: "center" }}>
          <div style={{ fontSize: "1.6rem", fontWeight: 900, color: "#F59E0B" }}>{paidAttrCount}</div>
          <div style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--color-text-secondary)" }}>Custom Attributes</div>
        </div>
        <div style={{ background: "rgba(239,68,68,0.08)", borderRadius: "var(--radius-md)", padding: "14px 16px", textAlign: "center" }}>
          <div style={{ fontSize: "1.6rem", fontWeight: 900, color: "#EF4444" }}>{eventsCount}</div>
          <div style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--color-text-secondary)" }}>Custom Events</div>
        </div>
        <div style={{ background: "rgba(59,130,246,0.08)", borderRadius: "var(--radius-md)", padding: "14px 16px", textAlign: "center" }}>
          <div style={{ fontSize: "1.6rem", fontWeight: 900, color: "#3B82F6" }}>{costEstimate?.tier || "N/A"}</div>
          <div style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--color-text-secondary)" }}>Tier estime</div>
        </div>
      </div>

      {/* Barre de progression gratuit/payant */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-body" style={{ padding: "16px 20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
            <span style={{ fontSize: "0.82rem", fontWeight: 600 }}>Ratio attributs gratuits / payants</span>
            <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "#22C55E" }}>{freeRatio.toFixed(0)}% gratuit</span>
          </div>
          <div style={{
            height: 12, borderRadius: 6, background: "#f1f5f9", overflow: "hidden", display: "flex",
          }}>
            <div style={{ width: `${freeRatio}%`, background: "linear-gradient(90deg, #22C55E, #16A34A)", transition: "width 0.5s ease", borderRadius: "6px 0 0 6px" }} />
            <div style={{ width: `${100 - freeRatio}%`, background: "linear-gradient(90deg, #F59E0B, #EF4444)", transition: "width 0.5s ease", borderRadius: "0 6px 6px 0" }} />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6, fontSize: "0.72rem", color: "var(--color-text-secondary)" }}>
            <span>{freeCount} attributs gratuits</span>
            <span>{paidAttrCount} custom attributes payants</span>
          </div>
        </div>
      </div>

      {/* Tableau des custom attributes */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-body" style={{ padding: "16px 20px" }}>
          <h4 style={{ color: "var(--color-navy)", fontSize: "0.95rem", fontWeight: 700, marginBottom: 12 }}>
            Detail des attributs ({breakdown.custom_attributes?.length || 0})
          </h4>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid var(--color-border)" }}>
                  <th style={{ textAlign: "left", padding: "8px 10px", fontWeight: 700 }}>Attribut</th>
                  <th style={{ textAlign: "left", padding: "8px 10px", fontWeight: 700 }}>Type</th>
                  <th style={{ textAlign: "center", padding: "8px 10px", fontWeight: 700 }}>Frequence</th>
                  <th style={{ textAlign: "center", padding: "8px 10px", fontWeight: 700 }}>Statut</th>
                  <th style={{ textAlign: "right", padding: "8px 10px", fontWeight: 700 }}>Data points/mois</th>
                </tr>
              </thead>
              <tbody>
                {(breakdown.custom_attributes || []).map((attr, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid var(--color-border)", background: getRowBg(attr.monthly_data_points, attr.is_free) }}>
                    <td style={{ padding: "8px 10px", fontWeight: 600 }}>
                      <code style={{ fontSize: "0.78rem", background: "rgba(0,0,0,0.04)", padding: "2px 6px", borderRadius: 4 }}>
                        {attr.name}
                      </code>
                    </td>
                    <td style={{ padding: "8px 10px", color: "var(--color-text-secondary)" }}>{attr.type}</td>
                    <td style={{ textAlign: "center", padding: "8px 10px" }}>
                      <span style={{
                        fontSize: "0.72rem", padding: "2px 8px", borderRadius: "var(--radius-full)",
                        background: attr.is_free ? "rgba(34,197,94,0.1)" : "rgba(245,158,11,0.1)",
                        color: attr.is_free ? "#16A34A" : "#D97706",
                        fontWeight: 600,
                      }}>
                        {attr.frequency}
                      </span>
                    </td>
                    <td style={{ textAlign: "center", padding: "8px 10px" }}>
                      {attr.is_free ? (
                        <span style={{
                          fontSize: "0.72rem", padding: "2px 10px", borderRadius: "var(--radius-full)",
                          background: "#22C55E", color: "#fff", fontWeight: 700,
                        }}>
                          GRATUIT
                        </span>
                      ) : (
                        <span style={{
                          fontSize: "0.72rem", padding: "2px 10px", borderRadius: "var(--radius-full)",
                          background: attr.monthly_data_points >= 1_000_000 ? "#EF4444" : "#F59E0B",
                          color: "#fff", fontWeight: 700,
                        }}>
                          PAYANT
                        </span>
                      )}
                    </td>
                    <td style={{
                      textAlign: "right", padding: "8px 10px", fontWeight: 700, fontFamily: "monospace",
                      color: getCostColor(attr.monthly_data_points),
                    }}>
                      {attr.is_free ? "0" : formatDataPointsFull(attr.monthly_data_points)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Tableau des custom events */}
      {(breakdown.custom_events || []).length > 0 && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-body" style={{ padding: "16px 20px" }}>
            <h4 style={{ color: "var(--color-navy)", fontSize: "0.95rem", fontWeight: 700, marginBottom: 12 }}>
              Detail des custom events ({breakdown.custom_events.length})
            </h4>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid var(--color-border)" }}>
                    <th style={{ textAlign: "left", padding: "8px 10px", fontWeight: 700 }}>Evenement</th>
                    <th style={{ textAlign: "center", padding: "8px 10px", fontWeight: 700 }}>Occurrences moy./mois/user</th>
                    <th style={{ textAlign: "right", padding: "8px 10px", fontWeight: 700 }}>Data points/mois</th>
                  </tr>
                </thead>
                <tbody>
                  {breakdown.custom_events.map((evt, idx) => (
                    <tr key={idx} style={{ borderBottom: "1px solid var(--color-border)", background: getRowBg(evt.monthly_data_points, false) }}>
                      <td style={{ padding: "8px 10px", fontWeight: 600 }}>
                        <code style={{ fontSize: "0.78rem", background: "rgba(0,0,0,0.04)", padding: "2px 6px", borderRadius: 4 }}>
                          {evt.name}
                        </code>
                      </td>
                      <td style={{ textAlign: "center", padding: "8px 10px" }}>
                        <span style={{
                          fontSize: "0.78rem", padding: "2px 8px", borderRadius: "var(--radius-full)",
                          background: "rgba(239,68,68,0.1)", color: "#DC2626", fontWeight: 600,
                        }}>
                          {evt.avg_monthly_occurrences}x
                        </span>
                      </td>
                      <td style={{
                        textAlign: "right", padding: "8px 10px", fontWeight: 700, fontFamily: "monospace",
                        color: getCostColor(evt.monthly_data_points),
                      }}>
                        {formatDataPointsFull(evt.monthly_data_points)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Estimation de cout */}
      {costEstimate && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-body" style={{ padding: "16px 20px" }}>
            <h4 style={{ color: "var(--color-navy)", fontSize: "0.95rem", fontWeight: 700, marginBottom: 12 }}>
              Estimation de cout indicative
            </h4>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
              <div>
                <span style={{ fontSize: "0.75rem", color: "var(--color-text-secondary)", fontWeight: 600 }}>Tier Braze estime</span>
                <div style={{ fontSize: "1.1rem", fontWeight: 800, color: "var(--color-navy)", marginTop: 2 }}>
                  {costEstimate.tier}
                </div>
              </div>
              <div>
                <span style={{ fontSize: "0.75rem", color: "var(--color-text-secondary)", fontWeight: 600 }}>Fourchette de prix mensuel</span>
                <div style={{ fontSize: "1.1rem", fontWeight: 800, color: "#F59E0B", marginTop: 2 }}>
                  {costEstimate.estimated_monthly_cost_range}
                </div>
              </div>
            </div>
            <p style={{ fontSize: "0.75rem", color: "var(--color-text-secondary)", marginTop: 12, fontStyle: "italic" }}>
              {costEstimate.note}
            </p>
          </div>
        </div>
      )}

      {/* Recommandations */}
      {recommendations?.length > 0 && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-body" style={{ padding: "16px 20px" }}>
            <h4 style={{ color: "var(--color-navy)", fontSize: "0.95rem", fontWeight: 700, marginBottom: 12 }}>
              Recommandations d'optimisation
            </h4>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {recommendations.map((rec, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: "10px 14px",
                    background: "rgba(59,130,246,0.04)",
                    border: "1px solid rgba(59,130,246,0.12)",
                    borderRadius: "var(--radius-md)",
                    fontSize: "0.82rem",
                    lineHeight: 1.5,
                    color: "var(--color-text)",
                  }}
                >
                  <span style={{ fontWeight: 700, color: "#3B82F6", marginRight: 8 }}>Tip {idx + 1}</span>
                  {rec}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Export */}
      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
        <ExportButton
          data={estimation}
          filename="braze_data_points_estimation.json"
          label="Exporter l'estimation (JSON)"
          format="json"
        />
        <ExportButton
          data={formatDataPointsText(estimation, userVolume)}
          filename="braze_data_points_estimation.txt"
          label="Exporter l'estimation (Texte)"
          format="text"
        />
      </div>
    </div>
  );
}

function formatDataPointsText(estimation, userVolume) {
  if (!estimation) return "";
  const { summary, breakdown, recommendations, cost_estimate: costEstimate } = estimation;
  const lines = [
    "=== Estimation Data Points Braze ===",
    `MAU: ${formatDataPointsFull(userVolume)}`,
    `Total mensuel: ${formatDataPointsFull(summary.total_monthly_data_points)} data points`,
    `Total annuel: ${formatDataPointsFull(summary.total_yearly_data_points)} data points`,
    "",
    `Custom Attributes: ${summary.custom_attributes_count} (payants)`,
    `Attributs gratuits: ${summary.free_attributes_count}`,
    `Custom Events: ${summary.custom_events_count}`,
    "",
    "--- Detail des attributs ---",
  ];
  for (const attr of breakdown.custom_attributes || []) {
    const status = attr.is_free ? "[GRATUIT]" : `[${formatDataPointsFull(attr.monthly_data_points)} dp/mois]`;
    lines.push(`  ${attr.name} (${attr.type}) - ${attr.frequency} ${status}`);
  }
  lines.push("", "--- Detail des events ---");
  for (const evt of breakdown.custom_events || []) {
    lines.push(`  ${evt.name} - ${evt.avg_monthly_occurrences}x/mois/user [${formatDataPointsFull(evt.monthly_data_points)} dp/mois]`);
  }
  if (costEstimate) {
    lines.push("", "--- Estimation de cout ---");
    lines.push(`  Tier: ${costEstimate.tier}`);
    lines.push(`  Fourchette: ${costEstimate.estimated_monthly_cost_range}`);
    lines.push(`  ${costEstimate.note}`);
  }
  if (recommendations?.length) {
    lines.push("", "--- Recommandations ---");
    recommendations.forEach((r, i) => lines.push(`  ${i + 1}. ${r}`));
  }
  return lines.join("\n");
}

/* ── Composant principal ── */

export default function AnalysisResult({ result, onReset }) {
  const analyses = result.use_case_analysis || [];
  const nbAnalyses = analyses.length;
  const analysisId = result._response_id || null;

  return (
    <div>
      {/* Action bar */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16, flexWrap: "wrap", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button className="btn btn-secondary btn-sm" onClick={onReset}>
            &larr; Nouvelle analyse
          </button>
          <div
            style={{
              background: "rgba(59,130,246,0.06)",
              border: "1px solid rgba(59,130,246,0.15)",
              borderRadius: "var(--radius-md)",
              padding: "8px 14px",
              fontSize: "0.82rem",
              color: "#2B6CB0",
            }}
          >
            {nbAnalyses} use case(s) analyse(s) -- Parcourez les onglets pour explorer les resultats
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <DownloadButton
            url={`/data-model/export/${analysisId}?format=excel`}
            filename="braze_data_model.xlsx"
            label="Export Excel"
            icon={"\uD83D\uDCCA"}
            disabled={!analysisId}
          />
          <DownloadButton
            url={`/data-model/export/${analysisId}?format=csv`}
            filename="braze_data_model.csv"
            label="Export CSV"
            icon={"\uD83D\uDCC4"}
            disabled={!analysisId}
          />
          <ExportButton data={result} filename="braze_data_model.json" label="Export JSON" format="json" />
          <ExportButton
            data={formatResultsText(result)}
            filename="braze_data_model.txt"
            label="Export Texte"
            format="text"
          />
        </div>
      </div>

      {/* Error banner */}
      {result.error && (
        <div
          style={{
            background: "#FFF5F5",
            border: "1px solid #FED7D7",
            borderRadius: "var(--radius-md)",
            padding: "10px 14px",
            marginBottom: 16,
            fontSize: "0.82rem",
            color: "#C53030",
          }}
        >
          {result.error}
        </div>
      )}

      {/* Tabs */}
      <ResultTabs
        tabs={[
          {
            id: "data",
            label: "Donnees Requises",
            content: <DataTab results={result} />,
          },
          {
            id: "hierarchy",
            label: "Hierarchie",
            content: <HierarchyTab results={result} />,
          },
          {
            id: "datapoints",
            label: "Data Points",
            content: <DataPointsTab results={result} />,
          },
          {
            id: "json",
            label: "JSON",
            content: <JsonTab results={result} />,
          },
        ]}
      />
    </div>
  );
}
