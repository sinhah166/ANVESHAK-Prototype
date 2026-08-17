import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, ChevronLeft, ChevronRight } from 'lucide-react';

const CandidatesList = () => {
  const navigate = useNavigate();
  const [candidates, setCandidates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 20;

  // Filters
  const [sourceId, setSourceId] = useState('');
  const [classification, setClassification] = useState('');

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      const skip = (page - 1) * limit;
      let url = `/api/candidates?skip=${skip}&limit=${limit}`;
      if (sourceId) url += `&source_id=${sourceId}`;
      if (classification) url += `&classification=${classification}`;

      const res = await fetch(url);
      const data = await res.json();
      setCandidates(data.items);
      setTotal(data.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, [page, sourceId, classification]);

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-10">
      <header className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight">Candidates Explorer</h2>
          <p className="text-text_muted mt-1">Browse and filter detected astronomical signals</p>
        </div>
        
        {/* Filters */}
        <div className="flex gap-4">
          <div className="relative">
            <Filter size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text_muted" />
            <select 
              className="bg-surface border border-white/10 rounded-lg pl-10 pr-8 py-2 text-sm text-text_main focus:outline-none focus:border-primary appearance-none"
              value={sourceId}
              onChange={(e) => { setSourceId(e.target.value); setPage(1); }}
            >
              <option value="">All Sources</option>
              <option value="tess">TESS</option>
              <option value="kepler">Kepler</option>
              <option value="radio_demo">Radio Demo</option>
              <option value="synthetic">Synthetic</option>
            </select>
          </div>
          
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text_muted" />
            <select 
              className="bg-surface border border-white/10 rounded-lg pl-10 pr-8 py-2 text-sm text-text_main focus:outline-none focus:border-primary appearance-none"
              value={classification}
              onChange={(e) => { setClassification(e.target.value); setPage(1); }}
            >
              <option value="">All Classifications</option>
              <option value="planet_candidate">Planet Candidate</option>
              <option value="narrowband_candidate">Radio Candidate</option>
              <option value="stellar_variability">Stellar Variability</option>
              <option value="false_positive">False Positive</option>
              <option value="noise">Noise / RFI</option>
            </select>
          </div>
        </div>
      </header>

      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/5 bg-surface/50 text-text_muted text-xs uppercase tracking-wider">
                <th className="p-4 font-medium">ID</th>
                <th className="p-4 font-medium">Source</th>
                <th className="p-4 font-medium">Target</th>
                <th className="p-4 font-medium">Classification</th>
                <th className="p-4 font-medium">Confidence</th>
                <th className="p-4 font-medium">Time</th>
                <th className="p-4 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr><td colSpan={7} className="p-8 text-center text-text_muted">Loading candidates...</td></tr>
              ) : candidates.length === 0 ? (
                <tr><td colSpan={7} className="p-8 text-center text-text_muted">No candidates found matching criteria.</td></tr>
              ) : (
                candidates.map((cand) => (
                  <tr 
                    key={cand.id} 
                    onClick={() => navigate(`/candidates/${cand.id}`)}
                    className="hover:bg-white/5 cursor-pointer transition-colors"
                  >
                    <td className="p-4 font-mono text-sm">{cand.id}</td>
                    <td className="p-4"><span className="px-2 py-1 bg-surface rounded text-xs font-bold text-primary">{cand.source_id.toUpperCase()}</span></td>
                    <td className="p-4 font-medium">{cand.target_name}</td>
                    <td className="p-4">
                      {cand.classification.replace('_', ' ').toUpperCase()}
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-surface rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${cand.confidence > 0.8 ? 'bg-success' : cand.confidence > 0.5 ? 'bg-warning' : 'bg-danger'}`}
                            style={{ width: `${cand.confidence * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-mono">{(cand.confidence * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="p-4 text-sm text-text_muted">{new Date(cand.created_at).toLocaleString()}</td>
                    <td className="p-4"><span className="badge badge-primary">{cand.status.toUpperCase()}</span></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        <div className="p-4 border-t border-white/5 flex items-center justify-between bg-surface/30">
          <p className="text-sm text-text_muted">
            Showing {total === 0 ? 0 : (page - 1) * limit + 1} to {Math.min(page * limit, total)} of {total} results
          </p>
          <div className="flex gap-2">
            <button 
              className="p-2 rounded hover:bg-white/10 disabled:opacity-50 disabled:hover:bg-transparent"
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              <ChevronLeft size={18} />
            </button>
            <button 
              className="p-2 rounded hover:bg-white/10 disabled:opacity-50 disabled:hover:bg-transparent"
              onClick={() => setPage(p => p + 1)}
              disabled={page >= totalPages}
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CandidatesList;
