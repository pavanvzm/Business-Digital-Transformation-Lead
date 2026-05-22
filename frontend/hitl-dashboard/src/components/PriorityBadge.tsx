import type { HITLPriority } from "../types";

interface Props {
  priority: HITLPriority;
}

const priorityConfig: Record<HITLPriority, { label: string; bg: string; color: string; glow: string }> = {
  "P0-Critical": { label: "P0-Critical", bg: "var(--color-p0-bg)", color: "var(--color-p0)", glow: "var(--color-p0-glow)" },
  "P1-High":    { label: "P1-High",    bg: "var(--color-p1-bg)", color: "var(--color-p1)", glow: "transparent" },
  "P2-Medium":  { label: "P2-Medium",  bg: "var(--color-p2-bg)", color: "var(--color-p2)", glow: "transparent" },
  "P3-Low":     { label: "P3-Low",     bg: "var(--color-p3-bg)", color: "var(--color-p3)", glow: "transparent" },
};

export default function PriorityBadge({ priority }: Props) {
  const cfg = priorityConfig[priority];

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        padding: "2px 8px",
        borderRadius: "var(--radius-sm)",
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: "0.02em",
        textTransform: "uppercase",
        background: cfg.bg,
        color: cfg.color,
        boxShadow: priority === "P0-Critical" ? `0 0 8px ${cfg.glow}` : "none",
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: cfg.color,
          opacity: priority === "P0-Critical" ? 1 : 0.7,
        }}
      />
      {cfg.label}
    </span>
  );
}
