import { useState, useEffect, useRef, useCallback } from "react";
import { useApi } from "../../shared/hooks/useApi";
import { API_BASE } from "../../shared/constants";
import { useProject } from "../../shared/context/ProjectContext";

const MODES = [
  { id: "dry_run", label: "Dry Run", desc: "Simulation sans ecriture vers Braze", color: "var(--color-info)" },
  { id: "warmup", label: "Warmup", desc: "Migration progressive par paliers", color: "var(--color-warning)" },
  { id: "full", label: "Full", desc: "Migration complete de tous les contacts", color: "var(--color-red)" },
];

function formatDuration(seconds) {
  if (!seconds || seconds < 0) return "0s";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

export default function MigrationRunner({ platform, credentials, previewData, onMigrationJob }) {
  const [mode, setMode] = useState("dry_run");
  const [job, setJob] = useState(null);
  const [status, setStatus] = useState(null);
  const [stopping, setStopping] = useState(false);
  const pollingRef = useRef(null);
  const { loading: launching, error: launchError, call: launchCall } = useApi();
  const { currentProject } = useProject();

  const isRunning = status?.status === "running" || status?.status === "pending";
  const isFinished = status?.status === "completed" || status?.status === "failed" || status?.status === "stopped";

  // Polling for job status
  const startPolling = useCallback((jobId) => {
    // Clear any existing polling
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }
    pollingRef.current = setInterval(async () => {
      try {
        const url = `${API_BASE}/migration/status/${jobId}`;
        const res = await fetch(url, { headers: { "Content-Type": "application/json" } });
        if (res.ok) {
          const data = await res.json();
          setStatus(data);
          if (data.status === "completed" || data.status === "failed" || data.status === "stopped") {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
        }
      } catch {
        // Silently retry on next interval
      }
    }, 2000);
  }, []);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, []);

  const handleLaunch = async () => {
    try {
      const payload = {
        platform,
        credentials,
        mode,
        deduplicate_by_email: previewData?.deduplicate_by_email || false,
        project_id: currentProject?.id || undefined,
        project_name: currentProject?.name || undefined,
      };
      const result = await launchCall("/migration/run", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setJob(result);
      // The POST /run endpoint is synchronous: if it returns a status and result,
      // use them directly instead of relying on polling
      if (result.status === "completed" || result.status === "failed") {
        const contacts = result.result?.contacts || result.result?.total_contacts || 0;
        const success = result.result?.success || result.result?.total_success || 0;
        const failed = result.result?.failed || result.result?.total_failed || 0;
        setStatus({
          status: result.status,
          progress: {
            total: contacts,
            processed: contacts,
            success: success,
            errors: failed,
            elapsed_seconds: result.result?.elapsed_seconds || 0,
          },
          result: result.result,
        });
      } else {
        setStatus({ status: "pending", progress: {} });
      }
      setStopping(false);
      if (onMigrationJob) onMigrationJob(result);
      // Only poll if the job is not already finished
      if (result.job_id && result.status !== "completed" && result.status !== "failed") {
        startPolling(result.job_id);
      }
    } catch {
      // handled by useApi
    }
  };

  const handleStop = async () => {
    if (!job?.job_id) return;
    setStopping(true);
    try {
      await fetch(`${API_BASE}/migration/${job.job_id}/stop`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
    } catch {
      // Best effort
    }
  };

  const handleReset = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    setJob(null);
    setStatus(null);
    setStopping(false);
  };

  // When status is completed/failed, read counters from result (sync execution)
  // otherwise fall back to progress (async/polling)
  const progress = status?.progress || {};
  const resultData = status?.result || {};
  const isTerminal = status?.status === "completed" || status?.status === "failed" || status?.status === "stopped";
  const total = progress.total || (isTerminal ? (resultData.contacts || resultData.total_contacts || 0) : 0);
  const processed = progress.processed || (isTerminal ? total : 0);
  const successCount = progress.success || (isTerminal ? (resultData.success || resultData.total_success || 0) : 0);
  const errorCount = progress.errors || (isTerminal ? (resultData.failed || resultData.total_failed || 0) : 0);
  const progressPct = total > 0 ? Math.round((processed / total) * 100) : (isTerminal ? 100 : 0);
  const elapsed = progress.elapsed_seconds || resultData.elapsed_seconds || 0;

  return (
    <div className="card">
      <div className="card-body">
        <h2 style={{ color: "var(--color-navy)", fontSize: "1.15rem", fontWeight: 700, marginBottom: 4 }}>
          Lancer la migration
        </h2>
        <span className="text-sm text-muted">
          Choisissez le mode d'execution et lancez la migration vers Braze
        </span>

        {/* Mode selector */}
        {!job && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, margin: "20px 0" }}>
            {MODES.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => setMode(m.id)}
                style={{
                  background: mode === m.id ? "var(--color-surface)" : "transparent",
                  border: `2px solid ${mode === m.id ? m.color : "var(--color-border)"}`,
                  borderRadius: "var(--radius-md)",
                  padding: "16px",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "all 0.15s",
                  fontFamily: "var(--font-family)",
                  boxShadow: mode === m.id ? "var(--shadow-sm)" : "none",
                }}
              >
                <div style={{ fontWeight: 700, fontSize: "0.95rem", color: mode === m.id ? m.color : "var(--color-text)", marginBottom: 4 }}>
                  {m.label}
                </div>
                <div className="text-xs text-muted">{m.desc}</div>
              </button>
            ))}
          </div>
        )}

        {/* Full mode warning */}
        {mode === "full" && !job && (
          <div style={{
            background: "rgba(239, 68, 68, 0.06)",
            border: "1px solid rgba(239, 68, 68, 0.2)",
            borderRadius: "var(--radius-md)",
            padding: "12px 16px",
            marginBottom: 16,
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}>
            <span style={{ fontSize: "1.2rem" }}>&#9888;</span>
            <span className="text-sm" style={{ color: "var(--color-error)", fontWeight: 600 }}>
              Mode PRODUCTION : les donnees seront ecrites dans Braze. Cette action est irreversible.
            </span>
          </div>
        )}

        {/* Launch button */}
        {!job && (
          <button
            className="btn btn-danger btn-lg w-full"
            onClick={handleLaunch}
            disabled={launching}
          >
            {launching ? (
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span className="spinner spinner-sm" />
                Lancement...
              </span>
            ) : (
              `Lancer la migration (${MODES.find((m) => m.id === mode)?.label})`
            )}
          </button>
        )}

        {launchError && !job && (
          <div style={{
            background: "#FFF5F5",
            border: "1px solid #FED7D7",
            borderRadius: "var(--radius-md)",
            padding: "10px 14px",
            marginTop: 12,
            fontSize: "0.82rem",
            color: "#C53030",
          }}>
            {launchError}
          </div>
        )}

        {/* Progress section */}
        {job && status && (
          <div style={{ marginTop: 20 }}>
            {/* Status badge */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <StatusBadge status={status.status} />
                <span className="text-xs text-muted font-mono">
                  Job: {job.job_id?.slice(0, 8)}...
                </span>
              </div>
              <span className="text-sm text-muted">
                {formatDuration(elapsed)}
              </span>
            </div>

            {/* Progress bar */}
            <div style={{
              background: "var(--color-border-light)",
              borderRadius: "var(--radius-full)",
              height: 10,
              overflow: "hidden",
              marginBottom: 16,
            }}>
              <div
                style={{
                  height: "100%",
                  width: `${progressPct}%`,
                  background: isFinished && status.status === "failed"
                    ? "var(--color-error)"
                    : isFinished && status.status === "stopped"
                      ? "var(--color-warning)"
                      : "var(--color-red)",
                  borderRadius: "var(--radius-full)",
                  transition: "width 0.4s ease",
                }}
              />
            </div>

            <div className="text-sm font-semibold" style={{ textAlign: "center", marginBottom: 16, color: "var(--color-text-secondary)" }}>
              {processed} / {total} contacts ({progressPct}%)
            </div>

            {/* Real-time counters */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 20 }}>
              <CounterCard label="Traites" value={processed} color="var(--color-navy)" />
              <CounterCard label="Succes" value={successCount} color="var(--color-success)" />
              <CounterCard label="Erreurs" value={errorCount} color={errorCount > 0 ? "var(--color-error)" : "var(--color-text-muted)"} />
            </div>

            {/* Action buttons */}
            <div style={{ display: "flex", gap: 12 }}>
              {isRunning && (
                <button
                  className="btn btn-secondary"
                  onClick={handleStop}
                  disabled={stopping}
                  style={{ flex: 1 }}
                >
                  {stopping ? "Arret en cours..." : "Arreter la migration"}
                </button>
              )}
              {isFinished && (
                <button
                  className="btn btn-primary"
                  onClick={handleReset}
                  style={{ flex: 1 }}
                >
                  Nouvelle migration
                </button>
              )}
            </div>

            {/* Final result message */}
            {isFinished && (
              <div style={{
                marginTop: 16,
                padding: "14px 18px",
                borderRadius: "var(--radius-md)",
                background: status.status === "completed" ? "rgba(34, 197, 94, 0.06)" : status.status === "stopped" ? "rgba(245, 158, 11, 0.06)" : "rgba(239, 68, 68, 0.06)",
                border: `1px solid ${status.status === "completed" ? "rgba(34, 197, 94, 0.2)" : status.status === "stopped" ? "rgba(245, 158, 11, 0.2)" : "rgba(239, 68, 68, 0.2)"}`,
              }}>
                <div className="font-semibold text-sm" style={{
                  color: status.status === "completed" ? "var(--color-success)" : status.status === "stopped" ? "#d97706" : "var(--color-error)",
                }}>
                  {status.status === "completed" && "Migration terminee avec succes"}
                  {status.status === "stopped" && "Migration arretee par l'utilisateur"}
                  {status.status === "failed" && "Migration echouee"}
                </div>
                <div className="text-xs text-muted" style={{ marginTop: 4 }}>
                  {successCount} contacts migres, {errorCount} erreurs en {formatDuration(elapsed)}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const config = {
    pending: { label: "En attente", cls: "badge-info" },
    running: { label: "En cours", cls: "badge-warning" },
    completed: { label: "Termine", cls: "badge-success" },
    failed: { label: "Echoue", cls: "badge-error" },
    stopped: { label: "Arrete", cls: "badge-warning" },
  };
  const c = config[status] || config.pending;
  return (
    <span className={`badge ${c.cls}`}>
      <span className="badge-dot" />
      {c.label}
    </span>
  );
}

function CounterCard({ label, value, color }) {
  return (
    <div style={{
      background: "var(--color-bg)",
      border: "1px solid var(--color-border)",
      borderRadius: "var(--radius-md)",
      padding: "12px 14px",
      textAlign: "center",
    }}>
      <div style={{ fontSize: "1.4rem", fontWeight: 700, color }}>{value}</div>
      <div className="text-xs text-muted" style={{ marginTop: 2, fontWeight: 600 }}>{label}</div>
    </div>
  );
}
