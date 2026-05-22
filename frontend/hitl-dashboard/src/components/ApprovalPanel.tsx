import { useState } from "react";
import type { HITLTicket } from "../types";

interface Props {
  ticket: HITLTicket;
  onDecision: (action: string, reason: string, overrideParams?: Record<string, unknown>) => void;
}

const decisionActions = [
  { id: "approve", label: "Approve", color: "var(--color-success)" },
  { id: "reject", label: "Reject", color: "var(--color-danger)" },
  { id: "modify", label: "Modify", color: "var(--color-info)" },
  { id: "request_info", label: "Request Info", color: "var(--color-info)" },
  { id: "escalate", label: "Escalate", color: "var(--color-warning)" },
  { id: "defer", label: "Defer", color: "var(--text-secondary)" },
] as const;

export default function ApprovalPanel({ ticket, onDecision }: Props) {
  const [action, setAction] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [overrideHedge, setOverrideHedge] = useState("60");
  const [submitting, setSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState<{ ok: boolean; msg: string } | null>(null);

  const isPending =
    ticket.status === "created" || ticket.status === "notified" || ticket.status === "review";

  if (!isPending) return null;

  const handleSubmit = () => {
    setSubmitting(true);
    const params =
      action === "modify"
        ? { hedge_percentage: parseFloat(overrideHedge) || 60 }
        : undefined;
    onDecision(action!, reason, params);
    const label = decisionActions.find((a) => a.id === action)!.label;
    setSubmitResult({ ok: true, msg: `Decision submitted: ${label}` });
    setTimeout(() => setSubmitResult(null), 3000);
    setSubmitting(false);
  };

  const canSubmit = Boolean(
    action && (action === "approve" || action === "defer" || (reason && reason.length >= 3))
  );

  const getEscalateHint = () => {
    const next = ticket.escalationPath[1] || ticket.escalationPath[0];
    return next ? `Escalate to (default: ${next})` : "Escalate to (role/name)";
  };

  const getLabel = () => {
    switch (action) {
      case "approve": return "Approval reason (optional)";
      case "reject": return "Rejection reason (required)";
      case "modify": return "Modification details";
      case "request_info": return "Request additional analysis (15-min SLA pause)";
      case "escalate": return getEscalateHint();
      case "defer": return "Defer until (reason)";
      default: return "";
    }
  };

  const getPlaceholder = () => {
    switch (action) {
      case "approve": return "e.g., Hedge makes sense given market conditions...";
      case "reject": return "e.g., Insufficient data for this decision...";
      case "modify": return "e.g., Reduce hedge to 40%, maintain flexibility...";
      case "request_info": return "e.g., Show me last 5 similar price spikes...";
      case "escalate": return "e.g., Escalated to CFO for review...";
      case "defer": return "e.g., Revisit after Q3 forecast is published...";
      default: return "";
    }
  };

  return (
    <div
      style={{
        background: "var(--bg-card)",
        borderRadius: "var(--radius-lg)",
        border: "1px solid var(--border-subtle)",
        padding: 16,
        animation: "slideIn 0.25s ease-out",
      }}
    >
      <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, color: "var(--text-secondary)" }}>
        Decision Actions
      </h3>

      {/* Action buttons */}
      <div style={{ display: "flex", gap: 8, marginBottom: 14, flexWrap: "wrap" }}>
        {decisionActions.map((btn) => (
          <button
            key={btn.id}
            onClick={() => setAction(action === btn.id ? null : btn.id)}
            style={{
              padding: "6px 12px",
              borderRadius: "var(--radius-sm)",
              border: action === btn.id ? `1px solid ${btn.color}` : "1px solid var(--border-subtle)",
              background: action === btn.id ? `${btn.color}15` : "transparent",
              color: action === btn.id ? btn.color : "var(--text-secondary)",
              cursor: "pointer",
              fontSize: 11,
              fontWeight: 600,
              transition: "all 0.15s ease",
            }}
          >
            {btn.label}
          </button>
        ))}
      </div>

      {/* Reason input */}
      {action && (
        <div style={{ marginBottom: 14 }}>
          <label
            style={{
              fontSize: 11,
              color: "var(--text-tertiary)",
              marginBottom: 4,
              display: "block",
            }}
          >
            {getLabel()}
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder={getPlaceholder()}
            rows={2}
            style={{
              width: "100%",
              padding: "8px 10px",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border-subtle)",
              background: "var(--bg-input)",
              color: "var(--text-primary)",
              fontSize: 12,
              resize: "vertical",
              fontFamily: "inherit",
              outline: "none",
            }}
          />
        </div>
      )}

      {/* Override params */}
      {action === "modify" && (
        <div style={{ marginBottom: 14 }}>
          <label
            style={{
              fontSize: 11,
              color: "var(--text-tertiary)",
              marginBottom: 4,
              display: "block",
            }}
          >
            Hedge percentage (%)
          </label>
          <input
            type="number"
            value={overrideHedge}
            onChange={(e) => setOverrideHedge(e.target.value)}
            min={0}
            max={100}
            style={{
              width: 100,
              padding: "6px 8px",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border-subtle)",
              background: "var(--bg-input)",
              color: "var(--text-primary)",
              fontSize: 12,
              outline: "none",
            }}
          />
        </div>
      )}

      {/* Submit result feedback */}
      {submitResult && (
        <div
          style={{
            padding: "6px 10px",
            borderRadius: "var(--radius-sm)",
            background: submitResult.ok ? "var(--color-success)15" : "var(--color-danger)15",
            color: submitResult.ok ? "var(--color-success)" : "var(--color-danger)",
            fontSize: 11,
            fontWeight: 600,
            marginBottom: 8,
            textAlign: "center",
          }}
        >
          {submitResult.msg}
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={!canSubmit || submitting}
        style={{
          width: "100%",
          padding: "8px 14px",
          borderRadius: "var(--radius-sm)",
          border: "none",
          background: canSubmit && !submitting ? "var(--color-info)" : "var(--bg-tertiary)",
          color: canSubmit && !submitting ? "white" : "var(--text-muted)",
          cursor: canSubmit && !submitting ? "pointer" : "not-allowed",
          fontSize: 12,
          fontWeight: 600,
          transition: "all 0.15s ease",
        }}
      >
        {submitting
          ? "Processing..."
          : action
          ? `Submit ${action.charAt(0).toUpperCase() + action.slice(1)}`
          : "Select an action above"}
      </button>
    </div>
  );
}
