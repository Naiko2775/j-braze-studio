import ResultTabs from "../../shared/components/ResultTabs";
import CodeBlock from "../../shared/components/CodeBlock";
import ExportButton from "../../shared/components/ExportButton";
import BannerPreview from "./BannerPreview";

/* ── Sous-composants pour chaque onglet ── */

function PreviewTab({ result }) {
  return (
    <div>
      <BannerPreview data={result} />

      {/* Notes de personnalisation */}
      {result.personalization_notes && (
        <div
          style={{
            marginTop: 16,
            background: "rgba(59,130,246,0.06)",
            border: "1px solid rgba(59,130,246,0.15)",
            borderRadius: "var(--radius-md)",
            padding: "12px 16px",
            fontSize: "0.82rem",
            color: "#2B6CB0",
            lineHeight: 1.55,
          }}
        >
          <strong style={{ display: "block", marginBottom: 4, fontSize: "0.78rem" }}>
            Variables Liquid utilisees
          </strong>
          {result.personalization_notes}
        </div>
      )}
    </div>
  );
}

function LiquidCodeTab({ result }) {
  const code = result.liquid_code || "<!-- Aucun code Liquid genere -->";
  return (
    <div>
      <CodeBlock code={code} language="html" maxHeight={600} />
    </div>
  );
}

function JsonTab({ result }) {
  const json = JSON.stringify(result.params || result, null, 2);
  return (
    <div>
      <CodeBlock code={json} language="json" maxHeight={600} />
    </div>
  );
}

function VariantsTab({ result }) {
  const variants = result.ab_variants || [];

  if (variants.length === 0) {
    return (
      <p className="text-sm text-muted" style={{ padding: "16px 0" }}>
        Aucune variante A/B generee pour ce brief.
      </p>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {variants.map((v, idx) => (
        <div
          key={idx}
          className="card"
          style={{
            borderLeft: `4px solid ${idx === 0 ? "var(--color-navy)" : "var(--color-red)"}`,
          }}
        >
          <div className="card-body" style={{ padding: "16px 18px" }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                marginBottom: 10,
              }}
            >
              <span
                style={{
                  background: idx === 0 ? "var(--color-navy)" : "var(--color-red)",
                  color: "#fff",
                  width: 28,
                  height: 28,
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 13,
                  fontWeight: 700,
                  flexShrink: 0,
                }}
              >
                {v.variant || String.fromCharCode(65 + idx)}
              </span>
              <h4
                style={{
                  color: "var(--color-navy)",
                  fontSize: "0.95rem",
                  fontWeight: 700,
                  margin: 0,
                }}
              >
                Variante {v.variant || String.fromCharCode(65 + idx)}
              </h4>
            </div>

            <div
              style={{
                background: "var(--color-bg)",
                borderRadius: "var(--radius-md)",
                padding: "12px 16px",
                marginBottom: 10,
                fontSize: "1rem",
                fontWeight: 600,
                color: "var(--color-text)",
                lineHeight: 1.4,
              }}
            >
              "{v.headline}"
            </div>

            {v.rationale && (
              <p
                className="text-sm text-secondary"
                style={{ lineHeight: 1.5, margin: 0 }}
              >
                <strong>Rationale :</strong> {v.rationale}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Composant principal ── */

export default function LiquidResult({ result, onReset }) {
  const templateLabel = result.template
    ? result.template.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
    : "Banniere";

  return (
    <div>
      {/* Action bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 16,
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button className="btn btn-secondary btn-sm" onClick={onReset}>
            &larr; Nouveau brief
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
            {templateLabel} generee -- Parcourez les onglets pour explorer les resultats
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <ExportButton
            data={result}
            filename="braze_liquid_banner.json"
            label="Export JSON"
            format="json"
          />
          <ExportButton
            data={result.liquid_code || ""}
            filename="braze_banner.html"
            label="Export HTML"
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
            id: "preview",
            label: "Preview",
            content: <PreviewTab result={result} />,
          },
          {
            id: "liquid",
            label: "Code Liquid",
            content: <LiquidCodeTab result={result} />,
          },
          {
            id: "json",
            label: "JSON",
            content: <JsonTab result={result} />,
          },
          {
            id: "variants",
            label: "Variantes A/B",
            content: <VariantsTab result={result} />,
          },
        ]}
      />
    </div>
  );
}
