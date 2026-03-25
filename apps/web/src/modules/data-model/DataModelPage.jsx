import { useState } from "react";
import { useLocation } from "react-router-dom";
import AnalysisForm from "./AnalysisForm";
import AnalysisResult from "./AnalysisResult";
import EntityExplorer from "./EntityExplorer";

export default function DataModelPage() {
  const [result, setResult] = useState(null);
  const location = useLocation();

  // Si le path est /data-model/explorer, afficher l'EntityExplorer
  const isExplorerView = location.pathname.includes("/data-model/explorer");

  if (isExplorerView) {
    return <EntityExplorer />;
  }

  return (
    <div>
      {!result ? (
        <>
          <AnalysisForm onResult={setResult} />

          {/* Empty state */}
          <div style={{ textAlign: "center", padding: "48px 16px 24px" }}>
            <div style={{ color: "var(--color-red)", fontSize: "2.2rem", marginBottom: 8 }}>
              {"\u26A1"}
            </div>
            <h3 style={{ color: "var(--color-navy)", fontSize: "1.05rem", fontWeight: 700, marginBottom: 6 }}>
              Pret a analyser
            </h3>
            <p
              style={{
                color: "var(--color-text-secondary)",
                fontSize: "0.86rem",
                maxWidth: 440,
                margin: "0 auto",
                lineHeight: 1.55,
              }}
            >
              Decrivez votre use case metier dans le formulaire ci-dessus et laissez
              l'agent identifier les donnees Braze necessaires, les segments,
              les canaux de messaging et la hierarchie du data model.
            </p>
          </div>
        </>
      ) : (
        <AnalysisResult result={result} onReset={() => setResult(null)} />
      )}
    </div>
  );
}
