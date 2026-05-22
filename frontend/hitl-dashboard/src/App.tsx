import { useState, useCallback } from "react";
import type { HITLTicket } from "./types";
import { sampleTickets, dashboardMetrics } from "./data/sampleTickets";
import StatusBar from "./components/StatusBar";
import TicketQueue from "./components/TicketQueue";
import TicketDetail from "./components/TicketDetail";

export default function App() {
  const [tickets, setTickets] = useState<HITLTicket[]>(sampleTickets);
  const [selectedId, setSelectedId] = useState<string | null>(() => {
    // Default: select the first pending P0 or P1 ticket
    const firstPriority = sampleTickets.find(
      (t) => (t.priority === "P0-Critical" || t.priority === "P1-High") &&
        (t.status === "created" || t.status === "notified" || t.status === "review")
    );
    return firstPriority?.ticket_id || sampleTickets[0]?.ticket_id || null;
  });

  const selectedTicket = tickets.find((t) => t.ticket_id === selectedId) || null;

  const handleSelect = useCallback((id: string) => {
    setSelectedId(id);
  }, []);

  const handleDecision = useCallback(
    (ticketId: string, action: string, reason: string, overrideParams?: Record<string, unknown>) => {
      setTickets((prev) =>
        prev.map((t) => {
          if (t.ticket_id !== ticketId) return t;

          const now = new Date().toISOString();
          const updatedAudit = [
            ...t.auditLog,
            {
              timestamp: now,
              actor: "current.user@corp.com",
              detail: `${action.charAt(0).toUpperCase() + action.slice(1)}: ${reason || "No reason provided"}`,
            },
          ];

          let newStatus: HITLTicket["status"] = "closed";
          if (action === "approve") newStatus = "approved";
          else if (action === "reject") newStatus = "rejected";
          else if (action === "modify") newStatus = "override";
          else if (action === "escalate") {
            newStatus = "escalated";
            updatedAudit.push({
              timestamp: now,
              actor: "system",
              detail: `Escalated to ${reason || "next-level approver"}`,
            });
          } else if (action === "defer") {
            // Defer keeps as pending with note
            return {
              ...t,
              auditLog: [
                ...t.auditLog,
                {
                  timestamp: now,
                  actor: "current.user@corp.com",
                  detail: `Deferred: ${reason || "No reason"}`,
                },
              ],
            };
          }

          return {
            ...t,
            status: newStatus,
            resolvedBy: "current.user@corp.com",
            resolvedAt: now,
            decision: action as HITLTicket["decision"],
            overrideParams: overrideParams || null,
            auditLog: updatedAudit,
            sla: {
              ...t.sla,
              decision_at: now,
            },
          };
        })
      );
    },
    []
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <StatusBar metrics={dashboardMetrics} />

      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <TicketQueue
          tickets={tickets}
          selectedId={selectedId}
          onSelect={handleSelect}
        />

        {selectedTicket ? (
          <TicketDetail
            key={selectedTicket.ticket_id}
            ticket={selectedTicket}
            onDecision={handleDecision}
            onClose={() => setSelectedId(null)}
          />
        ) : (
          <div
            style={{
              flex: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--text-muted)",
              fontSize: 14,
            }}
          >
            No ticket selected — click a ticket from the queue
          </div>
        )}
      </div>
    </div>
  );
}
