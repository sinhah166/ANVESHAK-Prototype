import { Activity, CheckCircle2, Zap, ArrowRight, Loader2 } from 'lucide-react';

const pipelineStages = [
  { name: 'Ingestion', status: 'active', processed: '1,248', rate: '42/min', icon: Zap },
  { name: 'Preprocessing', status: 'active', processed: '1,245', rate: '41/min', icon: Activity },
  { name: 'Feature Extraction', status: 'active', processed: '1,242', rate: '40/min', icon: Activity },
  { name: 'Detection', status: 'active', processed: '892', rate: '28/min', icon: CheckCircle2 },
  { name: 'AI Classification', status: 'active', processed: '889', rate: '27/min', icon: Activity },
  { name: 'Delivery', status: 'active', processed: '886', rate: '27/min', icon: CheckCircle2 },
];

const recentJobs = [
  { id: 'JOB-4821', source: 'TESS Sector 47', started: '12:38:22', status: 'Running', progress: 78 },
  { id: 'JOB-4820', source: 'Kepler Q16', started: '12:35:10', status: 'Running', progress: 92 },
  { id: 'JOB-4819', source: 'BL Scan #2847', started: '12:30:05', status: 'Completed', progress: 100 },
  { id: 'JOB-4818', source: 'TESS Sector 46', started: '12:22:18', status: 'Completed', progress: 100 },
];

export default function PipelinePage() {
  return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-2 mb-5">
        <Activity className="w-4 h-4 text-gold" />
        <h2 className="text-lg font-bold text-text tracking-wide">PIPELINE MONITOR</h2>
      </div>

      {/* Pipeline Flow */}
      <div className="glass-card p-5 mb-5">
        <h3 className="section-title mb-4">PIPELINE STAGES</h3>
        <div className="flex items-center justify-between">
          {pipelineStages.map((stage, idx) => {
            const Icon = stage.icon;
            return (
              <div key={stage.name} className="flex items-center">
                <div className="flex flex-col items-center gap-2">
                  <div className="w-12 h-12 rounded-xl bg-status-success/10 border border-status-success/25 flex items-center justify-center">
                    <Icon className="w-5 h-5 text-status-success" />
                  </div>
                  <span className="text-[10px] text-text font-medium text-center max-w-[80px]">{stage.name}</span>
                  <div className="text-center">
                    <p className="text-sm font-bold text-text font-mono">{stage.processed}</p>
                    <p className="text-[9px] text-text-muted">{stage.rate}</p>
                  </div>
                </div>
                {idx < pipelineStages.length - 1 && (
                  <ArrowRight className="w-4 h-4 text-gold/30 mx-3 mb-10" />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Jobs */}
      <div className="glass-card">
        <div className="px-5 pt-4 pb-3">
          <h3 className="section-title">RECENT JOBS</h3>
        </div>
        <table className="event-table w-full">
          <thead>
            <tr className="border-b border-surface-border">
              <th className="text-left pl-5">Job ID</th>
              <th className="text-left">Source</th>
              <th className="text-left">Started</th>
              <th className="text-left">Progress</th>
              <th className="text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {recentJobs.map((job) => (
              <tr key={job.id} className="transition-colors">
                <td className="pl-5 font-mono text-xs text-gold-dim">{job.id}</td>
                <td className="text-sm text-text">{job.source}</td>
                <td className="font-mono text-xs text-text-muted">{job.started} UTC</td>
                <td>
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-1.5 rounded-full bg-surface-light overflow-hidden">
                      <div
                        className="progress-fill"
                        style={{ width: `${job.progress}%` }}
                      ></div>
                    </div>
                    <span className="text-[10px] text-text-muted font-mono">{job.progress}%</span>
                  </div>
                </td>
                <td>
                  <span className={`badge ${job.status === 'Running' ? 'badge-processing' : 'badge-detected'}`}>
                    {job.status === 'Running' && <Loader2 className="w-3 h-3 mr-1 animate-spin inline" />}
                    {job.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
