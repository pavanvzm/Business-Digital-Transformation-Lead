import type { HITLTicket } from "../types";
import PriorityBadge from "./PriorityBadge";
import SLATimer from "./SLATimer";

interface Props {
  ticket: HITLTicket;
  isSelected: boolean;
  onClick: () => void;
}

const statusLabel: Record<string, string> = {
  created: "Created",
  notified: "Notified",
  review: "In Review",
  approved: "Approved ✓",
  rejected: "Rejected ✗",
  override: "Override",
  escalated: "Escalated",
  timeout: "Timed Out",
  cancelled: "Cancelled",
  closed: "Closed",
};

const agentBadge: Record<string, string> = {
  "agent-01": "Procurement",
  "agent-02": "Production",
  "agent-03": "Inventory",
  "agent-04": "Sales",
  "agent-05": "Market",
  "agent-06": "Predictive",
  "agent-07": "Financial",
  "agent-08": "Compliance",
  "agent-09": "Orchestrator",
};

export default function TicketCard({ ticket, isSelected, onClick }: Props) {
  const isPending =
    ticket.status === "created" || ticket.status === "notified" || ticket.status === "review";
  const isCritical = ticket.priority === "P0-Critical" && isPending;

  return (
    <div
      onClick={onClick}
      style={{
        padding: "12px 16px",
        background: isSelected
          ? "var(--bg-card-hover)"
          : "var(--bg-card)",
        borderLeft: `3px solid ${
          ticket.priority === "P0-Critical"
            ? "var(--color-p0)"
            : ticket.priority === "P1-High"
            ? "var(--color-p1)"
            : ticket.priority === "P2-Medium"
            ? "var(--color-p2)"
            : "var(--color-p3)"
        }`,
        borderRadius: "var(--radius-md)",
        cursor: "pointer",
        transition: "all 0.15s ease",
        boxShadow: isCritical
          ? "0 0 12px var(--color-p0-glow)"
          : isSelected
          ? "0 2px 8px rgba(0,0,0,0.3)"
          : "0 1px 3px rgba(0,0,0,0.2)",
        opacity: !isPending ? 0.6 : 1,
        animation: isCritical ? "pulse-sla 2s ease-in-out infinite" : "none",
      }}
      onMouseEnter={(e) => {
        if (!isSelected) e.currentTarget.style.background = "var(--bg-card-hover)";
      }}
      onMouseLeave={(e) => {
        if (!isSelected) e.currentTarget.style.background = "var(--bg-card)";
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <PriorityBadge priority={ticket.priority} />
          <span style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "'JetBrains Mono', monospace" }}>
            {ticket.ticket_id}
          </span>
        </div>
        {isPending && <SLATimer deadline={ticket.sla.sla_deadline} created={ticket.createdAt} slaMinutes={ticket.sla.sla_minutes} priority={ticket.priority} />}
        {!isPending && (
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              color:
                ticket.status === "approved" || ticket.status === "override"
                  ? "var(--color-success)"
                  : ticket.status === "rejected"
                  ? "var(--color-danger)"
                  : ticket.status === "escalated"
                  ? "var(--color-warning)"
                  : "var(--text-muted)",
            }}
          >
            {statusLabel[ticket.status] || ticket.status}
          </span>
        )}
      </div>

      <h3
        style={{
          fontSize: 13,
          fontWeight: 600,
          color: "var(--text-primary)",
          marginBottom: 4,
          lineHeight: 1.3,
          display: "-webkit-box",
          WebkitLineClamp: 2,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
        }}
      >
        {ticket.title}
      </h3>

      <p
        style={{
          fontSize: 11,
          color: "var(--text-tertiary)",
          marginBottom: 8,
          display: "-webkit-box",
          WebkitLineClamp: 1,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
        }}
      >
        {ticket.description}
      </p>

      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        <span
          style={{
            fontSize: 10,
            padding: "1px 6px",
            borderRadius: "var(--radius-sm)",
            background: "var(--bg-tertiary)",
            color: "var(--text-secondary)",
          }}
        >
          {agentBadge[ticket.sourceAgent] || ticket.sourceAgent}
        </span>
        <span
          style={{
            fontSize: 10,
            padding: "1px 6px",
            borderRadius: "var(--radius-sm)",
            background: "var(--bg-tertiary)",
            color: "var(--text-secondary)",
          }}
        >
          {ticket.scenarioId}
        </span>
        <span
          style={{
            fontSize: 10,
            padding: "1px 6px",
            borderRadius: "var(--radius-sm)",
            background: "var(--bg-tertiary)",
            color: "var(--text-secondary)",
          }}
        >
          Approver: {ticket.approver}
        </span>
      </div>
    </div>
  );
}
