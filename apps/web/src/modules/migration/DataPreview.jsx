import { useState, useEffect } from "react";
import { useApi } from "../../shared/hooks/useApi";

function formatNumber(n) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

export default function DataPreview({ platform, credentials, onPreviewData }) {
  const { data, loading, error, call } = useApi();
  const [deduplicate, setDeduplicate] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const handleLoadPreview = async () => {
    try {
      const result = await call(`/migration/preview/${platform}`, {
        method: "POST",
        body: JSON.stringify({ credentials, deduplicate_by_email: deduplicate }),
      });
      setLoaded(true);
      if (onPreviewData) onPreviewData({ ...result, deduplicate_by_email: deduplicate });
    } catch {
      // handled by useApi
    }
  };

  // Notify parent of dedup change
  useEffect(() => {
    if (data && onPreviewData) {
      onPreviewData({ ...data, deduplicate_by_email: deduplicate });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deduplicate]);

  const contacts = data?.sample || [];
  const contactCount = data?.contacts_count || contacts.length;
  const segmentCount = data?.segment_count || 0;
  const templateCount = data?.template_count || 0;
  const avgAttributes = data?.avg_attributes || 0;
  const dataPoints = contactCount * avgAttributes;

  return (
    <div className="card">
      <div className="card-body">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
          <div>
            <h2 style={{ color: "var(--color-navy)", fontSize: "1.15rem", fontWeight: 700, marginBottom: 4 }}>
              Apercu des donnees
            </h2>
            <span className="text-sm text-muted">
              Visualisez les contacts et estimez l'impact en data points avant migration
            </span>
          </div>
          <button
            className="btn btn-primary"
            onClick={handleLoadPreview}
            disabled={loading}
          >
            {loading ? (
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span className="spinner spinner-sm" />
                Chargement...
              </span>
            ) : loaded ? "Rafraichir" : "Charger l'apercu"}
          </button>
        </div>

        {/* Deduplication option */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={deduplicate}
              onChange={(e) => setDeduplicate(e.target.checked)}
              style={{ width: 18, height: 18, accentColor: "var(--color-navy)" }}
            />
            <span className="text-sm font-semibold" style={{ color: "var(--color-text)" }}>
              Dedupliquer par email
            </span>
            <span className="text-xs text-muted">
              (supprime les doublons avant migration)
            </span>
          </label>
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

        {loaded && data && (
          <>
            {/* Stat counters */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12, marginBottom: 20 }}>
              <StatCard label="Contacts" value={formatNumber(contactCount)} color="var(--color-navy)" />
              <StatCard label="Segments" value={String(segmentCount)} color="var(--color-navy)" />
              <StatCard label="Templates" value={String(templateCount)} color="var(--color-navy)" />
              <StatCard label="Attr. moy. / contact" value={String(avgAttributes)} color="var(--color-navy)" />
            </div>

            {/* Data points estimation alert */}
            <div style={{
              background: dataPoints > 1_000_000 ? "rgba(245, 158, 11, 0.08)" : "rgba(59, 130, 246, 0.06)",
              border: `1px solid ${dataPoints > 1_000_000 ? "rgba(245, 158, 11, 0.3)" : "rgba(59, 130, 246, 0.2)"}`,
              borderRadius: "var(--radius-md)",
              padding: "14px 18px",
              marginBottom: 20,
              display: "flex",
              alignItems: "flex-start",
              gap: 12,
            }}>
              <span style={{ fontSize: "1.3rem", lineHeight: 1 }}>
                {dataPoints > 1_000_000 ? "\u26A0" : "\u2139"}
              </span>
              <div>
                <div className="font-semibold text-sm" style={{ color: dataPoints > 1_000_000 ? "#d97706" : "#2563eb", marginBottom: 2 }}>
                  Estimation data points
                </div>
                <div className="text-sm" style={{ color: "var(--color-text)" }}>
                  {formatNumber(contactCount)} contacts x {avgAttributes} attributs ={" "}
                  <strong>{formatNumber(dataPoints)} data points</strong>
                </div>
                <div className="text-xs text-muted" style={{ marginTop: 4 }}>
                  Chaque attribut ecrit via /users/track consomme 1 data point Braze.
                  {deduplicate && " La deduplication par email reduira le nombre reel."}
                  {" "}Utilisez le mode Dry Run pour valider sans consommer.
                </div>
              </div>
            </div>

            {/* Contacts table */}
            {contacts.length > 0 && (
              <div style={{ overflowX: "auto" }}>
                <table style={{
                  width: "100%",
                  borderCollapse: "collapse",
                  fontSize: "0.82rem",
                }}>
                  <thead>
                    <tr style={{ borderBottom: "2px solid var(--color-border)" }}>
                      {["ID", "Email", "Prenom", "Nom", "Telephone", "Pays", "Abonnement", "Attr. custom"].map((h) => (
                        <th
                          key={h}
                          style={{
                            textAlign: "left",
                            padding: "10px 12px",
                            fontWeight: 700,
                            color: "var(--color-text-secondary)",
                            fontSize: "0.75rem",
                            textTransform: "uppercase",
                            letterSpacing: "0.5px",
                          }}
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {contacts.map((c, i) => (
                      <tr
                        key={c.external_id || i}
                        style={{
                          borderBottom: "1px solid var(--color-border-light)",
                          background: i % 2 === 0 ? "transparent" : "rgba(0,0,0,0.015)",
                        }}
                      >
                        <td style={{ padding: "8px 12px", fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
                          {c.external_id || "-"}
                        </td>
                        <td style={{ padding: "8px 12px" }}>{c.email || "-"}</td>
                        <td style={{ padding: "8px 12px" }}>{c.first_name || "-"}</td>
                        <td style={{ padding: "8px 12px" }}>{c.last_name || "-"}</td>
                        <td style={{ padding: "8px 12px" }}>{c.phone || "-"}</td>
                        <td style={{ padding: "8px 12px" }}>{c.country || "-"}</td>
                        <td style={{ padding: "8px 12px" }}>
                          <span className={`badge ${c.email_subscribe === "subscribed" ? "badge-success" : "badge-neutral"}`}>
                            <span className="badge-dot" />
                            {c.email_subscribe || "-"}
                          </span>
                        </td>
                        <td style={{ padding: "8px 12px", textAlign: "center" }}>
                          {c.custom_attributes_count ?? (c.custom_attributes?.length || 0)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {contacts.length === 0 && (
              <div style={{ textAlign: "center", padding: "32px 16px", color: "var(--color-text-muted)" }}>
                Aucun contact trouve pour cette plateforme.
              </div>
            )}
          </>
        )}

        {/* Empty state */}
        {!loaded && !loading && (
          <div style={{ textAlign: "center", padding: "40px 16px" }}>
            <div style={{ fontSize: "2rem", marginBottom: 8, opacity: 0.3 }}>&#128202;</div>
            <p className="text-sm text-muted">
              Cliquez sur "Charger l'apercu" pour visualiser les donnees source
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div style={{
      background: "var(--color-bg)",
      border: "1px solid var(--color-border)",
      borderRadius: "var(--radius-md)",
      padding: "14px 16px",
      textAlign: "center",
    }}>
      <div style={{ fontSize: "1.5rem", fontWeight: 700, color }}>{value}</div>
      <div className="text-xs text-muted" style={{ marginTop: 2, textTransform: "uppercase", letterSpacing: "0.5px", fontWeight: 600 }}>
        {label}
      </div>
    </div>
  );
}
