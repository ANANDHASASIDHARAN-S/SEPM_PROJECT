import { ThreatEvent } from "@/lib/types";

interface AlertTableProps {
  events: ThreatEvent[];
}

function levelBadge(level: ThreatEvent["alert_level"]): string {
  if (level === "CRITICAL") return "bg-red-600/20 text-red-300 border-red-500/40";
  if (level === "HIGH") return "bg-orange-500/20 text-orange-300 border-orange-400/40";
  if (level === "MEDIUM") return "bg-yellow-500/20 text-yellow-300 border-yellow-400/40";
  return "bg-emerald-500/20 text-emerald-300 border-emerald-400/40";
}

export default function AlertTable({ events }: AlertTableProps) {
  return (
    <div className="overflow-auto rounded-xl border border-soc-border bg-soc-panel2">
      <table className="w-full min-w-[900px] text-left text-xs text-soc-text">
        <thead className="sticky top-0 bg-[#0b111b] text-[11px] uppercase tracking-[0.08em] text-soc-muted">
          <tr>
            <th className="px-3 py-2">Time</th>
            <th className="px-3 py-2">Level</th>
            <th className="px-3 py-2">Source</th>
            <th className="px-3 py-2">Event</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">Details</th>
          </tr>
        </thead>
        <tbody>
          {events.map((event) => (
            <tr key={event.id} className="border-t border-soc-border/60 hover:bg-white/[0.03]">
              <td className="px-3 py-2 font-mono text-[11px] text-soc-muted">
                {new Date(event.timestamp).toLocaleTimeString()}
              </td>
              <td className="px-3 py-2">
                <span className={`inline-flex rounded border px-2 py-0.5 text-[11px] ${levelBadge(event.alert_level)}`}>
                  {event.alert_level}
                </span>
              </td>
              <td className="px-3 py-2">{event.source}</td>
              <td className="px-3 py-2">{event.event_type}</td>
              <td className="px-3 py-2 text-soc-muted">{event.status}</td>
              <td className="max-w-[340px] truncate px-3 py-2 text-soc-muted">{event.details ?? "-"}</td>
            </tr>
          ))}
          {events.length === 0 ? (
            <tr>
              <td colSpan={6} className="px-3 py-8 text-center text-soc-muted">
                No alerts yet. Start the SIEM generator to stream test data.
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}
