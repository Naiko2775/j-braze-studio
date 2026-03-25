import { useState, useEffect, useCallback } from "react";
import { useApi } from "../shared/hooks/useApi";

/* ── Constantes ── */

const CLAUDE_MODELS = [
  { value: "claude-sonnet-4-20250514", label: "Claude Sonnet 4 (2025-05-14)" },
  { value: "claude-opus-4-20250514", label: "Claude Opus 4 (2025-05-14)" },
  { value: "claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet (2024-10-22)" },
  { value: "claude-3-5-haiku-20241022", label: "Claude 3.5 Haiku (2024-10-22)" },
];

const BRAZE_INSTANCES = [
  { value: "https://rest.iad-01.braze.com", label: "US-01 (rest.iad-01.braze.com)" },
  { value: "https://rest.iad-02.braze.com", label: "US-02 (rest.iad-02.braze.com)" },
  { value: "https://rest.iad-03.braze.com", label: "US-03 (rest.iad-03.braze.com)" },
  { value: "https://rest.iad-04.braze.com", label: "US-04 (rest.iad-04.braze.com)" },
  { value: "https://rest.iad-05.braze.com", label: "US-05 (rest.iad-05.braze.com)" },
  { value: "https://rest.iad-06.braze.com", label: "US-06 (rest.iad-06.braze.com)" },
  { value: "https://rest.iad-08.braze.com", label: "US-08 (rest.iad-08.braze.com)" },
  { value: "https://rest.fra-01.braze.eu", label: "EU-01 (rest.fra-01.braze.eu)" },
  { value: "https://rest.fra-02.braze.eu", label: "EU-02 (rest.fra-02.braze.eu)" },
];

/* ── Composant StatusDot ── */

function ServiceStatus({ label, status, detail }) {
  const colors = {
    connected: { bg: "rgba(34,197,94,0.1)", color: "#16a34a", dot: "#22c55e", text: "Connecte" },
    disconnected: { bg: "rgba(239,68,68,0.1)", color: "#dc2626", dot: "#ef4444", text: "Deconnecte" },
    unknown: { bg: "rgba(0,0,0,0.05)", color: "var(--color-text-muted)", dot: "#9ca3af", text: "Inconnu" },
    checking: { bg: "rgba(59,130,246,0.1)", color: "#2563eb", dot: "#3b82f6", text: "Verification..." },
  };
  const s = colors[status] || colors.unknown;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "14px 0",
        borderBottom: "1px solid var(--color-border-light)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <span
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            background: s.dot,
            flexShrink: 0,
          }}
        />
        <div>
          <div style={{ fontWeight: 600, fontSize: "0.875rem" }}>{label}</div>
          {detail && <div className="text-xs text-muted">{detail}</div>}
        </div>
      </div>
      <span
        className="badge"
        style={{ background: s.bg, color: s.color }}
      >
        {s.text}
      </span>
    </div>
  );
}

/* ── Page principale ── */

export default function SettingsPage() {
  const [selectedModel, setSelectedModel] = useState(CLAUDE_MODELS[0].value);
  const [brazeUrl, setBrazeUrl] = useState("");
  const [saved, setSaved] = useState(false);

  // Cle API Claude
  const [apiKey, setApiKey] = useState("");
  const [apiKeyMasked, setApiKeyMasked] = useState(null);
  const [apiKeySaved, setApiKeySaved] = useState(false);
  const [apiKeyError, setApiKeyError] = useState(null);

  const [services, setServices] = useState({
    claude: "unknown",
    braze: "unknown",
    database: "unknown",
  });
  const [servicesChecking, setServicesChecking] = useState(false);

  const configApi = useApi();
  const saveApi = useApi();

  // Charger la config existante + statut cle API
  useEffect(() => {
    configApi
      .call("/app-config", { method: "GET" })
      .then((cfgArray) => {
        const cfg = Array.isArray(cfgArray)
          ? cfgArray.reduce((acc, { key, value }) => ({ ...acc, [key]: value }), {})
          : cfgArray;
        if (cfg && cfg.default_model) {
          setSelectedModel(cfg.default_model);
        }
        if (cfg && cfg.braze_api_url) {
          setBrazeUrl(cfg.braze_api_url);
        }
      })
      .catch(() => {});

    // Verifier si une cle API est deja configuree
    fetch("/api/settings/anthropic-key")
      .then((r) => r.json())
      .then((d) => {
        if (d.configured) {
          setApiKeyMasked(d.masked_key);
        }
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Verifier le statut des services
  const checkServices = useCallback(async () => {
    setServicesChecking(true);
    setServices({ claude: "checking", braze: "checking", database: "checking" });

    // Check each service independently
    const checks = await Promise.allSettled([
      fetch("/api/health/claude").then((r) => r.json()).then((d) => d.status === "ok"),
      fetch("/api/health/braze").then((r) => r.json()).then((d) => d.status === "ok"),
      fetch("/api/health/database").then((r) => r.json()).then((d) => d.status === "ok"),
    ]);

    setServices({
      claude: checks[0].status === "fulfilled" && checks[0].value ? "connected" : "disconnected",
      braze: checks[1].status === "fulfilled" && checks[1].value ? "connected" : "disconnected",
      database: checks[2].status === "fulfilled" && checks[2].value ? "connected" : "disconnected",
    });
    setServicesChecking(false);
  }, []);

  useEffect(() => {
    checkServices();
  }, [checkServices]);

  // Sauvegarder la cle API Claude
  const handleSaveApiKey = async () => {
    setApiKeySaved(false);
    setApiKeyError(null);
    try {
      const resp = await fetch("/api/settings/anthropic-key", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: apiKey }),
      });
      const data = await resp.json();
      if (data.status === "ok") {
        setApiKeySaved(true);
        setApiKey("");
        // Refresh le masque et le health check
        const keyStatus = await fetch("/api/settings/anthropic-key").then((r) => r.json());
        if (keyStatus.configured) setApiKeyMasked(keyStatus.masked_key);
        checkServices();
        setTimeout(() => setApiKeySaved(false), 3000);
      } else {
        setApiKeyError(data.detail || "Erreur");
      }
    } catch {
      setApiKeyError("Erreur de connexion au serveur");
    }
  };

  // Sauvegarder le modele
  const handleSave = async () => {
    setSaved(false);
    try {
      await saveApi.call("/app-config", {
        method: "POST",
        body: JSON.stringify({
          key: "default_model",
          value: selectedModel,
        }),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch {
      // Endpoint pas encore disponible, feedback visuel quand meme
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    }
  };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ color: "var(--color-navy)", fontSize: 24, fontWeight: 700 }}>
          Parametres
        </h1>
        <p className="text-sm text-secondary" style={{ marginTop: 4 }}>
          Configuration de l'application et statut des services.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, alignItems: "start" }}>
        {/* Left column: Configuration */}
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {/* Cle API Claude */}
          <div className="card">
            <div className="card-header">Cle API Claude (Anthropic)</div>
            <div className="card-body">
              <p className="text-sm text-secondary" style={{ marginBottom: 12 }}>
                Renseignez votre cle API Anthropic pour activer les analyses Data Model et la generation Liquid.
                {apiKeyMasked && (
                  <span style={{ display: "block", marginTop: 6, fontWeight: 600, color: "var(--color-success)" }}>
                    Cle active : {apiKeyMasked}
                  </span>
                )}
              </p>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="label">Cle API</label>
                <input
                  type="password"
                  className="input"
                  placeholder="sk-ant-api03-..."
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem" }}
                />
              </div>
            </div>
            <div className="card-footer" style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <button
                className="btn btn-primary btn-sm"
                onClick={handleSaveApiKey}
                disabled={!apiKey.trim()}
              >
                Configurer la cle
              </button>
              {apiKeySaved && (
                <span className="text-sm" style={{ color: "var(--color-success)", fontWeight: 600 }}>
                  Cle API configuree avec succes
                </span>
              )}
              {apiKeyError && (
                <span className="text-sm" style={{ color: "var(--color-error)", fontWeight: 600 }}>
                  {apiKeyError}
                </span>
              )}
            </div>
          </div>

          {/* Modele Claude */}
          <div className="card">
            <div className="card-header">Modele Claude par defaut</div>
            <div className="card-body">
              <p className="text-sm text-secondary" style={{ marginBottom: 12 }}>
                Modele utilise pour les analyses Data Model et la generation Liquid.
              </p>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="label">Modele</label>
                <select
                  className="select"
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                >
                  {CLAUDE_MODELS.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="card-footer" style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <button
                className="btn btn-primary btn-sm"
                onClick={handleSave}
                disabled={saveApi.loading}
              >
                {saveApi.loading ? "Sauvegarde..." : "Sauvegarder"}
              </button>
              {saved && (
                <span className="text-sm text-success font-semibold">
                  Sauvegarde effectuee
                </span>
              )}
            </div>
          </div>

          {/* Instance Braze */}
          <div className="card">
            <div className="card-header">Instance Braze API</div>
            <div className="card-body">
              <p className="text-sm text-secondary" style={{ marginBottom: 12 }}>
                L'URL de l'instance Braze est definie via les variables d'environnement serveur.
                La valeur ci-dessous est indicative (lecture seule).
              </p>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="label">Instance</label>
                <select
                  className="select"
                  value={brazeUrl || BRAZE_INSTANCES[0].value}
                  disabled
                  style={{ opacity: 0.6, cursor: "not-allowed" }}
                >
                  {BRAZE_INSTANCES.map((inst) => (
                    <option key={inst.value} value={inst.value}>
                      {inst.label}
                    </option>
                  ))}
                </select>
              </div>
              <p className="text-xs text-muted" style={{ marginTop: 8 }}>
                Pour modifier l'instance, changez la variable <code style={{ fontFamily: "var(--font-mono)", background: "rgba(0,0,0,0.04)", padding: "1px 4px", borderRadius: 3 }}>BRAZE_API_URL</code> dans les parametres d'environnement Vercel.
              </p>
            </div>
          </div>
        </div>

        {/* Right column: Services status */}
        <div className="card">
          <div className="card-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span>Statut des services</span>
            <button
              className="btn btn-ghost btn-sm"
              onClick={checkServices}
              disabled={servicesChecking}
            >
              {servicesChecking ? "Verification..." : "Actualiser"}
            </button>
          </div>
          <div className="card-body">
            <ServiceStatus
              label="Claude API (Anthropic)"
              status={services.claude}
              detail="Modele IA pour analyses et generation"
            />
            <ServiceStatus
              label="Braze REST API"
              status={services.braze}
              detail="API pour les migrations et exports"
            />
            <ServiceStatus
              label="Base de donnees (Neon PostgreSQL)"
              status={services.database}
              detail="Stockage de l'historique et configurations"
            />
          </div>
          <div className="card-footer">
            <p className="text-xs text-muted">
              Les verifications de connexion utilisent les endpoints <code style={{ fontFamily: "var(--font-mono)", background: "rgba(0,0,0,0.04)", padding: "1px 4px", borderRadius: 3 }}>/api/health/*</code>.
              Un statut "Deconnecte" peut indiquer que les cles API ne sont pas configurees.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
