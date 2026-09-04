import { useState } from "react";
import { API_BASE } from "../constants";

/**
 * Bouton qui declenche un telechargement de fichier depuis une URL API.
 * Props :
 *   - url       : chemin API relatif (ex: "/data-model/export/abc?format=excel")
 *   - filename  : nom du fichier telecharge
 *   - label     : texte du bouton
 *   - icon      : (optionnel) emoji/icone affichee avant le label
 *   - disabled  : (optionnel) desactiver le bouton
 */
export default function DownloadButton({
  url,
  filename,
  label = "Telecharger",
  icon = null,
  disabled = false,
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleDownload = async () => {
    if (loading || disabled) return;
    setLoading(true);
    setError(null);
    try {
      const fullUrl = `${API_BASE}${url}`;
      const response = await fetch(fullUrl);
      if (!response.ok) {
        const errBody = await response.json().catch(() => ({}));
        throw new Error(errBody.detail || `Erreur HTTP ${response.status}`);
      }
      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);
    } catch (err) {
      // Sans retour visuel, un export en echec donne un bouton qui ne fait rien.
      console.error("Erreur de telechargement:", err.message);
      setError(err.message || "Echec du telechargement");
    } finally {
      setLoading(false);
    }
  };

  return (
    <span style={{ display: "inline-flex", flexDirection: "column", alignItems: "stretch", gap: 6 }}>
      <button
        className="btn btn-secondary"
        onClick={handleDownload}
        disabled={disabled || loading}
        style={{ opacity: disabled ? 0.5 : 1, cursor: disabled ? "not-allowed" : "pointer" }}
      >
        {loading ? (
          <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span className="spinner spinner-sm" />
            Export...
          </span>
        ) : (
          <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
            {icon && <span>{icon}</span>}
            {label}
          </span>
        )}
      </button>
      {error && (
        <span
          role="alert"
          style={{
            background: "#FFF5F5",
            border: "1px solid #FED7D7",
            borderRadius: "var(--radius-md)",
            padding: "6px 10px",
            fontSize: "0.75rem",
            color: "#C53030",
            lineHeight: 1.4,
            maxWidth: 220,
          }}
        >
          {error}
        </span>
      )}
    </span>
  );
}
