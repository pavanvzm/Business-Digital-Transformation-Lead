import type { DashboardMetrics } from "../types";

interface Props {
  metrics: DashboardMetrics;
}

interface MetricProps {
  label: string;
  value: string;
  color?: string;
  critical?: boolean;
}

function Metric({ label, value, color, critical }: MetricProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 2, padding: "4px 14px" }}>
      <span
        style={{
          fontSize: 16,
          fontWeight: 700,
          fontFamily: "'JetBrains Mono', 'Consolas', monospace",
          color: critical ? "var(--color-danger)" : color || "var(--text-primary)",
          animation: critical ? "timerWarning 1.5s ease-in-out infinite" : "none",
        }}
      >
        {value}
      </span>
      <span style={{ fontSize: 10, color: "var(--text-tertiary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
        {label}
      </span>
    </div>
  );
}

export default function StatusBar({ metrics }: Props) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "8px 20px",
        background: "var(--bg-secondary)",
        borderBottom: "1px solid var(--border-subtle)",
        flexShrink: 0,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "0.02em" }}>
          ⚙ HITL Dashboard
        </span>
        <span style={{ fontSize: 11, color: "var(--text-muted)", background: "var(--bg-card)", padding: "2px 8px", borderRadius: "var(--radius-sm)" }}>
          {metrics.totalTicketsToday} tickets today
        </span>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
        <Metric label="SLA Compliance" value={`${metrics.slaComplianceRate.toFixed(1)}%`} color="var(--color-success)" />
        <div style={{ width: 1, height: 28, background: "var(--border-subtle)" }} />
        <Metric label="P0 Pending" value={String(metrics.p0Pending)} critical={metrics.p0Pending > 0} />
        <Metric label="P1 Pending" value={String(metrics.p1Pending)} color={metrics.p1Pending > 0 ? "var(--color-p1)" : "var(--text-primary)"} />
        <Metric label="Pending Total" value={String(metrics.pendingCount)} />
        <div style={{ width: 1, height: 28, background: "var(--border-subtle)" }} />
        <Metric label="Override Rate" value={`${metrics.overrideRate.toFixed(1)}%`} color="var(--color-info)" />
        <Metric label="Avg P1 Resp" value={`${metrics.avgResponseTimeP1.toFixed(0)}m`} />
        <Metric label="Overdue" value={`${metrics.overdueTicketRatio.toFixed(1)}%`} critical={metrics.overdueTicketRatio > 5} />
      </div>
    </div>
  );
}
