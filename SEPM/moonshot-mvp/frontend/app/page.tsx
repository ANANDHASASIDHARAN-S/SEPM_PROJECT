import AlertTable from "@/components/AlertTable";
import { ThreatEvent } from "@/lib/types";

const sampleAlerts: ThreatEvent[] = [
  {
    id: 101,
    alert_level: "CRITICAL",
    source: "SIEM",
    event_type: "Privilege Escalation Attempt",
    timestamp: new Date().toISOString(),
    status: "OPEN",
    details: "Admin token misuse pattern detected from 10.0.10.55",
  },
  {
    id: 102,
    alert_level: "HIGH",
    source: "EDR",
    event_type: "Suspicious PowerShell Execution",
    timestamp: new Date(Date.now() - 60_000).toISOString(),
    status: "INVESTIGATING",
    details: "Encoded command chain observed on faculty workstation",
  },
  {
    id: 103,
    alert_level: "MEDIUM",
    source: "Firewall",
    event_type: "Lateral Movement Traffic Spike",
    timestamp: new Date(Date.now() - 120_000).toISOString(),
    status: "OPEN",
    details: "Unusual east-west traffic between VLAN-12 and VLAN-22",
  },
];

const stats = [
  { label: "Open Alerts", value: 2 },
  { label: "Critical Open", value: 1 },
  { label: "Investigating", value: 1 },
  { label: "Tracked Users", value: "70,000+" },
];

export default function HomePage() {

  return (
    <main className="mx-auto flex min-h-screen max-w-[1500px] flex-col gap-4 p-4 lg:p-6">
      <header className="panel p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">SRM Moonshot SOC Dashboard (Sample)</h1>
            <p className="text-sm text-soc-muted">Simple dark-mode frontend with mock threat alerts</p>
          </div>
          <div className="rounded-lg border border-soc-border bg-soc-panel2 px-3 py-2 text-xs text-soc-muted">
            Demo Mode
          </div>
        </div>
      </header>

      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {stats.map((item) => (
          <div key={item.label} className="panel p-3">
            <p className="text-[11px] uppercase tracking-[0.08em] text-soc-muted">{item.label}</p>
            <p className="mt-1 text-2xl font-semibold">{item.value}</p>
          </div>
        ))}
      </section>

      <section className="grid flex-1 gap-4 lg:grid-cols-[300px_1fr]">
        <aside className="panel p-4">
          <h2 className="text-sm font-semibold uppercase tracking-[0.08em] text-soc-muted">Sample Notes</h2>

          <div className="mt-3 rounded-md border border-soc-border bg-soc-panel2 p-3 text-xs text-soc-muted">
            <p className="font-semibold text-soc-text">What this sample includes</p>
            <ul className="mt-2 list-disc space-y-1 pl-4">
              <li>Simple dark-mode SOC layout</li>
              <li>Mock alerts table</li>
              <li>Status cards for quick scanning</li>
            </ul>
          </div>
        </aside>

        <section className="panel p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-[0.08em] text-soc-muted">Threat Feed</h2>
            <span className="text-xs text-soc-muted">Static sample data</span>
          </div>
          <AlertTable events={sampleAlerts} />
        </section>
      </section>
    </main>
  );
}
