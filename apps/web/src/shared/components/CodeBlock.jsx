import { useState } from "react";

export default function CodeBlock({ code, language = "text", maxHeight = 400 }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div style={{ position: "relative" }}>
      <div
        style={{
          position: "absolute",
          top: 10,
          right: 10,
          display: "flex",
          alignItems: "center",
          gap: 8,
          zIndex: 1,
        }}
      >
        {language !== "text" && (
          <span
            style={{
              fontSize: 11,
              color: "var(--color-text-muted)",
              fontWeight: 600,
              textTransform: "uppercase",
            }}
          >
            {language}
          </span>
        )}
        <button
          onClick={handleCopy}
          style={{
            background: copied ? "var(--color-success)" : "rgba(0,0,0,0.06)",
            color: copied ? "#fff" : "var(--color-text-secondary)",
            padding: "5px 14px",
            borderRadius: "var(--radius-sm)",
            fontSize: 12,
            cursor: "pointer",
            fontWeight: 600,
            border: "1px solid rgba(0,0,0,0.1)",
            transition: "all 0.2s",
            fontFamily: "var(--font-family)",
          }}
        >
          {copied ? "Copie !" : "Copier"}
        </button>
      </div>
      <pre
        style={{
          background: "#1e1e2e",
          color: "#cdd6f4",
          padding: 20,
          borderRadius: "var(--radius-md)",
          overflow: "auto",
          fontSize: 13,
          lineHeight: 1.6,
          maxHeight,
          border: "1px solid rgba(255,255,255,0.06)",
          fontFamily: "var(--font-mono)",
        }}
      >
        {code}
      </pre>
    </div>
  );
}
