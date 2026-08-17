import { useEffect, useState } from 'react';
import { RadioTower, CheckCircle2, XCircle, RefreshCw } from 'lucide-react';

const SourcesPage = () => {
  const [sources, setSources] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [checkingId, setCheckingId] = useState<string | null>(null);

  const fetchSources = async () => {
    try {
      const res = await fetch('/api/sources');
      const data = await res.json();
      setSources(data.sources);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSources();
  }, []);

  const checkHealth = async (id: string) => {
    setCheckingId(id);
    try {
      await fetch(`/api/sources/${id}/health`, { method: 'POST' });
      await fetchSources();
    } catch (e) {
      console.error(e);
    } finally {
      setCheckingId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-10">
      <header>
        <h2 className="text-3xl font-bold text-white tracking-tight">Data Sources</h2>
        <p className="text-text_muted mt-1">Configured astronomical data ingestion points and adapters</p>
      </header>

      {loading ? (
        <div className="text-center text-text_muted">Loading sources...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {sources.map((source) => (
            <div key={source.id} className="glass-card flex flex-col h-full relative overflow-hidden">
              {/* Type Accent Banner */}
              <div className={`h-1 w-full absolute top-0 left-0 ${source.type === 'lightcurve' ? 'bg-primary' : 'bg-accent'}`}></div>
              
              <div className="p-6 flex-1 flex flex-col">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-surface_hover rounded-lg border border-white/5">
                      <RadioTower className={source.type === 'lightcurve' ? 'text-primary' : 'text-accent'} />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold">{source.name}</h3>
                      <p className="text-sm font-mono text-text_muted uppercase">{source.type}</p>
                    </div>
                  </div>
                  <div>
                    {source.health === 'healthy' ? (
                      <span className="badge badge-success flex items-center gap-1"><CheckCircle2 size={12} /> OK</span>
                    ) : source.health === 'unhealthy' ? (
                      <span className="badge badge-danger flex items-center gap-1"><XCircle size={12} /> ERR</span>
                    ) : (
                      <span className="badge">UNKNOWN</span>
                    )}
                  </div>
                </div>

                <div className="space-y-3 flex-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-text_muted">Adapter</span>
                    <span className="font-mono bg-surface px-2 rounded border border-white/5">{source.adapter}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-text_muted">Status</span>
                    <span>{source.enabled ? 'Enabled' : 'Disabled'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-text_muted">Total Processed</span>
                    <span className="font-mono">{source.observation_count.toLocaleString()}</span>
                  </div>
                  {source.last_seen && (
                    <div className="flex justify-between text-sm">
                      <span className="text-text_muted">Last Seen</span>
                      <span>{new Date(source.last_seen).toLocaleString()}</span>
                    </div>
                  )}
                  {source.error_message && (
                    <div className="mt-4 p-3 bg-danger/10 border border-danger/20 rounded text-xs text-danger">
                      {source.error_message}
                    </div>
                  )}
                </div>

                <div className="mt-6 pt-4 border-t border-white/5 flex gap-3">
                  <button 
                    onClick={() => checkHealth(source.id)}
                    disabled={checkingId === source.id || !source.enabled}
                    className="flex-1 py-2 bg-surface hover:bg-surface_hover border border-white/10 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <RefreshCw size={14} className={checkingId === source.id ? 'animate-spin' : ''} />
                    Check Health
                  </button>
                  <button 
                    className="flex-1 py-2 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                    disabled={!source.enabled}
                  >
                    Run Specific
                  </button>
                </div>
              </div>
            </div>
          ))}

          {/* Add Future Adapter Card */}
          <div className="glass-card flex flex-col h-full border-dashed border-2 border-white/10 hover:border-white/20 transition-colors cursor-pointer bg-transparent items-center justify-center p-8 text-center group">
            <div className="w-16 h-16 rounded-full bg-surface flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <span className="text-2xl text-text_muted">+</span>
            </div>
            <h3 className="font-medium text-text_muted group-hover:text-white transition-colors">Add Future Telescope</h3>
            <p className="text-sm text-text_muted/70 mt-2">Implement a new adapter class and register it in sources.yaml to ingest new data formats.</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default SourcesPage;
