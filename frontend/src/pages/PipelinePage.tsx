import React, { useEffect, useState } from 'react';
import { Play, Database, Zap, Cpu, Server, CheckCircle2, XCircle, Loader2 } from 'lucide-react';

const PipelinePage = () => {
  const [status, setStatus] = useState<any>(null);
  const [isDemoRunning, setIsDemoRunning] = useState(false);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/pipeline/status');
      const data = await res.json();
      setStatus(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const runDemo = async () => {
    setIsDemoRunning(true);
    try {
      await fetch('/api/pipeline/demo', { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
    setTimeout(() => setIsDemoRunning(false), 2000);
  };

  if (!status) return <div className="p-8 text-center text-text_muted">Loading pipeline status...</div>;

  const getStageIcon = (stageName: string) => {
    switch (stageName) {
      case 'ingestion': return <Database size={24} />;
      case 'preprocessing': return <Cpu size={24} />;
      case 'detection': return <Zap size={24} />;
      case 'classification': return <Activity size={24} />;
      case 'normalization': return <Server size={24} />;
      case 'database': return <Database size={24} />;
      default: return <Server size={24} />;
    }
  };

  // Helper icon just for mapping
  const Activity = ({size}: {size:number}) => (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
  );

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-10">
      <header className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight">Pipeline Monitor</h2>
          <p className="text-text_muted mt-1">Real-time status of data processing stages</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-text_muted">System Status:</span>
            {status.is_running ? (
              <span className="text-warning flex items-center gap-1"><Loader2 size={14} className="animate-spin" /> PROCESSING</span>
            ) : (
              <span className="text-success flex items-center gap-1"><CheckCircle2 size={14} /> IDLE</span>
            )}
          </div>
          <button 
            onClick={runDemo}
            disabled={status.is_running || isDemoRunning}
            className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play size={16} /> Run Demo Sequence
          </button>
        </div>
      </header>

      <div className="glass-card p-8 relative overflow-hidden">
        {/* Animated background line */}
        <div className="absolute top-1/2 left-10 right-10 h-1 bg-white/5 -translate-y-1/2 hidden md:block"></div>
        {status.is_running && (
          <div className="absolute top-1/2 left-10 w-20 h-1 bg-primary blur-[2px] -translate-y-1/2 hidden md:block animate-[shimmer_2s_infinite]"></div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-6 gap-6 relative z-10">
          {status.stages.map((stage: any, index: number) => {
            const isRunning = stage.status === 'running';
            const isError = stage.status === 'error';
            
            let colorClass = 'text-text_muted bg-surface border-white/10';
            if (isRunning) colorClass = 'text-primary bg-primary/10 border-primary/50 shadow-[0_0_15px_rgba(56,189,248,0.2)]';
            if (isError) colorClass = 'text-danger bg-danger/10 border-danger/50';

            return (
              <div key={stage.stage} className="flex flex-col items-center text-center group">
                <div className={`w-16 h-16 rounded-2xl border flex items-center justify-center mb-4 transition-all duration-300 ${colorClass}`}>
                  {isRunning ? <Loader2 size={28} className="animate-spin" /> : getStageIcon(stage.stage)}
                </div>
                <h4 className="font-semibold text-sm uppercase tracking-wider mb-1">
                  {stage.stage}
                </h4>
                <div className="text-xs text-text_muted space-y-1">
                  <p>Processed: <span className="text-white font-mono">{stage.processed_count}</span></p>
                  {stage.error_count > 0 && <p className="text-danger">Errors: {stage.error_count}</p>}
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); opacity: 0; }
          50% { opacity: 1; }
          100% { transform: translateX(50vw); opacity: 0; }
        }
      `}</style>
    </div>
  );
};

export default PipelinePage;
