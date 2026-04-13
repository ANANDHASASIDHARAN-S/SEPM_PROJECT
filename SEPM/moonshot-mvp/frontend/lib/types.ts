export type AlertLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type ThreatStatus = "OPEN" | "INVESTIGATING" | "RESOLVED" | "FALSE_POSITIVE";

export interface ThreatEvent {
  id: number;
  alert_level: AlertLevel;
  source: string;
  event_type: string;
  timestamp: string;
  status: ThreatStatus;
  details: string | null;
}

export interface DashboardResponse {
  total_open_alerts: number;
  critical_open_alerts: number;
  investigating_alerts: number;
  latest_events: ThreatEvent[];
}
