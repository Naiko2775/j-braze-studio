import { useState } from "react";
import PlatformConfig from "./PlatformConfig";
import DataPreview from "./DataPreview";
import MigrationRunner from "./MigrationRunner";
import WarmupMonitor from "./WarmupMonitor";

const STEPS = [
  { id: "config", label: "1. Configuration", icon: "\u2699" },
  { id: "preview", label: "2. Apercu", icon: "\uD83D\uDD0D" },
  { id: "migration", label: "3. Migration", icon: "\uD83D\uDE80" },
];

export default function MigrationPage() {
  // Workflow step
  const [currentStep, setCurrentStep] = useState("config");

  // State
  const [platform, setPlatform] = useState("demo");
  const [credentials, setCredentials] = useState({});
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [migrationJob, setMigrationJob] = useState(null);

  const isConnected = connectionStatus?.success === true || connectionStatus?.source === true;
  const hasPreview = previewData !== null;

  const canGoToPreview = isConnected;
  const canGoToMigration = isConnected && hasPreview;

  const goToStep = (step) => {
    if (step === "preview" && !canGoToPreview) return;
    if (step === "migration" && !canGoToMigration) return;
    setCurrentStep(step);
  };

  return (
    <div>
      {/* Page header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ color: "var(--color-navy)", fontSize: 24, fontWeight: 700 }}>
          Migration
        </h1>
        <p style={{ color: "var(--color-text-secondary)", marginTop: 4, fontSize: "0.9rem" }}>
          Migrez vos donnees depuis Brevo, SFMC ou CSV vers Braze
        </p>
      </div>

      {/* Step indicator */}
      <div style={{
        display: "flex",
        gap: 0,
        marginBottom: 24,
        background: "var(--color-surface)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        overflow: "hidden",
      }}>
        {STEPS.map((step, i) => {
          const isActive = currentStep === step.id;
          const isEnabled =
            step.id === "config" ||
            (step.id === "preview" && canGoToPreview) ||
            (step.id === "migration" && canGoToMigration);
          const isCompleted =
            (step.id === "config" && isConnected) ||
            (step.id === "preview" && hasPreview);

          return (
            <button
              key={step.id}
              type="button"
              onClick={() => goToStep(step.id)}
              disabled={!isEnabled}
              style={{
                flex: 1,
                padding: "14px 16px",
                background: isActive ? "var(--color-navy)" : "transparent",
                color: isActive ? "#fff" : isEnabled ? "var(--color-text)" : "var(--color-text-muted)",
                border: "none",
                borderRight: i < STEPS.length - 1 ? "1px solid var(--color-border)" : "none",
                cursor: isEnabled ? "pointer" : "not-allowed",
                fontFamily: "var(--font-family)",
                fontWeight: 600,
                fontSize: "0.875rem",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 8,
                transition: "all 0.15s",
                opacity: isEnabled ? 1 : 0.5,
              }}
            >
              {isCompleted && !isActive ? (
                <span style={{ color: "var(--color-success)", fontSize: "1rem" }}>{"\u2713"}</span>
              ) : (
                <span>{step.icon}</span>
              )}
              {step.label}
            </button>
          );
        })}
      </div>

      {/* Step content */}
      {currentStep === "config" && (
        <div>
          <PlatformConfig
            platform={platform}
            onPlatformChange={(p) => {
              setPlatform(p);
              setConnectionStatus(null);
              setPreviewData(null);
              setMigrationJob(null);
            }}
            credentials={credentials}
            onCredentialsChange={setCredentials}
            connectionStatus={connectionStatus}
            onConnectionStatusChange={setConnectionStatus}
          />

          {/* Next step hint */}
          {isConnected && (
            <div style={{ textAlign: "center", marginTop: 16 }}>
              <button
                className="btn btn-primary btn-lg"
                onClick={() => setCurrentStep("preview")}
              >
                Suivant : Apercu des donnees &rarr;
              </button>
            </div>
          )}
        </div>
      )}

      {currentStep === "preview" && (
        <div>
          <DataPreview
            platform={platform}
            credentials={credentials}
            onPreviewData={setPreviewData}
          />

          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 16 }}>
            <button
              className="btn btn-secondary"
              onClick={() => setCurrentStep("config")}
            >
              &larr; Configuration
            </button>
            {hasPreview && (
              <button
                className="btn btn-primary btn-lg"
                onClick={() => setCurrentStep("migration")}
              >
                Suivant : Migration &rarr;
              </button>
            )}
          </div>
        </div>
      )}

      {currentStep === "migration" && (
        <div>
          <MigrationRunner
            platform={platform}
            credentials={credentials}
            previewData={previewData}
            onMigrationJob={setMigrationJob}
          />

          {/* Warmup monitor */}
          {migrationJob && (
            <div style={{ marginTop: 16 }}>
              <WarmupMonitor warmupData={migrationJob.warmup} />
            </div>
          )}

          <div style={{ marginTop: 16 }}>
            <button
              className="btn btn-secondary"
              onClick={() => setCurrentStep("preview")}
            >
              &larr; Apercu
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
