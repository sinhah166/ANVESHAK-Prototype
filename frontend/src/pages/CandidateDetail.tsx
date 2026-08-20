import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Globe2, Satellite, Activity, ShieldCheck, Clock, Thermometer } from 'lucide-react';

export default function CandidateDetail() {
  const { id } = useParams();

  return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-3 mb-5">
        <Link to="/candidates" className="p-2 rounded-lg hover:bg-surface-light border border-surface-border transition-colors">
          <ArrowLeft className="w-4 h-4 text-text-muted" />
        </Link>
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <Globe2 className="w-4 h-4 text-gold" />
            <h2 className="text-lg font-bold text-text tracking-wide">CANDIDATE DETAIL</h2>
          </div>
          <p className="text-xs text-text-muted font-mono">ID: {id || 'TIC-2024-0847'}</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-5">
        {/* Main Info */}
        <div className="col-span-2 glass-card p-5">
          <h3 className="text-base font-bold text-text mb-4">TOI-7892 b</h3>
          <div className="grid grid-cols-4 gap-4">
            {[
              { icon: Activity, label: 'Confidence', value: '97.4%', color: 'text-status-success' },
              { icon: Clock, label: 'Orbital Period', value: '3.21 days', color: 'text-gold' },
              { icon: Globe2, label: 'Radius', value: '1.8 R⊕', color: 'text-teal' },
              { icon: Thermometer, label: 'Eq. Temperature', value: '842 K', color: 'text-status-warning' },
            ].map((stat) => {
              const Icon = stat.icon;
              return (
                <div key={stat.label} className="stat-card">
                  <div className="flex items-center gap-2 mb-2">
                    <Icon className={`w-4 h-4 ${stat.color}`} />
                    <span className="text-[9px] text-text-muted uppercase tracking-wider">{stat.label}</span>
                  </div>
                  <p className="text-xl font-bold text-text font-mono">{stat.value}</p>
                </div>
              );
            })}
          </div>

          {/* Light Curve Placeholder */}
          <div className="mt-5 p-6 rounded-lg bg-surface border border-surface-border flex items-center justify-center h-48">
            <div className="text-center">
              <Activity className="w-8 h-8 text-gold/30 mx-auto mb-2" />
              <p className="text-sm text-text-muted">Light Curve Visualization</p>
              <p className="text-[10px] text-text-dim mt-1">Connect to backend to view transit data</p>
            </div>
          </div>
        </div>

        {/* Side Info */}
        <div className="space-y-5">
          <div className="glass-card p-4">
            <h4 className="section-title mb-3">SOURCE INFORMATION</h4>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Satellite className="w-4 h-4 text-teal" />
                <div>
                  <p className="text-sm text-text font-medium">TESS</p>
                  <p className="text-[10px] text-text-muted">Sector 47, Camera 2</p>
                </div>
              </div>
              <div>
                <p className="text-[9px] text-text-muted uppercase tracking-wider mb-1">Detection Time</p>
                <p className="text-sm text-text font-mono">2026-06-16 12:41:03 UTC</p>
              </div>
              <div>
                <p className="text-[9px] text-text-muted uppercase tracking-wider mb-1">Classification</p>
                <span className="badge badge-transit">Transit Candidate</span>
              </div>
            </div>
          </div>

          <div className="glass-card p-4">
            <h4 className="section-title mb-3">STATUS</h4>
            <span className="badge badge-high-priority">High Priority</span>
            <div className="mt-3 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-status-success" />
              <span className="text-xs text-text-muted">Passed automated vetting</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
