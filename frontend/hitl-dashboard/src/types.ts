/** Priority levels matching the HITL policy Section 5.3 */
export type HITLPriority = "P0-Critical" | "P1-High" | "P2-Medium" | "P3-Low";

/** Ticket lifecycle states matching policy Section 5.1 state machine */
export type HITLStatus =
  | "created"
  | "notified"
  | "review"
  | "approved"
  | "rejected"
  | "override"
  | "escalated"
  | "timeout"
  | "cancelled"
  | "closed";

/** Decision actions from policy Section 5.2 Step 4 */
export type HITLDecisionAction =
  | "approve"
  | "reject"
  | "modify"
  | "defer"
  | "escalate"
  | "request_info";

/** Agent IDs from the policy Section 4.1 matrix */
export type AgentId =
  | "agent-01"
  | "agent-02"
  | "agent-03"
  | "agent-04"
  | "agent-05"
  | "agent-06"
  | "agent-07"
  | "agent-08"
  | "agent-09";

/** Business impact from policy Appendix A format */
export interface BusinessImpact {
  costIncrease?: string;
  marginImpact?: string;
  affectedLines?: string;
  cashFlow?: string;
  inventoryCover?: string;
  description?: string;
}

/** Agent recommendation option from policy Appendix A */
export interface RecommendationOption {
  label: string;
  description: string;
  impact: string;
  confidence: number;
  dataSources: string[];
  modelVersion?: string;
}

/** SLA metrics from policy Section 7.1 audit trail */
export interface SLAMetrics {
  created_at: string;
  notified_at: string | null;
  decision_at: string | null;
  sla_deadline: string;
  sla_minutes: number;
}

/** Escalation history entry from policy Section 5.2 */
export interface EscalationEntry {
  from: string;
  to: string;
  timestamp: string;
  reason?: string;
}

/** Audit log entry from policy Section 7.1 */
export interface AuditEntry {
  timestamp: string;
  actor: string;
  detail: string;
}

/** Full HITL ticket model matching policy Sections 5.2 and 7.1 + Appendix A */
export interface HITLTicket {
  ticket_id: string; // Format: H-YYYY-NNNN
  title: string;
  description: string;
  triggerValue: string;
  priority: HITLPriority;
  status: HITLStatus;
  sourceAgent: AgentId;
  scenarioId: string; // e.g., H-002, H-010
  approver: string;
  sla: SLAMetrics;
  businessImpact: BusinessImpact;
  recommendations: RecommendationOption[];
  alternatives: string[];
  decision: HITLDecisionAction | null;
  resolvedBy: string | null;
  resolvedAt: string | null;
  overrideParams: Record<string, unknown> | null;
  escalationPath: string[];
  escalationHistory: EscalationEntry[];
  auditLog: AuditEntry[];
  confidenceScore: number;
  modelVersion: string;
  dataSources: string[];
  createdAt: string;
}

/** Dashboard-level metrics from policy Section 7.5 */
export interface DashboardMetrics {
  slaComplianceRate: number;
  overrideRate: number;
  avgResponseTimeP0: number;
  avgResponseTimeP1: number;
  overdueTicketRatio: number;
  escalationRate: number;
  totalTicketsToday: number;
  pendingCount: number;
  p0Pending: number;
  p1Pending: number;
}

/** Filter state for the ticket queue */
export interface FilterState {
  priority: HITLPriority | "all";
  agent: AgentId | "all";
  status: HITLStatus | "pending" | "all";
  search: string;
}
