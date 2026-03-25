import { useState } from "react";
import { useApi } from "../../shared/hooks/useApi";

const PLATFORMS = [
  { id: "demo", label: "Demo (donnees fictives)" },
  { id: "brevo", label: "Brevo (Sendinblue)" },
  { id: "sfmc", label: "Salesforce Marketing Cloud" },
  { id: "csv", label: "CSV / Fichier plat" },
];

const CREDENTIAL_FIELDS = {
  brevo: [
    { key: "api_key", label: "API Key Brevo", type: "password", placeholder: "xkeysib-..." },
  ],
  sfmc: [
    { key: "client_id", label: "Client ID", type: "text", placeholder: "Client ID SFMC" },
    { key: "client_secret", label: "Client Secret", type: "password", placeholder: "Client Secret" },
    { key: "subdomain", label: "Subdomain", type: "text", placeholder: "mc563885gzs27c5t9-63k636ttgm" },
  ],
  csv: [
    { key: "file", label: "Fichier CSV", type: "file", accept: ".csv,.tsv,.txt" },
  ],
  demo: [],
};

export default function PlatformConfig({ platform, onPlatformChange, credentials, onCredentialsChange, connectionStatus, onConnectionStatusChange }) {
  const { loading, error, call } = useApi();
  const [csvFileName, setCsvFileName] = useState("");

  const fields = CREDENTIAL_FIELDS[platform] || [];

  const handleCredentialChange = (key, value) => {
    onCredentialsChange({ ...credentials, [key]: value });
    // Reset connection status when credentials change
    if (connectionStatus !== null) {
      onConnectionStatusChange(null);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setCsvFileName(file.name);
      // Read file and store as base64 for API transport
      const reader = new FileReader();
      reader.onload = () => {
        handleCredentialChange("file_content", reader.result);
        handleCredentialChange("file_name", file.name);
      };
      reader.readAsDataURL(file);
    }
  };

  const hasCredentials = () => {
    if (platform === "demo") return true;
    if (platform === "csv") return !!credentials.file_content;
    const required = fields.filter((f) => f.type !== "file").map((f) => f.key);
    return required.every((k) => credentials[k]?.trim());
  };

  const handleTestConnection = async () => {
    try {
      const result = await call("/migration/test-connection", {
        method: "POST",
        body: JSON.stringify({
          platform,
          credentials: platform === "csv"
            ? { file_name: credentials.file_name, file_content: credentials.file_content }
            : credentials,
        }),
      });
      // Backend returns {source: bool, braze: bool}, transform for frontend
      const transformed = {
        success: result.source === true,
        source: result.source,
        braze: result.braze,
        message: result.source ? "Connexion source reussie" : "Echec connexion source",
      };
      onConnectionStatusChange(transformed);
    } catch {
      onConnectionStatusChange({ success: false, error: error || "Erreur de connexion" });
    }
  };

  return (
    <div className="card">
      <div className="card-body">
        <h2 style={{ color: "var(--color-navy)", fontSize: "1.15rem", fontWeight: 700, marginBottom: 4 }}>
          Configuration de la plateforme source
        </h2>
        <span className="text-sm text-muted">
          Selectionnez la plateforme et renseignez les identifiants pour commencer la migration
        </span>

        {/* Platform selector */}
        <div className="form-group" style={{ marginTop: 20 }}>
          <label className="label" htmlFor="mig-platform">Plateforme source</label>
          <select
            id="mig-platform"
            className="select"
            value={platform}
            onChange={(e) => {
              onPlatformChange(e.target.value);
              onCredentialsChange({});
              onConnectionStatusChange(null);
              setCsvFileName("");
            }}
          >
            {PLATFORMS.map((p) => (
              <option key={p.id} value={p.id}>{p.label}</option>
            ))}
          </select>
        </div>

        {/* Demo badge */}
        {platform === "demo" && (
          <div style={{
            background: "var(--color-red-light)",
            border: "1px solid rgba(240, 10, 10, 0.15)",
            borderRadius: "var(--radius-md)",
            padding: "12px 16px",
            marginBottom: 16,
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}>
            <span style={{ fontSize: "1.2rem" }}>&#9888;</span>
            <span className="text-sm" style={{ color: "var(--color-red)", fontWeight: 600 }}>
              Mode demonstration : donnees fictives, aucune connexion requise
            </span>
          </div>
        )}

        {/* Dynamic credential fields */}
        {fields.map((field) => (
          <div className="form-group" key={field.key}>
            <label className="label" htmlFor={`mig-${field.key}`}>{field.label}</label>
            {field.type === "file" ? (
              <div>
                <input
                  id={`mig-${field.key}`}
                  type="file"
                  accept={field.accept}
                  onChange={handleFileChange}
                  style={{
                    width: "100%",
                    background: "var(--color-surface)",
                    border: "2px dashed var(--color-border)",
                    borderRadius: "var(--radius-md)",
                    padding: "16px",
                    fontSize: "0.875rem",
                    fontFamily: "var(--font-family)",
                    cursor: "pointer",
                  }}
                />
                {csvFileName && (
                  <span className="text-xs text-muted" style={{ marginTop: 4, display: "block" }}>
                    Fichier selectionne : {csvFileName}
                  </span>
                )}
              </div>
            ) : (
              <input
                id={`mig-${field.key}`}
                className="input"
                type={field.type}
                placeholder={field.placeholder}
                value={credentials[field.key] || ""}
                onChange={(e) => handleCredentialChange(field.key, e.target.value)}
              />
            )}
          </div>
        ))}

        {/* Connection test */}
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 8 }}>
          <button
            className="btn btn-primary"
            onClick={handleTestConnection}
            disabled={loading || !hasCredentials()}
          >
            {loading ? (
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span className="spinner spinner-sm" />
                Test en cours...
              </span>
            ) : (
              "Tester la connexion"
            )}
          </button>

          {/* Status indicator */}
          {connectionStatus !== null && !loading && (
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  background: connectionStatus.success ? "var(--color-success)" : "var(--color-error)",
                  display: "inline-block",
                }}
              />
              <span
                className="text-sm font-semibold"
                style={{ color: connectionStatus.success ? "var(--color-success)" : "var(--color-error)" }}
              >
                {connectionStatus.success ? "Connexion reussie" : connectionStatus.error || "Echec de connexion"}
              </span>
            </div>
          )}
        </div>

        {/* API error */}
        {error && !connectionStatus && (
          <div style={{
            background: "#FFF5F5",
            border: "1px solid #FED7D7",
            borderRadius: "var(--radius-md)",
            padding: "10px 14px",
            marginTop: 12,
            fontSize: "0.82rem",
            color: "#C53030",
          }}>
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
