import { useState, useMemo } from "react";
import type { HITLTicket, HITLPriority, AgentId, HITLStatus, FilterState } from "../types";
import TicketCard from "./TicketCard";

interface Props {
  tickets: HITLTicket[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

const priorities: (HITLPriority | "all")[] = ["all", "P0-Critical", "P1-High", "P2-Medium", "P3-Low"];

const agents: { value: AgentId | "all"; label: string }[] = [
  { value: "all", label: "All Agents" },
  { value: "agent-01", label: "Procurement" },
  { value: "agent-02", label: "Production" },
  { value: "agent-03", label: "Inventory" },
  { value: "agent-04", label: "Sales" },
  { value: "agent-05", label: "Market" },
  { value: "agent-06", label: "Predictive" },
  { value: "agent-07", label: "Financial" },
  { value: "agent-08", label: "Compliance" },
  { value: "agent-09", label: "Orchestrator" },
];

export default function TicketQueue({ tickets, selectedId, onSelect }: Props) {
  const [filters, setFilters] = useState<FilterState>({
    priority: "all",
    agent: "all",
    status: "pending",
    search: "",
  });

  const filtered = useMemo(() => {
    return tickets.filter((t) => {
      if (filters.priority !== "all" && t.priority !== filters.priority) return false;
      if (filters.agent !== "all" && t.sourceAgent !== filters.agent) return false;
      if (filters.status === "pending" && t.status !== "created" && t.status !== "notified" && t.status !== "review") return false;
      if (filters.status !== "all" && filters.status !== "pending" && t.status !== filters.status) return false;
      if (filters.search) {
        const q = filters.search.toLowerCase();
        return (
          t.title.toLowerCase().includes(q) ||
          t.ticket_id.toLowerCase().includes(q) ||
          t.scenarioId.toLowerCase().includes(q) ||
          t.sourceAgent.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [tickets, filters]);

  // Group pending vs resolved
  const pending = filtered.filter((t) => t.status === "created" || t.status === "notified" || t.status === "review");
  const resolved = filtered.filter((t) => !(t.status === "created" || t.status === "notified" || t.status === "review"));

  // Sort: P0 first, then P1, then by SLA deadline (most urgent first)
  const sortPriority = (a: HITLTicket, b: HITLTicket) => {
    const prioMap: Record<string, number> = { "P0-Critical": 0, "P1-High": 1, "P2-Medium": 2, "P3-Low": 3 };
    const pa = prioMap[a.priority] ?? 99;
    const pb = prioMap[b.priority] ?? 99;
    if (pa !== pb) return pa - pb;
    return new Date(a.sla.sla_deadline).getTime() - new Date(b.sla.sla_deadline).getTime();
  };

  const sorted = [...pending].sort(sortPriority);
  const sortedResolved = [...resolved].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

  return (
    <div
      style={{
        width: "var(--sidebar-width)",
        borderRight: "1px solid var(--border-subtle)",
        display: "flex",
        flexDirection: "column",
        background: "var(--bg-secondary)",
        flexShrink: 0,
      }}
    >
      {/* ── Filters ── */}
      <div style={{ padding: "12px 14px", borderBottom: "1px solid var(--border-subtle)", display: "flex", flexDirection: "column", gap: 8 }}>
        <input
          type="text"
          placeholder="Search tickets..."
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          style={{
            width: "100%",
            padding: "7px 10px",
            borderRadius: "var(--radius-sm)",
            border: "1px solid var(--border-subtle)",
            background: "var(--bg-input)",
            color: "var(--text-primary)",
            fontSize: 12,
            outline: "none",
          }}
          onFocus={(e) => (e.currentTarget.style.borderColor = "var(--border-focus)")}
          onBlur={(e) => (e.currentTarget.style.borderColor = "var(--border-subtle)")}
        />
        <div style={{ display: "flex", gap: 6 }}>
          <select
            value={filters.priority}
            onChange={(e) => setFilters({ ...filters, priority: e.target.value as HITLPriority | "all" })}
            style={{
              flex: 1,
              padding: "5px 6px",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border-subtle)",
              background: "var(--bg-input)",
              color: "var(--text-primary)",
              fontSize: 11,
              outline: "none",
            }}
          >
            {priorities.map((p) => (
              <option key={p} value={p}>
                {p === "all" ? "All Priorities" : p}
              </option>
            ))}
          </select>
          <select
            value={filters.agent}
            onChange={(e) => setFilters({ ...filters, agent: e.target.value as AgentId | "all" })}
            style={{
              flex: 1,
              padding: "5px 6px",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border-subtle)",
              background: "var(--bg-input)",
              color: "var(--text-primary)",
              fontSize: 11,
              outline: "none",
            }}
          >
            {agents.map((a) => (
              <option key={a.value} value={a.value}>
                {a.label}
              </option>
            ))}
          </select>
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value as HITLStatus | "pending" | "all" })}
            style={{
              flex: 1,
              padding: "5px 6px",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border-subtle)",
              background: "var(--bg-input)",
              color: "var(--text-primary)",
              fontSize: 11,
              outline: "none",
            }}
          >
            <option value="pending">Pending Only</option>
            <option value="all">All Statuses</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="override">Overrides</option>
            <option value="escalated">Escalated</option>
          </select>
        </div>
        <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
          {filtered.length} ticket{filtered.length !== 1 ? "s" : ""}
          {pending.length > 0 && ` · ${pending.length} pending`}
        </div>
      </div>

      {/* ── Ticket List ── */}
      <div style={{ flex: 1, overflowY: "auto", padding: "8px" }}>
        {sorted.length > 0 && (
          <>
            <div
              style={{
                fontSize: 10,
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                color: "var(--text-muted)",
                padding: "4px 8px 8px",
              }}
            >
              Pending ({sorted.length})
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {sorted.map((t) => (
                <TicketCard key={t.ticket_id} ticket={t} isSelected={selectedId === t.ticket_id} onClick={() => onSelect(t.ticket_id)} />
              ))}
            </div>
          </>
        )}

        {sortedResolved.length > 0 && (
          <>
            <div
              style={{
                fontSize: 10,
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                color: "var(--text-muted)",
                padding: "16px 8px 8px",
              }}
            >
              Resolved ({sortedResolved.length})
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {sortedResolved.map((t) => (
                <TicketCard key={t.ticket_id} ticket={t} isSelected={selectedId === t.ticket_id} onClick={() => onSelect(t.ticket_id)} />
              ))}
            </div>
          </>
        )}

        {filtered.length === 0 && (
          <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
            No tickets match the current filters.
          </div>
        )}
      </div>
    </div>
  );
}
