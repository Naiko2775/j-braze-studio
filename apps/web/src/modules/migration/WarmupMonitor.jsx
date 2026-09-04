// Paliers affiches tant qu'aucun warmup n'a tourne
const DEFAULT_STAGE_PERCENTS = [1, 5, 10, 25, 50, 100];

const ERROR_THRESHOLD_WARNING = 2;
const ERROR_THRESHOLD_DANGER = 5;

function getStageColor(errorRate, isCompleted, isActive) {
  if (!isCompleted && !isActive) return "var(--color-text-muted)";
  if (errorRate >= ERROR_THRESHOLD_DANGER) return "var(--color-error)";
  if (errorRate >= ERROR_THRESHOLD_WARNING) return "var(--color-warning)";
  return "var(--color-success)";
}

function getStageIcon(errorRate, isCompleted, isActive) {
  if (!isCompleted && !isActive) return "\u25CB"; // empty circle
  if (isActive && !isCompleted) return "\u25CF"; // filled circle (in progress)
  if (errorRate >= ERROR_THRESHOLD_DANGER) return "\u2716"; // cross
  if (errorRate >= ERROR_THRESHOLD_WARNING) return "\u26A0"; // warning
  return "\u2714"; // checkmark
}

function toCount(value) {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

// Le backend (POST /migration/run, mode warmup) emet par palier :
// stage_index, stage_percent, contacts, success, failed, error_rate,
// duration_seconds et status (pending/running/completed/failed/skipped/stopped).
function readStage(raw, fallbackPercent) {
  const status = raw?.status || "pending";
  const total = toCount(raw?.contacts);
  const success = toCount(raw?.success);
  const errors = toCount(raw?.failed);
  const processed = success + errors;
  const isCompleted = status === "completed" || status === "failed" || status === "stopped" || status === "skipped";
  const isActive = status === "running";
  const percent = toCount(raw?.stage_percent) || fallbackPercent;

  return {
    pct: percent,
    label: `${percent}%`,
    status,
    total,
    success,
    errors,
    processed,
    duration: toCount(raw?.duration_seconds),
    errorRate: toCount(raw?.error_rate),
    isCompleted,
    isActive,
    progressPct: total > 0 ? Math.round((processed / total) * 100) : (isCompleted ? 100 : 0),
  };
}

export default function WarmupMonitor({ warmupData }) {
  const stages = Array.isArray(warmupData?.stages) ? warmupData.stages : [];
  const stopReason = warmupData?.stop_reason || null;
  const totalContacts = toCount(warmupData?.total_contacts);
  const totalSuccess = toCount(warmupData?.total_success);
  const totalFailed = toCount(warmupData?.total_failed);

  // Les paliers reellement executes priment sur la liste par defaut
  const displayStages = stages.length > 0
    ? stages.map((raw, i) => readStage(raw, DEFAULT_STAGE_PERCENTS[i] ?? 0))
    : DEFAULT_STAGE_PERCENTS.map((pct) => readStage(null, pct));

  // Overall progress
  const completedCount = displayStages.filter((s) => s.isCompleted).length;
  const overallPct = displayStages.length > 0
    ? Math.round((completedCount / displayStages.length) * 100)
    : 0;

  return (
    <div className="card">
      <div className="card-body">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div>
            <h2 style={{ color: "var(--color-navy)", fontSize: "1.15rem", fontWeight: 700, marginBottom: 4 }}>
              Monitoring Warmup
            </h2>
            <span className="text-sm text-muted">
              Progression par paliers : 1% &rarr; 5% &rarr; 10% &rarr; 25% &rarr; 50% &rarr; 100%
            </span>
          </div>
          <span className="badge badge-info">
            <span className="badge-dot" />
            {completedCount}/{displayStages.length} paliers
          </span>
        </div>

        {/* Resume global */}
        {stages.length > 0 && (
          <div className="text-sm" style={{ color: "var(--color-text-secondary)", marginBottom: 12 }}>
            {totalSuccess} contacts migres et {totalFailed} en erreur sur {totalContacts} au total
          </div>
        )}

        {/* Arret automatique ou manuel */}
        {stopReason && (
          <div style={{
            background: "rgba(245, 158, 11, 0.08)",
            border: "1px solid rgba(245, 158, 11, 0.3)",
            borderRadius: "var(--radius-md)",
            padding: "10px 14px",
            marginBottom: 16,
          }}>
            <span className="text-sm font-semibold" style={{ color: "#d97706" }}>
              Warmup interrompu : {stopReason}
            </span>
          </div>
        )}

        {/* Overall progress bar */}
        <div style={{ marginBottom: 20 }}>
          <div style={{
            background: "var(--color-border-light)",
            borderRadius: "var(--radius-full)",
            height: 6,
            overflow: "hidden",
          }}>
            <div style={{
              height: "100%",
              width: `${overallPct}%`,
              background: "var(--color-navy)",
              borderRadius: "var(--radius-full)",
              transition: "width 0.4s ease",
            }} />
          </div>
          <div className="text-xs text-muted" style={{ marginTop: 4, textAlign: "right" }}>
            Progression globale : {overallPct}%
          </div>
        </div>

        {/* Stage cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12 }}>
          {displayStages.map((stage, i) => {
            const color = getStageColor(stage.errorRate, stage.isCompleted, stage.isActive);
            const icon = getStageIcon(stage.errorRate, stage.isCompleted, stage.isActive);

            return (
              <div
                key={stage.pct}
                style={{
                  background: stage.isActive ? "rgba(4, 0, 102, 0.03)" : "var(--color-surface)",
                  border: `2px solid ${stage.isActive ? "var(--color-navy)" : stage.isCompleted ? color : "var(--color-border)"}`,
                  borderRadius: "var(--radius-md)",
                  padding: "14px 12px",
                  textAlign: "center",
                  transition: "all 0.2s",
                  opacity: !stage.isCompleted && !stage.isActive ? 0.5 : 1,
                }}
              >
                {/* Stage header */}
                <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 6, marginBottom: 8 }}>
                  <span style={{ color, fontSize: "1rem" }}>{icon}</span>
                  <span style={{ fontWeight: 700, fontSize: "1.2rem", color: "var(--color-navy)" }}>
                    {stage.label}
                  </span>
                </div>

                {/* Stage progress bar */}
                <div style={{
                  background: "var(--color-border-light)",
                  borderRadius: "var(--radius-full)",
                  height: 4,
                  overflow: "hidden",
                  marginBottom: 8,
                }}>
                  <div style={{
                    height: "100%",
                    width: `${stage.progressPct}%`,
                    background: color,
                    borderRadius: "var(--radius-full)",
                    transition: "width 0.3s ease",
                  }} />
                </div>

                {/* Error rate */}
                {(stage.isCompleted || stage.isActive) && (
                  <div className="text-xs" style={{ color, fontWeight: 600 }}>
                    Erreurs : {stage.errorRate.toFixed(1)}%
                  </div>
                )}

                {/* Counters */}
                {(stage.isCompleted || stage.isActive) && stage.total > 0 && (
                  <div className="text-xs text-muted" style={{ marginTop: 2 }}>
                    {stage.success}&#10003; {stage.errors}&#10007; / {stage.total}
                    {stage.duration > 0 && ` - ${stage.duration}s`}
                  </div>
                )}

                {/* Palier sans contact supplementaire */}
                {stage.status === "skipped" && (
                  <div className="text-xs text-muted" style={{ marginTop: 2 }}>
                    Deja couvert
                  </div>
                )}

                {/* Stage label */}
                <div className="text-xs text-muted" style={{ marginTop: 4, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  Palier {i + 1}
                </div>
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div style={{
          display: "flex",
          gap: 20,
          marginTop: 20,
          paddingTop: 14,
          borderTop: "1px solid var(--color-border-light)",
          justifyContent: "center",
        }}>
          <LegendItem color="var(--color-success)" label="OK (< 2% erreurs)" />
          <LegendItem color="var(--color-warning)" label={`Attention (${ERROR_THRESHOLD_WARNING}-${ERROR_THRESHOLD_DANGER}%)`} />
          <LegendItem color="var(--color-error)" label={`Seuil depasse (> ${ERROR_THRESHOLD_DANGER}%)`} />
        </div>

        {/* Empty state */}
        {stages.length === 0 && (
          <div style={{ textAlign: "center", padding: "32px 16px", color: "var(--color-text-muted)" }}>
            <div style={{ fontSize: "1.5rem", marginBottom: 8, opacity: 0.3 }}>&#9881;</div>
            <p className="text-sm">
              Lancez une migration en mode Warmup pour visualiser la progression par paliers
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function LegendItem({ color, label }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <span style={{
        width: 10,
        height: 10,
        borderRadius: "50%",
        background: color,
        display: "inline-block",
      }} />
      <span className="text-xs text-muted">{label}</span>
    </div>
  );
}
