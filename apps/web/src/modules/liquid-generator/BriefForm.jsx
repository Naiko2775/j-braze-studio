import { useState, useEffect, useMemo } from "react";
import { useApi } from "../../shared/hooks/useApi";
import { useProject } from "../../shared/context/ProjectContext";

/* ── Categories de templates ── */
const CATEGORIES = [
  { id: "banner", label: "Bannieres" },
  { id: "email", label: "Emails" },
  { id: "push", label: "Push" },
  { id: "sms", label: "SMS" },
];

/* ── Templates de bannieres (charges dynamiquement, fallback statique) ── */
const FALLBACK_TEMPLATES = [
  { id: "hero_banner", name: "Hero Banner", description: "Grande banniere promotionnelle plein ecran", category: "banner" },
  { id: "product_card", name: "Product Card", description: "Mise en avant d'un produit specifique", category: "banner" },
  { id: "countdown", name: "Countdown", description: "Offre limitee avec urgence", category: "banner" },
  { id: "cta_simple", name: "CTA Simple", description: "Banniere minimaliste avec call-to-action", category: "banner" },
  { id: "testimonial", name: "Testimonial", description: "Social proof / avis client", category: "banner" },
  { id: "welcome_email", name: "Welcome Email", description: "Email de bienvenue avec avantages et onboarding", category: "email" },
  { id: "abandoned_cart_email", name: "Abandoned Cart Email", description: "Relance panier abandonne avec produits et recommandations", category: "email" },
  { id: "loyalty_email", name: "Loyalty Program Email", description: "Email fidelite avec statut, points et avantages exclusifs", category: "email" },
  { id: "post_purchase_email", name: "Post-Purchase Email", description: "Confirmation commande avec cross-sell et enquete NPS", category: "email" },
  { id: "winback_email", name: "Win-Back Email", description: "Email de reconquete avec offre personnalisee et urgence", category: "email" },
  { id: "push_notification", name: "Push Notification", description: "Notification push mobile avec titre, corps, image et deep link", category: "push" },
  { id: "sms_message", name: "SMS", description: "Message SMS court avec lien et opt-out (max 160 chars)", category: "sms" },
];

const CHANNELS = [
  { id: "email", label: "Email" },
  { id: "in-app", label: "In-App" },
  { id: "content-card", label: "Content Card" },
  { id: "push", label: "Push" },
  { id: "sms", label: "SMS" },
];

const EXAMPLE_BRIEFS_BY_CATEGORY = {
  banner: [
    {
      label: "Soldes VIP",
      brief:
        "Banniere soldes d'ete pour nos clients VIP, ton premium et exclusif, couleurs #040066 et #f00a0a, CTA vers /collection-ete",
    },
    {
      label: "Promo Flash",
      brief:
        "Promo flash -30% sur les sneakers, segment jeunes 18-25, ton dynamique et fun, urgence 48h",
    },
    {
      label: "Bienvenue",
      brief:
        "Bienvenue aux nouveaux inscrits, ton chaleureux, avec prenom personnalise, CTA vers l'onboarding",
    },
    {
      label: "Testimonial",
      brief:
        "Banniere testimonial client satisfait pour notre assurance auto, ton rassurant et professionnel",
    },
  ],
  email: [
    {
      label: "Welcome",
      brief:
        "Email de bienvenue pour nouveaux inscrits e-commerce mode, ton chaleureux, 3 avantages (livraison gratuite, retours 30j, programme fidelite), CTA vers /mon-compte",
    },
    {
      label: "Panier abandonne",
      brief:
        "Email de relance panier abandonne pour e-commerce beaute, rappeler les produits laisses, afficher le total, recommandations, CTA Finaliser ma commande",
    },
    {
      label: "Fidelite",
      brief:
        "Email programme fidelite pour clients existants, afficher leur statut Bronze/Silver/Gold, points actuels et prochain palier, avantages exclusifs",
    },
    {
      label: "Win-back",
      brief:
        "Email win-back pour clients inactifs depuis 90+ jours, offre -20% avec code promo unique, best-sellers, compteur d'expiration, ton amical",
    },
  ],
  push: [
    {
      label: "Promo Flash",
      brief:
        "Push notification promo flash pour app e-commerce, personnalise avec prenom et ville, deep link vers /promo, 2 boutons Voir / Plus tard",
    },
    {
      label: "Rappel panier",
      brief:
        "Push rappel panier abandonne, ton amical, inclure le nombre d'articles, deep link vers le checkout",
    },
  ],
  sms: [
    {
      label: "Promo code",
      brief:
        "SMS promo soldes d'ete, personnalise avec prenom, code promo ETE25, lien court vers le site, mention STOP",
    },
    {
      label: "Flash sale",
      brief:
        "SMS vente flash 24h, ton urgent, lien court, opt-out STOP au 36200",
    },
  ],
};

export default function BriefForm({ onResult }) {
  const [brief, setBrief] = useState("");
  const [category, setCategory] = useState("banner");
  const [templateType, setTemplateType] = useState("hero_banner");
  const [channel, setChannel] = useState("email");
  const [projectName, setProjectName] = useState("");
  const [templates, setTemplates] = useState(FALLBACK_TEMPLATES);

  const { loading, error, call } = useApi();
  const { call: fetchTemplates } = useApi();
  const { currentProject } = useProject();

  // Pre-fill project name from context
  useEffect(() => {
    if (currentProject && !projectName) {
      setProjectName(currentProject.name);
    }
  }, [currentProject]); // eslint-disable-line react-hooks/exhaustive-deps

  /* Charge la liste des templates depuis l'API */
  useEffect(() => {
    fetchTemplates("/liquid/templates")
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setTemplates(data);
        }
      })
      .catch(() => {
        /* Utilise le fallback statique */
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /* Templates filtres par categorie */
  const filteredTemplates = useMemo(
    () => templates.filter((tpl) => (tpl.category || "banner") === category),
    [templates, category]
  );

  /* Exemples de briefs selon la categorie */
  const exampleBriefs = EXAMPLE_BRIEFS_BY_CATEGORY[category] || EXAMPLE_BRIEFS_BY_CATEGORY.banner;

  /* Reset le template selectionne quand la categorie change */
  useEffect(() => {
    if (filteredTemplates.length > 0) {
      setTemplateType(filteredTemplates[0].id);
    }
  }, [category]); // eslint-disable-line react-hooks/exhaustive-deps

  /* Auto-select channel based on category */
  useEffect(() => {
    if (category === "push") setChannel("push");
    else if (category === "sms") setChannel("sms");
    else if (category === "email" || category === "banner") setChannel("email");
  }, [category]);

  const handleExampleClick = (exampleBrief) => {
    setBrief(exampleBrief);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!brief.trim()) return;

    try {
      const response = await call("/liquid/generate", {
        method: "POST",
        body: JSON.stringify({
          brief: brief.trim(),
          template_type: templateType,
          channel,
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

  const categoryLabels = {
    banner: "Generez une banniere Braze",
    email: "Generez un email complet Braze",
    push: "Generez une notification push Braze",
    sms: "Generez un SMS Braze",
  };

  const briefPlaceholders = {
    banner: "Decrivez votre banniere : audience, ton, couleurs, message, CTA, personnalisation souhaitee...",
    email: "Decrivez votre email : type (bienvenue, relance, fidelite...), audience, ton, blocs souhaites, CTA...",
    push: "Decrivez votre push : message court, audience, deep link, boutons d'action...",
    sms: "Decrivez votre SMS : message court (max 160 chars), code promo, lien, opt-out...",
  };

  const submitLabels = {
    banner: "Generer la banniere",
    email: "Generer l'email",
    push: "Generer la notification push",
    sms: "Generer le SMS",
  };

  return (
    <div className="card">
      <div className="card-body">
        <div style={{ marginBottom: 20 }}>
          <h2
            style={{
              color: "var(--color-navy)",
              fontSize: "1.15rem",
              fontWeight: 700,
              marginBottom: 4,
            }}
          >
            {categoryLabels[category] || categoryLabels.banner}
          </h2>
          <span className="text-sm text-muted">
            Decrivez votre brief creatif pour generer un template avec code Liquid, preview et variantes A/B
          </span>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Category selector */}
          <div className="form-group">
            <label className="label">Categorie</label>
            <div
              style={{
                display: "flex",
                gap: 0,
                borderRadius: "var(--radius-md)",
                overflow: "hidden",
                border: "1px solid var(--color-border)",
              }}
            >
              {CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => setCategory(cat.id)}
                  disabled={loading}
                  style={{
                    flex: 1,
                    padding: "10px 16px",
                    border: "none",
                    background: category === cat.id ? "var(--color-navy)" : "var(--color-bg)",
                    color: category === cat.id ? "#fff" : "var(--color-text-secondary)",
                    fontWeight: 600,
                    fontSize: "0.85rem",
                    cursor: loading ? "not-allowed" : "pointer",
                    transition: "all 0.15s",
                    fontFamily: "var(--font-family)",
                    opacity: loading ? 0.5 : 1,
                    borderRight: "1px solid var(--color-border)",
                  }}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* Project name (optional) */}
          <div className="form-group">
            <label className="label" htmlFor="lq-project-name">
              Nom du projet (optionnel)
            </label>
            <input
              id="lq-project-name"
              className="input"
              type="text"
              placeholder="Ex: Client XYZ - Campagne ete"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              disabled={loading}
            />
          </div>

          {/* Brief textarea */}
          <div className="form-group">
            <label className="label" htmlFor="lq-brief">
              Brief creatif
            </label>
            <textarea
              id="lq-brief"
              className="textarea"
              placeholder={briefPlaceholders[category] || briefPlaceholders.banner}
              value={brief}
              onChange={(e) => setBrief(e.target.value)}
              disabled={loading}
              style={{ minHeight: 130 }}
            />
          </div>

          {/* Example briefs chips */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              flexWrap: "wrap",
              marginBottom: 20,
            }}
          >
            <span className="text-xs text-muted font-semibold">Exemples :</span>
            {exampleBriefs.map((ex) => (
              <button
                key={ex.label}
                type="button"
                onClick={() => handleExampleClick(ex.brief)}
                disabled={loading}
                style={{
                  background: "var(--color-bg)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-full)",
                  padding: "5px 14px",
                  fontSize: "0.78rem",
                  color: "var(--color-text-secondary)",
                  fontWeight: 600,
                  cursor: loading ? "not-allowed" : "pointer",
                  transition: "all 0.15s",
                  fontFamily: "var(--font-family)",
                  opacity: loading ? 0.5 : 1,
                }}
                onMouseEnter={(e) => {
                  if (!loading) {
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
                {ex.label}
              </button>
            ))}
          </div>

          {/* Template selector */}
          <div className="form-group">
            <label className="label" htmlFor="lq-template">
              Type de template
            </label>
            <select
              id="lq-template"
              className="select"
              value={templateType}
              onChange={(e) => setTemplateType(e.target.value)}
              disabled={loading}
            >
              {filteredTemplates.map((tpl) => (
                <option key={tpl.id} value={tpl.id}>
                  {tpl.name} — {tpl.description}
                </option>
              ))}
            </select>
          </div>

          {/* Channel selector */}
          <div className="form-group">
            <label className="label" htmlFor="lq-channel">
              Canal
            </label>
            <select
              id="lq-channel"
              className="select"
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
              disabled={loading}
            >
              {CHANNELS.map((ch) => (
                <option key={ch.id} value={ch.id}>
                  {ch.label}
                </option>
              ))}
            </select>
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
            disabled={loading || !brief.trim()}
          >
            {loading ? (
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span className="spinner spinner-sm" />
                Generation en cours...
              </span>
            ) : (
              submitLabels[category] || submitLabels.banner
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
