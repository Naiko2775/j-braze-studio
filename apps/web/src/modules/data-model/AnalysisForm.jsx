import { useState, useEffect } from "react";
import { useApi } from "../../shared/hooks/useApi";
import { useProject } from "../../shared/context/ProjectContext";

const TEMPLATES = [
  {
    icon: "mail",
    label: "Bienvenue",
    brief:
      "Parcours de bienvenue multi-canal : email de bienvenue J+0, push de decouverte J+2, SMS promo J+5. Audience : nouveaux inscrits. Objectif : activer les utilisateurs et presenter les fonctionnalites cles.",
  },
  {
    icon: "cart",
    label: "Panier abandonne",
    brief:
      "Relance panier abandonne : email H+2 avec produits laisses dans le panier, push H+24 avec recommandation produit similaire, SMS J+3 avec code promo -10%. Audience : utilisateurs ayant ajoute au panier sans acheter.",
  },
  {
    icon: "star",
    label: "Fidelite",
    brief:
      "Programme de fidelite a 4 paliers (Bronze, Silver, Gold, Platinum). Notifications de progression, recompenses par palier, offres exclusives. Canaux : email + push + in-app. Objectif : augmenter la retention et le panier moyen.",
  },
  {
    icon: "clock",
    label: "Reactivation",
    brief:
      "Campagne de reactivation win-back : email J+14 d'inactivite avec offre personnalisee, push J+21 avec nouveautes, SMS J+30 avec code promo exclusif -20%. Audience : utilisateurs inactifs depuis 14+ jours.",
  },
  {
    icon: "bell",
    label: "Transactionnel",
    brief:
      "Messages transactionnels : confirmation de commande (email), notification d'expedition (push), alerte de livraison (SMS), demande d'avis post-achat J+7 (email). Objectif : informer et rassurer le client.",
  },
];

const ICON_MAP = {
  mail: "\u2709",
  cart: "\uD83D\uDED2",
  star: "\u2B50",
  clock: "\uD83D\uDD50",
  bell: "\uD83D\uDD14",
};

export default function AnalysisForm({ onResult, loading: externalLoading }) {
  const [useCase, setUseCase] = useState("");
  const [projectName, setProjectName] = useState("");
  const { loading, error, call } = useApi();
  const { currentProject } = useProject();

  // Pre-fill project name from context
  useEffect(() => {
    if (currentProject && !projectName) {
      setProjectName(currentProject.name);
    }
  }, [currentProject]); // eslint-disable-line react-hooks/exhaustive-deps

  const isLoading = loading || externalLoading;

  const handleTemplateClick = (brief) => {
    setUseCase(brief);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!useCase.trim()) return;

    try {
      const response = await call("/data-model/analyze", {
        method: "POST",
        body: JSON.stringify({
          use_cases: [useCase.trim()],
          project_name: projectName.trim() || undefined,
          project_id: currentProject?.id || undefined,
        }),
      });
      // Backend returns { id, result, created_at } — extract the actual content
      const payload = response.result || response;
      if (response.id) payload._response_id = response.id;
      onResult(payload);
    } catch {
      // error is handled by useApi
    }
  };

  return (
    <div className="card">
      <div className="card-body">
        <div style={{ marginBottom: 20 }}>
          <h2 style={{ color: "var(--color-navy)", fontSize: "1.15rem", fontWeight: 700, marginBottom: 4 }}>
            Analysez votre use case Braze
          </h2>
          <span className="text-sm text-muted">
            Decrivez votre scenario marketing pour identifier les donnees Braze necessaires
          </span>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Project name (optional) */}
          <div className="form-group">
            <label className="label" htmlFor="dm-project-name">
              Nom du projet (optionnel)
            </label>
            <input
              id="dm-project-name"
              className="input"
              type="text"
              placeholder="Ex: Client XYZ - Onboarding"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              disabled={isLoading}
            />
          </div>

          {/* Use case textarea */}
          <div className="form-group">
            <label className="label" htmlFor="dm-use-case">
              Use case
            </label>
            <textarea
              id="dm-use-case"
              className="textarea"
              placeholder="Decrivez votre scenario : audience ciblee, canaux (email, push, SMS...), declenchement, objectif marketing..."
              value={useCase}
              onChange={(e) => setUseCase(e.target.value)}
              disabled={isLoading}
              style={{ minHeight: 130 }}
            />
          </div>

          {/* Template chips */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 20 }}>
            <span className="text-xs text-muted font-semibold">Templates :</span>
            {TEMPLATES.map((tpl) => (
              <button
                key={tpl.label}
                type="button"
                onClick={() => handleTemplateClick(tpl.brief)}
                disabled={isLoading}
                style={{
                  background: "var(--color-bg)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-full)",
                  padding: "5px 14px",
                  fontSize: "0.78rem",
                  color: "var(--color-text-secondary)",
                  fontWeight: 600,
                  cursor: isLoading ? "not-allowed" : "pointer",
                  transition: "all 0.15s",
                  fontFamily: "var(--font-family)",
                  opacity: isLoading ? 0.5 : 1,
                }}
                onMouseEnter={(e) => {
                  if (!isLoading) {
                    e.target.style.background = "var(--color-navy)";
                    e.target.style.color = "#fff";
                    e.target.style.borderColor = "var(--color-navy)";
                  }
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = "var(--color-bg)";
                  e.target.style.color = "var(--color-text-secondary)";
                  e.target.style.borderColor = "var(--color-border)";
                }}
              >
                {ICON_MAP[tpl.icon]} {tpl.label}
              </button>
            ))}
          </div>

          {/* Error */}
          {error && (
            <div
              style={{
                background: "#FFF5F5",
                border: "1px solid #FED7D7",
                borderRadius: "var(--radius-md)",
                padding: "10px 14px",
                marginBottom: 16,
                fontSize: "0.82rem",
                color: "#C53030",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              {error}
            </div>
          )}

          {/* Submit button */}
          <button
            type="submit"
            className="btn btn-danger btn-lg w-full"
            disabled={isLoading || !useCase.trim()}
          >
            {isLoading ? (
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span className="spinner spinner-sm" />
                Analyse en cours...
              </span>
            ) : (
              "Generer le data model"
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
