import { Database, Satellite, Radio, CheckCircle2, Clock, Activity } from 'lucide-react';

const sources = [
  {
    name: 'TESS',
    fullName: 'Transiting Exoplanet Survey Satellite',
    type: 'Optical',
    status: 'Active',
    lastSync: '2 min ago',
    eventsToday: 847,
    totalProcessed: '2.4M',
    uptime: '99.97%',
    color: '#2dd4bf',
    description: 'NASA space telescope designed to search for exoplanets using the transit method across the full sky.',
  },
  {
    name: 'Kepler Space Telescope',
    fullName: 'Kepler / K2 Mission Archive',
    type: 'Optical',
    status: 'Active',
    lastSync: '5 min ago',
    eventsToday: 312,
    totalProcessed: '1.8M',
    uptime: '99.94%',
    color: '#c8a45c',
    description: 'Historical data archive from NASA Kepler mission. Contains 9+ years of high-precision photometric light curves.',
  },
  {
    name: 'Breakthrough Listen (GBT)',
    fullName: 'Green Bank Telescope',
    type: 'Radio',
    status: 'Active',
    lastSync: '1 min ago',
    eventsToday: 89,
    totalProcessed: '420K',
    uptime: '99.88%',
    color: '#f59e0b',
    description: 'Radio frequency observations from the Green Bank Telescope as part of the Breakthrough Listen SETI initiative.',
  },
];

export default function SourcesPage() {
  return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-2 mb-5">
        <Database className="w-4 h-4 text-gold" />
        <h2 className="text-lg font-bold text-text tracking-wide">DATA SOURCES</h2>
      </div>

      <div className="grid grid-cols-1 gap-5">
        {sources.map((source) => (
          <div key={source.name} className="glass-card-hover p-5">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-start gap-4">
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ background: `${source.color}12`, border: `1px solid ${source.color}25` }}
                >
                  {source.type === 'Radio' ? (
                    <Radio className="w-6 h-6" style={{ color: source.color }} />
                  ) : (
                    <Satellite className="w-6 h-6" style={{ color: source.color }} />
                  )}
                </div>
                <div>
                  <h3 className="text-base font-bold text-text">{source.name}</h3>
                  <p className="text-xs text-text-muted">{source.fullName}</p>
                  <p className="text-xs text-text-dim mt-1 max-w-lg">{source.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-status-success" />
                <span className="text-sm text-status-success font-medium">{source.status}</span>
              </div>
            </div>

            <div className="grid grid-cols-4 gap-4">
              {[
                { icon: Clock, label: 'Last Sync', value: source.lastSync },
                { icon: Activity, label: 'Events Today', value: source.eventsToday.toLocaleString() },
                { icon: Database, label: 'Total Processed', value: source.totalProcessed },
                { icon: CheckCircle2, label: 'Uptime', value: source.uptime },
              ].map((stat) => {
                const Icon = stat.icon;
                return (
                  <div key={stat.label} className="stat-card">
                    <div className="flex items-center gap-1.5 mb-1">
                      <Icon className="w-3 h-3 text-text-muted" />
                      <span className="text-[9px] text-text-muted uppercase tracking-wider">{stat.label}</span>
                    </div>
                    <p className="text-sm font-bold text-text font-mono">{stat.value}</p>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
