import { useState } from "react";
import BriefForm from "./BriefForm";
import LiquidResult from "./LiquidResult";

export default function LiquidPage() {
  const [result, setResult] = useState(null);

  return (
    <div>
      {!result ? (
        <>
          <BriefForm onResult={setResult} />

          {/* Empty state */}
          <div style={{ textAlign: "center", padding: "48px 16px 24px" }}>
            <div style={{ color: "var(--color-red)", fontSize: "2.2rem", marginBottom: 8 }}>
              {"\u2728"}
            </div>
            <h3
              style={{
                color: "var(--color-navy)",
                fontSize: "1.05rem",
                fontWeight: 700,
                marginBottom: 6,
              }}
            >
              Pret a generer
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
              Decrivez votre brief creatif dans le formulaire ci-dessus pour generer
              un template de banniere Braze avec code Liquid, preview visuel
              et variantes A/B.
            </p>
          </div>
        </>
      ) : (
        <LiquidResult result={result} onReset={() => setResult(null)} />
      )}
    </div>
  );
}
