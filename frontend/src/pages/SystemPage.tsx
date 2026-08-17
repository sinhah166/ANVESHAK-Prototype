import React, { useEffect, useState } from 'react';
import { Server, Database, Activity, Code } from 'lucide-react';

const SystemPage = () => {
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await fetch('/api/health');
        const data = await res.json();
        setHealth(data);
      } catch (e) {
        console.error(e);
      }
    };
    
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  if (!health) return <div className="p-8 text-center text-text_muted">Loading system metrics...</div>;

  const services = [
    { name: 'FastAPI Backend', icon: Code, status: health.status === 'healthy' ? 'connected' : 'error' },
    { name: 'PostgreSQL DB', icon: Database, status: health.database },
    { name: 'Redis Streams', icon: Activity, status: health.redis },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-10">
      <header>
        <h2 className="text-3xl font-bold text-white tracking-tight">System Health</h2>
        <p className="text-text_muted mt-1">Infrastructure and microservices status</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {services.map((svc) => (
          <div key={svc.name} className="glass-card p-6 flex items-center gap-4">
            <div className={`p-4 rounded-xl bg-surface border border-white/5`}>
              <svc.icon size={24} className={svc.status === 'connected' ? 'text-success' : 'text-danger'} />
            </div>
            <div>
              <h3 className="font-semibold">{svc.name}</h3>
              <div className="flex items-center gap-2 mt-1">
                <div className={`w-2 h-2 rounded-full ${svc.status === 'connected' ? 'bg-success' : 'bg-danger animate-pulse'}`}></div>
                <span className="text-sm text-text_muted uppercase tracking-wide">{svc.status}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="glass-card p-8 mt-8">
        <h3 className="text-xl font-bold mb-6 flex items-center gap-2 border-b border-white/5 pb-4">
          <Server className="text-primary" /> Application Details
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <ul className="space-y-4">
              <li className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-text_muted">Data Mode</span>
                <span className="font-mono text-primary uppercase">{health.mode}</span>
              </li>
              <li className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-text_muted">Frontend Version</span>
                <span className="font-mono">1.0.0-mvp</span>
              </li>
              <li className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-text_muted">Environment</span>
                <span className="font-mono">Docker Compose</span>
              </li>
            </ul>
          </div>
          
          <div className="bg-surface/50 p-6 rounded-lg border border-white/5">
            <h4 className="text-sm font-bold text-text_muted uppercase tracking-wider mb-2">Scientific Disclaimer</h4>
            <p className="text-sm leading-relaxed text-text_muted">
              ANVESHAK produces preliminary astronomical candidates and automated classifications. 
              These outputs are intended for research triage and demonstration purposes and do 
              <strong className="text-white"> not constitute scientific confirmation</strong> of an exoplanet or extraterrestrial signal. 
              Candidate validation requires independent astronomical analysis.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemPage;
