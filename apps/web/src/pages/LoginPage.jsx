import { useState, useMemo } from "react";
import { useAuth } from "../shared/context/AuthContext";
import "./LoginPage.css";

/* ──────────────────────────────────────────────
   Floating marketing element definitions
   ────────────────────────────────────────────── */

function makeEmailBanner(i) {
  const colors = ["#f00a0a", "#040066", "#3b82f6", "#8b5cf6", "#ec4899"];
  const subjects = [
    "Bienvenue chez nous !",
    "Offre exclusive -30%",
    "Votre commande est prete",
    "Nouvel arrivage",
    "Derniere chance !",
  ];
  const c = colors[i % colors.length];
  return (
    <div className="float-email" key={`email-${i}`}>
      <div className="float-email__header" style={{ background: c }} />
      <div className="float-email__body">
        <div className="float-email__title">{subjects[i % subjects.length]}</div>
        <div className="float-email__text">Lorem ipsum dolor sit amet consectetur...</div>
        <div className="float-email__cta" style={{ background: c }}>Decouvrir</div>
      </div>
    </div>
  );
}

function makePushNotif(i) {
  const titles = ["Mon App", "Braze", "Store", "Promo", "Alerte"];
  const messages = [
    "Vous avez un nouveau message !",
    "Offre flash : -50% aujourd'hui",
    "Votre colis est en route",
    "N'oubliez pas votre panier",
    "Nouvelle fonctionnalite dispo",
  ];
  const icons = ["\u{1F514}", "\u{1F4E6}", "\u{1F381}", "\u{1F525}", "\u{2B50}"];
  return (
    <div className="float-push" key={`push-${i}`}>
      <div className="float-push__icon">{icons[i % icons.length]}</div>
      <div className="float-push__content">
        <div className="float-push__app">{titles[i % titles.length]}</div>
        <div className="float-push__msg">{messages[i % messages.length]}</div>
      </div>
    </div>
  );
}

function makeSMS(i) {
  const texts = [
    "Bonjour ! Votre code promo : BRAZE20",
    "RDV confirme pour demain 14h",
    "Merci pour votre achat !",
    "Votre solde de points : 2 450",
    "Nouveau : decouvrez notre app",
  ];
  const isBlue = i % 2 === 0;
  return (
    <div className={`float-sms ${isBlue ? "float-sms--blue" : "float-sms--green"}`} key={`sms-${i}`}>
      {texts[i % texts.length]}
    </div>
  );
}

function makeSegmentBadge(i) {
  const segments = [
    "VIP Gold", "Panier abandonne", "Inactifs 30j", "Nouveaux inscrits",
    "Top acheteurs", "Churners", "Engages 7j", "Newsletter",
    "Mobile only", "High LTV",
  ];
  const colors = ["#8b5cf6", "#f00a0a", "#f59e0b", "#22c55e", "#3b82f6", "#ec4899"];
  const c = colors[i % colors.length];
  return (
    <div className="float-segment" style={{ background: c }} key={`seg-${i}`}>
      {segments[i % segments.length]}
    </div>
  );
}

function makeKPICard(i) {
  const kpis = [
    { value: "12.4K", label: "emails envoyes" },
    { value: "98.2%", label: "delivrabilite" },
    { value: "+24%", label: "CTR" },
    { value: "3.1M", label: "utilisateurs" },
    { value: "45.8%", label: "taux ouverture" },
    { value: "1.2K", label: "conversions" },
    { value: "-12%", label: "desabonnements" },
    { value: "89%", label: "inbox rate" },
  ];
  const kpi = kpis[i % kpis.length];
  return (
    <div className="float-kpi" key={`kpi-${i}`}>
      <div className="float-kpi__value">{kpi.value}</div>
      <div className="float-kpi__label">{kpi.label}</div>
    </div>
  );
}

function makeLiquidTag(i) {
  const tags = [
    "{{first_name}}",
    "{{email}}",
    '{% if vip %}',
    "{{loyalty_points}}",
    '{% abort_message %}',
    "{{city}}",
    '{% connected_content %}',
    "{{product_name | default: 'ami'}}",
  ];
  return (
    <div className="float-liquid" key={`liq-${i}`}>
      <code>{tags[i % tags.length]}</code>
    </div>
  );
}

function makeChannelIcon(i) {
  const icons = ["\u{2709}\uFE0F", "\u{1F514}", "\u{1F4F1}", "\u{1F4AC}", "\u{1F4E7}", "\u{1F310}", "\u{1F4E2}", "\u{1F3AF}"];
  return (
    <div className="float-channel" key={`ch-${i}`}>
      {icons[i % icons.length]}
    </div>
  );
}

/* ──────────────────────────────────────────────
   Generate all floating elements once
   ────────────────────────────────────────────── */

function generateFloatingElements() {
  const elements = [];
  const makers = [
    makeEmailBanner,
    makePushNotif,
    makeSMS,
    makeSegmentBadge,
    makeKPICard,
    makeLiquidTag,
    makeChannelIcon,
  ];

  // We create ~50 elements spread across 5 "lanes" with different speeds
  const totalPerType = [6, 6, 7, 8, 7, 8, 8]; // 50 total
  let globalIdx = 0;

  makers.forEach((maker, typeIdx) => {
    const count = totalPerType[typeIdx];
    for (let i = 0; i < count; i++) {
      const lane = globalIdx % 5;
      const duration = 30 + lane * 12 + Math.random() * 15; // 30-70s
      const delay = -(Math.random() * duration); // negative delay so they start spread out
      const startX = Math.random() * 100; // random horizontal start
      const startY = Math.random() * 100; // random vertical start
      const opacity = 0.08 + Math.random() * 0.12; // 0.08-0.20
      const scale = 0.6 + Math.random() * 0.5; // 0.6-1.1

      elements.push(
        <div
          className={`floating-element floating-lane-${lane}`}
          key={`float-${globalIdx}`}
          style={{
            "--float-duration": `${duration}s`,
            "--float-delay": `${delay}s`,
            "--float-start-x": `${startX}vw`,
            "--float-start-y": `${startY}vh`,
            "--float-opacity": opacity,
            "--float-scale": scale,
          }}
        >
          {maker(i)}
        </div>
      );
      globalIdx++;
    }
  });

  return elements;
}

/* ──────────────────────────────────────────────
   LoginPage Component
   ────────────────────────────────────────────── */

export default function LoginPage() {
  const { login } = useAuth();
  const [password, setPassword] = useState("");
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  // Generate floating elements once with useMemo
  const floatingElements = useMemo(() => generateFloatingElements(), []);

  const handleSubmit = (e) => {
    e.preventDefault();
    setError(false);
    setLoading(true);

    // Simulate a short delay for UX
    setTimeout(() => {
      const ok = login(password);
      if (!ok) {
        setLoading(false);
        setError(true);
        // Remove shake after animation
        setTimeout(() => setError(false), 600);
      } else {
        setLoading(false);
        setSuccess(true);
      }
    }, 800);
  };

  return (
    <div className="login-page">
      {/* Animated background */}
      <div className="login-bg">
        <div className="login-bg__gradient" />
        <div className="login-bg__elements">{floatingElements}</div>
      </div>

      {/* Login card */}
      <div className={`login-card ${error ? "login-card--shake" : ""} ${success ? "login-card--success" : ""}`}>
        <div className="login-card__logo">
          <span className="login-card__logo-text">J-Braze Studio</span>
          <span className="login-card__logo-sub">by JAKALA</span>
        </div>

        <p className="login-card__subtitle">
          Plateforme unifiee Braze pour consultants JAKALA
        </p>

        <form onSubmit={handleSubmit} className="login-card__form">
          <div className="login-input-wrapper">
            <svg
              className="login-input-icon"
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
            <input
              type="password"
              className="login-input"
              placeholder="Mot de passe"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoFocus
              disabled={loading || success}
            />
          </div>

          {error && (
            <div className="login-error">Mot de passe incorrect</div>
          )}

          <button
            type="submit"
            className="login-btn"
            disabled={loading || success || !password.trim()}
          >
            {loading ? (
              <span className="login-spinner" />
            ) : (
              "Se connecter"
            )}
          </button>
        </form>

        <p className="login-card__footer">
          Acces reserve aux consultants JAKALA
        </p>
      </div>
    </div>
  );
}
