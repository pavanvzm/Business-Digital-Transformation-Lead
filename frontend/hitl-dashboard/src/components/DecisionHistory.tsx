import type { AuditEntry, EscalationEntry } from "../types";
import { useState } from "react";

interface Props {
  auditLog: AuditEntry[];
  escalationHistory: EscalationEntry[];
  resolvedBy: string | null;
  resolvedAt: string | null;
  decision: string | null;
}

function formatTimestamp(ts: string) {
  const d = new Date(ts);
  return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function DecisionHistory({ auditLog, escalationHistory, resolvedBy, resolvedAt, decision }: Props) {
  const [filter, setFilter] = useState<string>("all");

  const filtered =
    filter === "all"
      ? auditLog
      : filter === "escalation"
      ? auditLog.filter((e) => e.detail.toLowerCase().includes("escalate"))
      : filter === "decision"
      ? auditLog.filter((e) => e.actor !== "system" && e.actor !== "agent-01" && e.actor !== "agent-02" && e.actor !== "agent-03" && e.actor !== "agent-06" && e.actor !== "agent-08" && e.actor !== "agent-09")
      : auditLog;

  return (
    <div
      style={{
        background: "var(--bg-card)",
        borderRadius: "var(--radius-lg)",
        border: "1px solid var(--border-subtle)",
        padding: 16,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)" }}>
          Decision History & Audit Trail
        </h3>
        <div style={{ display: "flex", gap: 6 }}>
          {[
            { id: "all", label: "All" },
            { id: "decision", label: "Decisions" },
            { id: "escalation", label: "Escalations" },
          ].map((f) => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              style={{
                padding: "3px 8px",
                borderRadius: "var(--radius-sm)",
                border: "none",
                background: filter === f.id ? "var(--bg-tertiary)" : "transparent",
                color: filter === f.id ? "var(--text-primary)" : "var(--text-tertiary)",
                cursor: "pointer",
                fontSize: 10,
                fontWeight: 600,
              }}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Resolution info */}
      {resolvedBy && resolvedAt && (
        <div
          style={{
            padding: "8px 10px",
            borderRadius: "var(--radius-sm)",
            background: "var(--bg-tertiary)",
            marginBottom: 10,
            fontSize: 11,
            color: "var(--text-secondary)",
          }}
        >
          <strong>Resolved</strong> by {resolvedBy} at {new Date(resolvedAt).toLocaleString()}
          {decision && <> — "{decision}"</>}
        </div>
      )}

      {/* Escalation history */}
      {escalationHistory.length > 0 && (
        <div
          style={{
            padding: "8px 10px",
            borderRadius: "var(--radius-sm)",
            background: "var(--color-warning)08",
            border: "1px solid var(--color-warning)20",
            marginBottom: 10,
            fontSize: 11,
            color: "var(--color-warning)",
          }}
        >
          <strong>Escalation Path:</strong>
          {escalationHistory.map((e, i) => (
            <div key={i} style={{ marginTop: 4 }}>
              {formatTimestamp(e.timestamp)} — {e.from} → {e.to}
              {e.reason && <span style={{ color: "var(--text-tertiary)" }}>: {e.reason}</span>}
            </div>
          ))}
        </div>
      )}

      {/* Audit log entries */}
      <div
        style={{
          maxHeight: 280,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 4,
        }}
      >
        {filtered.length === 0 && (
          <div style={{ padding: 20, textAlign: "center", color: "var(--text-muted)", fontSize: 12 }}>
            No entries match this filter.
          </div>
        )}
        {filtered.map((entry, i) => {
          const isHuman = entry.actor !== "system" && !entry.actor.startsWith("agent-");
          const isSystem = entry.actor === "system";
          const isSLA = entry.detail.toLowerCase().includes("sla") || entry.detail.toLowerCase().includes("timeout");

          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: 8,
                padding: "4px 8px",
                borderRadius: "var(--radius-sm)",
                background: isHuman ? "var(--color-info)08" : isSLA ? "var(--color-danger)08" : "transparent",
                animation: "slideIn 0.2s ease-out",
                animationDelay: `${i * 30}ms`,
              }}
            >
              <span
                style={{
                  fontSize: 10,
                  fontFamily: "'JetBrains Mono', 'Consolas', monospace",
                  color: "var(--text-muted)",
                  whiteSpace: "nowrap",
                  minWidth: 60,
                }}
              >
                {formatTimestamp(entry.timestamp)}
              </span>
              <span
                style={{
                  fontSize: 10,
                  fontWeight: 600,
                  color: isHuman
                    ? "var(--color-info)"
                    : isSystem
                    ? "var(--text-tertiary)"
                    : "var(--text-muted)",
                  minWidth: 80,
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {entry.actor}
              </span>
              <span
                style={{
                  fontSize: 11,
                  color: isHuman ? "var(--text-primary)" : isSLA ? "var(--color-danger)" : "var(--text-tertiary)",
                  lineHeight: 1.3,
                }}
              >
                {entry.detail}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
