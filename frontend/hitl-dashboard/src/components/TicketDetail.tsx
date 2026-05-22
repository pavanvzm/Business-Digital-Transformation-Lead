import type { HITLTicket } from "../types";
import PriorityBadge from "./PriorityBadge";
import SLATimer from "./SLATimer";
import ApprovalPanel from "./ApprovalPanel";
import DecisionHistory from "./DecisionHistory";

interface Props {
  ticket: HITLTicket;
  onDecision: (ticketId: string, action: string, reason: string, overrideParams?: Record<string, unknown>) => void;
  onClose: () => void;
}

const agentLabels: Record<string, string> = {
  "agent-01": "Agent-01 — Procurement",
  "agent-02": "Agent-02 — Production & MES",
  "agent-03": "Agent-03 — Inventory",
  "agent-04": "Agent-04 — Sales & Pricing",
  "agent-05": "Agent-05 — Market Intelligence",
  "agent-06": "Agent-06 — Predictive Analytics",
  "agent-07": "Agent-07 — Financial Accounting",
  "agent-08": "Agent-08 — Compliance & Risk",
  "agent-09": "Agent-09 — Orchestrator",
};

const statusLabels: Record<string, { label: string; color: string }> = {
  created: { label: "Created", color: "var(--color-neutral)" },
  notified: { label: "Notified", color: "var(--color-info)" },
  review: { label: "In Review", color: "var(--color-warning)" },
  approved: { label: "Approved ✓", color: "var(--color-success)" },
  rejected: { label: "Rejected ✗", color: "var(--color-danger)" },
  override: { label: "Override", color: "var(--color-info)" },
  escalated: { label: "Escalated ↑", color: "var(--color-warning)" },
  timeout: { label: "Timed Out ⚠", color: "var(--color-danger)" },
  cancelled: { label: "Cancelled", color: "var(--text-muted)" },
  closed: { label: "Closed", color: "var(--text-muted)" },
};

export default function TicketDetail({ ticket, onDecision, onClose }: Props) {
  const isPending =
    ticket.status === "created" || ticket.status === "notified" || ticket.status === "review";
  const statusCfg = statusLabels[ticket.status] || { label: ticket.status, color: "var(--text-muted)" };

  const handleDecision = (action: string, reason: string, overrideParams?: Record<string, unknown>) => {
    onDecision(ticket.ticket_id, action, reason, overrideParams);
  };

  return (
    <div
      style={{
        flex: 1,
        overflowY: "auto",
        padding: "16px 24px",
        background: "var(--bg-primary)",
      }}
    >
      {/* ── Header ── */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: 16,
          animation: "slideIn 0.2s ease-out",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
            <PriorityBadge priority={ticket.priority} />
            <span
              style={{
                fontSize: 11,
                fontFamily: "'JetBrains Mono', monospace",
                color: "var(--text-muted)",
              }}
            >
              {ticket.ticket_id}
            </span>
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                padding: "2px 8px",
                borderRadius: "var(--radius-sm)",
                background: `${statusCfg.color}15`,
                color: statusCfg.color,
              }}
            >
              {statusCfg.label}
            </span>
            <span style={{ fontSize: 10, color: "var(--text-tertiary)" }}>
              {ticket.scenarioId} · {agentLabels[ticket.sourceAgent] || ticket.sourceAgent}
            </span>
          </div>
          <h2
            style={{
              fontSize: 18,
              fontWeight: 700,
              color: "var(--text-primary)",
              lineHeight: 1.3,
            }}
          >
            {ticket.title}
          </h2>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {isPending && (
            <SLATimer
              deadline={ticket.sla.sla_deadline}
              created={ticket.createdAt}
              slaMinutes={ticket.sla.sla_minutes}
              priority={ticket.priority}
            />
          )}
          <button
            onClick={onClose}
            style={{
              padding: "4px 10px",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border-subtle)",
              background: "transparent",
              color: "var(--text-tertiary)",
              cursor: "pointer",
              fontSize: 16,
              lineHeight: 1,
            }}
            title="Close detail"
          >
            ✕
          </button>
        </div>
      </div>

      <div style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
        {/* ── Main Content ── */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Trigger & Description */}
          <div
            style={{
              background: "var(--bg-card)",
              borderRadius: "var(--radius-lg)",
              border: "1px solid var(--border-subtle)",
              padding: 16,
            }}
          >
            <div
              style={{
                padding: "6px 10px",
                borderRadius: "var(--radius-sm)",
                background: "var(--bg-tertiary)",
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 12,
                color: "var(--color-p1)",
                marginBottom: 10,
              }}
            >
              ⚡ TRIGGER: {ticket.triggerValue}
            </div>
            <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5 }}>
              {ticket.description}
            </p>
          </div>

          {/* Business Impact */}
          {ticket.businessImpact && (
            <div
              style={{
                background: "var(--bg-card)",
                borderRadius: "var(--radius-lg)",
                border: "1px solid var(--border-subtle)",
                padding: 16,
              }}
            >
              <h3 style={{ fontSize: 12, fontWeight: 600, color: "var(--text-tertiary)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 10 }}>
                Business Impact
              </h3>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                {ticket.businessImpact.costIncrease && (
                  <div>
                    <span style={{ fontSize: 10, color: "var(--text-muted)" }}>Cost Impact</span>
                    <div style={{ fontSize: 14, fontWeight: 700, color: "var(--color-danger)" }}>{ticket.businessImpact.costIncrease}</div>
                  </div>
                )}
                {ticket.businessImpact.marginImpact && (
                  <div>
                    <span style={{ fontSize: 10, color: "var(--text-muted)" }}>Margin Impact</span>
                    <div style={{ fontSize: 14, fontWeight: 700, color: "var(--color-p1)" }}>{ticket.businessImpact.marginImpact}</div>
                  </div>
                )}
                {ticket.businessImpact.affectedLines && (
                  <div>
                    <span style={{ fontSize: 10, color: "var(--text-muted)" }}>Affected</span>
                    <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>{ticket.businessImpact.affectedLines}</div>
                  </div>
                )}
                {ticket.businessImpact.cashFlow && (
                  <div>
                    <span style={{ fontSize: 10, color: "var(--text-muted)" }}>Cash Flow</span>
                    <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>{ticket.businessImpact.cashFlow}</div>
                  </div>
                )}
                {ticket.businessImpact.inventoryCover && (
                  <div>
                    <span style={{ fontSize: 10, color: "var(--text-muted)" }}>Inventory Cover</span>
                    <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>{ticket.businessImpact.inventoryCover}</div>
                  </div>
                )}
                {ticket.businessImpact.description && !ticket.businessImpact.costIncrease && !ticket.businessImpact.marginImpact && (
                  <div style={{ gridColumn: "1 / -1" }}>
                    <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>{ticket.businessImpact.description}</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Agent Recommendations */}
          {ticket.recommendations.length > 0 && (
            <div
              style={{
                background: "var(--bg-card)",
                borderRadius: "var(--radius-lg)",
                border: "1px solid var(--border-subtle)",
                padding: 16,
              }}
            >
              <h3 style={{ fontSize: 12, fontWeight: 600, color: "var(--text-tertiary)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 10 }}>
                Agent Recommendations
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {ticket.recommendations.map((rec, i) => (
                  <div
                    key={i}
                    style={{
                      padding: "10px 12px",
                      borderRadius: "var(--radius-md)",
                      background: i === 0 ? "rgba(59, 130, 246, 0.06)" : "var(--bg-tertiary)",
                      border: i === 0 ? "1px solid rgba(59, 130, 246, 0.2)" : "1px solid transparent",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                      <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
                        {i === 0 && "★ "}{rec.label}
                      </span>
                      <span
                        style={{
                          fontSize: 11,
                          fontWeight: 600,
                          padding: "1px 6px",
                          borderRadius: "var(--radius-sm)",
                          background: rec.confidence >= 0.85 ? "var(--color-success)15" : "var(--color-warning)15",
                          color: rec.confidence >= 0.85 ? "var(--color-success)" : "var(--color-warning)",
                        }}
                      >
                        {Math.round(rec.confidence * 100)}% confidence
                      </span>
                    </div>
                    <p style={{ fontSize: 12, color: "var(--text-tertiary)", marginBottom: 4 }}>{rec.description}</p>
                    <p style={{ fontSize: 11, color: "var(--text-secondary)", fontStyle: "italic" }}>
                      Impact: {rec.impact}
                    </p>
                    {rec.dataSources.length > 0 && (
                      <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 4 }}>
                        Data: {rec.dataSources.join(" · ")}
                        {rec.modelVersion && <> · Model: {rec.modelVersion}</>}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Alternatives */}
          {ticket.alternatives.length > 0 && (
            <div
              style={{
                background: "var(--bg-card)",
                borderRadius: "var(--radius-lg)",
                border: "1px solid var(--border-subtle)",
                padding: 16,
              }}
            >
              <h3 style={{ fontSize: 12, fontWeight: 600, color: "var(--text-tertiary)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 10 }}>
                Alternatives Considered
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {ticket.alternatives.map((alt, i) => (
                  <div
                    key={i}
                    style={{
                      padding: "6px 10px",
                      borderRadius: "var(--radius-sm)",
                      background: "var(--bg-tertiary)",
                      fontSize: 12,
                      color: "var(--text-secondary)",
                    }}
                  >
                    {alt}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Data Sources & Model Info */}
          <div
            style={{
              background: "var(--bg-card)",
              borderRadius: "var(--radius-lg)",
              border: "1px solid var(--border-subtle)",
              padding: 16,
            }}
          >
            <h3 style={{ fontSize: 12, fontWeight: 600, color: "var(--text-tertiary)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 10 }}>
              Audit Metadata
            </h3>
            <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "4px 16px", fontSize: 11 }}>
              <span style={{ color: "var(--text-muted)" }}>Model Version</span>
              <span style={{ color: "var(--text-secondary)", fontFamily: "'JetBrains Mono', monospace" }}>{ticket.modelVersion}</span>
              <span style={{ color: "var(--text-muted)" }}>Confidence Score</span>
              <span style={{ color: "var(--text-secondary)" }}>{Math.round(ticket.confidenceScore * 100)}%</span>
              <span style={{ color: "var(--text-muted)" }}>Approver</span>
              <span style={{ color: "var(--text-secondary)" }}>{ticket.approver}</span>
              <span style={{ color: "var(--text-muted)" }}>Escalation Path</span>
              <span style={{ color: "var(--text-secondary)" }}>{ticket.escalationPath.join(" → ")}</span>
              <span style={{ color: "var(--text-muted)" }}>Created</span>
              <span style={{ color: "var(--text-secondary)", fontFamily: "'JetBrains Mono', monospace" }}>
                {new Date(ticket.createdAt).toLocaleString()}
              </span>
            </div>
            <div style={{ marginTop: 8 }}>
              <span style={{ fontSize: 10, color: "var(--text-muted)" }}>Data Sources: </span>
              {ticket.dataSources.map((ds, i) => (
                <span
                  key={i}
                  style={{
                    fontSize: 10,
                    padding: "1px 6px",
                    borderRadius: "var(--radius-sm)",
                    background: "var(--bg-tertiary)",
                    color: "var(--text-tertiary)",
                    marginRight: 4,
                  }}
                >
                  {ds}
                </span>
              ))}
            </div>
          </div>

          {/* Decision History */}
          <DecisionHistory
            auditLog={ticket.auditLog}
            escalationHistory={ticket.escalationHistory}
            resolvedBy={ticket.resolvedBy}
            resolvedAt={ticket.resolvedAt}
            decision={ticket.decision}
          />
        </div>

        {/* ── Sidebar: Approval Panel ── */}
        <div style={{ width: 340, flexShrink: 0, display: "flex", flexDirection: "column", gap: 12 }}>
          <ApprovalPanel ticket={ticket} onDecision={handleDecision} />

          {/* Ticket Summary Card */}
          <div
            style={{
              background: "var(--bg-card)",
              borderRadius: "var(--radius-lg)",
              border: "1px solid var(--border-subtle)",
              padding: 16,
            }}
          >
            <h3 style={{ fontSize: 12, fontWeight: 600, color: "var(--text-tertiary)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 10 }}>
              Ticket Summary
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--text-muted)" }}>Priority</span>
                <PriorityBadge priority={ticket.priority} />
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--text-muted)" }}>Status</span>
                <span style={{ color: statusCfg.color, fontWeight: 600 }}>{statusCfg.label}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--text-muted)" }}>Scenario</span>
                <span style={{ color: "var(--text-secondary)" }}>{ticket.scenarioId}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--text-muted)" }}>Agent</span>
                <span style={{ color: "var(--text-secondary)" }}>{agentLabels[ticket.sourceAgent]?.split("—")[0] || ticket.sourceAgent}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--text-muted)" }}>Approver</span>
                <span style={{ color: "var(--text-secondary)" }}>{ticket.approver}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
