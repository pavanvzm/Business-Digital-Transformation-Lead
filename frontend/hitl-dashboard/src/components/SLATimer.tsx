import { useState, useEffect } from "react";
import type { HITLPriority } from "../types";

interface Props {
  deadline: string;
  created: string;
  slaMinutes: number;
  priority: HITLPriority;
}

export default function SLATimer({ deadline, created, slaMinutes, priority }: Props) {
  const [remaining, setRemaining] = useState(calcRemaining(deadline));
  const [elapsed, setElapsed] = useState(calcElapsed(created));

  useEffect(() => {
    const interval = setInterval(() => {
      setRemaining(calcRemaining(deadline));
      setElapsed(calcElapsed(created));
    }, 1000);
    return () => clearInterval(interval);
  }, [deadline, created]);

  const isOverdue = remaining <= 0;
  const pctUsed = slaMinutes > 0 ? Math.min((elapsed / (slaMinutes * 60)) * 100, 100) : 0;

  const formatTime = (seconds: number) => {
    if (seconds <= 0) return "OVERDUE";
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    if (m >= 60) return `${Math.floor(m / 60)}h ${m % 60}m`;
    return `${m}m ${s}s`;
  };

  const barColor =
    priority === "P0-Critical" ? "var(--color-p0)" :
    priority === "P1-High" ? "var(--color-p1)" :
    priority === "P2-Medium" ? "var(--color-p2)" :
    "var(--color-p3)";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 3, minWidth: 110 }}>
      <div
        style={{
          fontSize: 13,
          fontWeight: 600,
          fontFamily: "'JetBrains Mono', 'Consolas', monospace",
          color: isOverdue ? "var(--color-danger)" : remaining < slaMinutes * 60 * 0.25 ? "var(--color-p1)" : "var(--text-primary)",
          animation: isOverdue ? "timerWarning 1s ease-in-out infinite" : "none",
        }}
      >
        {isOverdue ? "⚠ OVERDUE" : formatTime(remaining)}
      </div>
      <div
        style={{
          height: 3,
          background: "var(--bg-tertiary)",
          borderRadius: 2,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${Math.min(pctUsed, 100)}%`,
            background: isOverdue ? "var(--color-danger)" : barColor,
            borderRadius: 2,
            transition: "width 1s linear",
            opacity: isOverdue ? 0.7 : 1,
          }}
        />
      </div>
      <div style={{ fontSize: 10, color: "var(--text-tertiary)", fontFamily: "'JetBrains Mono', 'Consolas', monospace" }}>
        SLA: {slaMinutes}m
      </div>
    </div>
  );
}

function calcRemaining(deadline: string): number {
  return Math.max(0, Math.floor((new Date(deadline).getTime() - Date.now()) / 1000));
}

function calcElapsed(created: string): number {
  return Math.floor((Date.now() - new Date(created).getTime()) / 1000);
}
