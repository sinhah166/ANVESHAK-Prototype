import { Globe2, Search, Filter, ChevronRight, Satellite } from 'lucide-react';

const candidates = [
  { id: 'TIC-2024-0847', name: 'TOI-7892 b', source: 'TESS', type: 'Transit Candidate', confidence: 97.4, status: 'High Priority', period: '3.21d', radius: '1.8 R⊕', temp: '842K' },
  { id: 'KIC-2024-1293', name: 'KOI-8821.01', source: 'Kepler', type: 'Transit Candidate', confidence: 94.8, status: 'Review', period: '7.55d', radius: '2.3 R⊕', temp: '654K' },
  { id: 'BL-2024-0392', name: 'GJ 1151 Signal', source: 'Breakthrough Listen', type: 'Radio Anomaly', confidence: 91.2, status: 'Detected', period: 'N/A', radius: 'N/A', temp: 'N/A' },
  { id: 'TIC-2024-0846', name: 'TOI-7891 c', source: 'TESS', type: 'Transit Candidate', confidence: 88.6, status: 'Processing', period: '12.4d', radius: '3.1 R⊕', temp: '412K' },
  { id: 'KIC-2024-1292', name: 'KOI-8820.02', source: 'Kepler', type: 'Transit Candidate', confidence: 85.1, status: 'Processing', period: '5.88d', radius: '1.4 R⊕', temp: '1024K' },
  { id: 'TIC-2024-0845', name: 'TOI-7890 d', source: 'TESS', type: 'Transit Candidate', confidence: 82.3, status: 'Review', period: '21.7d', radius: '4.2 R⊕', temp: '298K' },
];

export default function CandidatesList() {
  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Globe2 className="w-4 h-4 text-gold" />
            <h2 className="text-lg font-bold text-text tracking-wide">EXOPLANET ANALYSIS</h2>
          </div>
          <p className="text-xs text-text-muted">Detected transit candidates and radio anomalies awaiting classification</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted" />
            <input type="text" placeholder="Search candidates..." className="pl-9 pr-4 py-2 text-xs bg-surface border border-surface-border rounded-lg text-text placeholder-text-dim focus:outline-none focus:border-gold/30 transition-colors w-56" />
          </div>
          <button className="flex items-center gap-2 px-3 py-2 text-xs bg-surface border border-surface-border rounded-lg text-text-muted hover:text-text hover:border-gold/20 transition-all">
            <Filter className="w-3.5 h-3.5" /> Filters
          </button>
        </div>
      </div>

      <div className="glass-card overflow-hidden">
        <table className="event-table w-full">
          <thead>
            <tr className="border-b border-surface-border">
              <th className="text-left pl-5">ID</th>
              <th className="text-left">Name</th>
              <th className="text-left">Source</th>
              <th className="text-left">Type</th>
              <th className="text-left">Confidence</th>
              <th className="text-left">Period</th>
              <th className="text-left">Radius</th>
              <th className="text-left">Eq. Temp</th>
              <th className="text-left">Status</th>
              <th className="text-right pr-5"></th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((c) => (
              <tr key={c.id} className="transition-colors cursor-pointer group">
                <td className="pl-5 font-mono text-xs text-gold-dim">{c.id}</td>
                <td className="text-sm font-medium text-text">{c.name}</td>
                <td>
                  <div className="flex items-center gap-2">
                    <Satellite className="w-3 h-3 text-gold-dim" />
                    <span className="text-sm text-text-muted">{c.source}</span>
                  </div>
                </td>
                <td><span className={`badge ${c.type.includes('Radio') ? 'badge-radio' : 'badge-transit'}`}>{c.type}</span></td>
                <td className="font-mono text-sm">{c.confidence}%</td>
                <td className="font-mono text-xs text-text-muted">{c.period}</td>
                <td className="font-mono text-xs text-text-muted">{c.radius}</td>
                <td className="font-mono text-xs text-text-muted">{c.temp}</td>
                <td><span className={`badge badge-${c.status === 'High Priority' ? 'high-priority' : c.status === 'Review' ? 'review' : c.status === 'Detected' ? 'detected' : 'processing'}`}>{c.status}</span></td>
                <td className="pr-5 text-right">
                  <ChevronRight className="w-4 h-4 text-text-dim group-hover:text-gold transition-colors inline" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between mt-4">
        <p className="text-[10px] text-text-muted">Showing 6 of 342 candidates</p>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-text-muted">Auto-refreshing</span>
          <div className="w-1.5 h-1.5 rounded-full bg-status-success live-pulse"></div>
        </div>
      </div>
    </div>
  );
}
