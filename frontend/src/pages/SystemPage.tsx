import { Settings, Server, Database, HardDrive, Cpu, Thermometer, Activity, Wifi, Shield } from 'lucide-react';

const systemStats = [
  { icon: Cpu, label: 'CPU Usage', value: '34%', status: 'normal' },
  { icon: HardDrive, label: 'Memory', value: '6.2 / 16 GB', status: 'normal' },
  { icon: Database, label: 'Database', value: 'Connected', status: 'good' },
  { icon: Server, label: 'Redis', value: 'Connected', status: 'good' },
  { icon: Wifi, label: 'WebSocket', value: '24 clients', status: 'normal' },
  { icon: Thermometer, label: 'System Temp', value: '42°C', status: 'normal' },
  { icon: Shield, label: 'Security', value: 'No threats', status: 'good' },
  { icon: Activity, label: 'API Latency', value: '1.24 sec', status: 'normal' },
];

const configItems = [
  { label: 'Pipeline Mode', value: 'Real-time Processing' },
  { label: 'ML Model', value: 'Random Forest v2.1' },
  { label: 'Detection Threshold', value: '0.85 confidence' },
  { label: 'Auto-Classification', value: 'Enabled' },
  { label: 'Data Retention', value: '90 days' },
  { label: 'Backup Schedule', value: 'Every 6 hours' },
];

export default function SystemPage() {
  return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-2 mb-5">
        <Settings className="w-4 h-4 text-gold" />
        <h2 className="text-lg font-bold text-text tracking-wide">SYSTEM SETTINGS</h2>
      </div>

      <div className="grid grid-cols-2 gap-5">
        {/* System Health */}
        <div className="glass-card p-5">
          <h3 className="section-title mb-4">SYSTEM HEALTH</h3>
          <div className="grid grid-cols-2 gap-3">
            {systemStats.map((stat) => {
              const Icon = stat.icon;
              return (
                <div key={stat.label} className="stat-card flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-surface-light border border-surface-border flex items-center justify-center flex-shrink-0">
                    <Icon className={`w-4 h-4 ${stat.status === 'good' ? 'text-status-success' : 'text-gold'}`} />
                  </div>
                  <div>
                    <p className="text-[9px] text-text-muted uppercase tracking-wider">{stat.label}</p>
                    <p className="text-sm font-semibold text-text font-mono">{stat.value}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Configuration */}
        <div className="glass-card p-5">
          <h3 className="section-title mb-4">CONFIGURATION</h3>
          <div className="space-y-3">
            {configItems.map((item) => (
              <div key={item.label} className="flex items-center justify-between py-2 border-b border-surface-border last:border-0">
                <span className="text-sm text-text-muted">{item.label}</span>
                <span className="text-sm text-text font-medium font-mono">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
