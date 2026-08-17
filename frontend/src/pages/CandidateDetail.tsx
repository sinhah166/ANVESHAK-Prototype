import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Target, Cpu, Clock, Activity, AlertTriangle } from 'lucide-react';
import LightCurveChart from '../charts/LightCurveChart';
import SpectrogramChart from '../charts/SpectrogramChart';

const CandidateDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [candidate, setCandidate] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const res = await fetch(`/api/candidates/${id}`);
        const data = await res.json();
        setCandidate(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [id]);

  if (loading) return <div className="p-8 text-center text-text_muted">Loading candidate data...</div>;
  if (!candidate) return <div className="p-8 text-center text-danger">Candidate not found</div>;

  const isTransit = candidate.candidate_type === 'transit' || candidate.signal_type === 'transit';
  const isRadio = candidate.candidate_type === 'radio_signal' || candidate.signal_type.startsWith('radio');

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-10">
      <header className="mb-6">
        <button 
          onClick={() => navigate('/candidates')}
          className="flex items-center gap-2 text-text_muted hover:text-white transition-colors mb-4 text-sm"
        >
          <ArrowLeft size={16} /> Back to Candidates
        </button>
        
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="px-3 py-1 bg-surface rounded text-sm font-bold text-primary">
                {candidate.source_id.toUpperCase()}
              </span>
              <span className="text-sm font-mono text-text_muted">{candidate.record_id}</span>
            </div>
            <h2 className="text-3xl font-bold text-white tracking-tight">{candidate.target_name}</h2>
            <p className="text-text_muted mt-1 flex gap-4">
              <span>RA: {candidate.ra.toFixed(4)}°</span>
              <span>Dec: {candidate.dec.toFixed(4)}°</span>
            </p>
          </div>
          
          <div className="text-right">
            <div className="text-2xl font-bold text-white">{candidate.classification.replace('_', ' ').toUpperCase()}</div>
            <div className="text-primary font-mono mt-1">CONFIDENCE: {(candidate.confidence * 100).toFixed(1)}%</div>
          </div>
        </div>
      </header>

      {/* Warning for unvalidated data */}
      <div className="bg-warning/10 border border-warning/20 rounded-lg p-4 flex items-start gap-3">
        <AlertTriangle className="text-warning shrink-0" size={20} />
        <div className="text-sm text-text_muted">
          <strong className="text-warning block mb-1">Preliminary Scientific Candidate</strong>
          ANVESHAK automated output does not constitute scientific confirmation. Validating this candidate requires independent astronomical analysis and follow-up observation.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Metadata & Features */}
        <div className="space-y-6">
          
          <div className="glass-card p-6">
            <h3 className="text-lg font-medium mb-4 border-b border-white/5 pb-2 flex items-center gap-2">
              <Cpu size={18} className="text-primary" /> Processing Details
            </h3>
            <ul className="space-y-3 text-sm">
              <li className="flex justify-between"><span className="text-text_muted">Status</span> <span className="badge badge-primary">{candidate.status.toUpperCase()}</span></li>
              <li className="flex justify-between"><span className="text-text_muted">Signal Type</span> <span className="font-medium capitalize">{candidate.signal_type.replace('_', ' ')}</span></li>
              <li className="flex justify-between"><span className="text-text_muted">Model Used</span> <span className="font-mono text-xs">{candidate.model_name}</span></li>
              <li className="flex justify-between"><span className="text-text_muted">Observed</span> <span>{new Date(candidate.observed_at).toLocaleString()}</span></li>
            </ul>
          </div>

          <div className="glass-card p-6">
            <h3 className="text-lg font-medium mb-4 border-b border-white/5 pb-2 flex items-center gap-2">
              <Activity size={18} className="text-accent" /> Extracted Features
            </h3>
            
            {isTransit && candidate.transit_features && (
              <ul className="space-y-3 text-sm">
                <li className="flex justify-between"><span className="text-text_muted">Period</span> <span className="font-mono">{candidate.transit_features.period?.toFixed(5) || 'N/A'} days</span></li>
                <li className="flex justify-between"><span className="text-text_muted">Depth</span> <span className="font-mono">{((candidate.transit_features.depth || 0) * 100).toFixed(3)}%</span></li>
                <li className="flex justify-between"><span className="text-text_muted">Duration</span> <span className="font-mono">{candidate.transit_features.duration?.toFixed(2) || 'N/A'} hrs</span></li>
                <li className="flex justify-between"><span className="text-text_muted">Transit Time (T0)</span> <span className="font-mono">{candidate.transit_features.transit_time?.toFixed(4) || 'N/A'}</span></li>
                <li className="flex justify-between"><span className="text-text_muted">Detection SDE</span> <span className="font-mono">{candidate.transit_features.detection_power?.toFixed(1) || 'N/A'}</span></li>
                <li className="flex justify-between"><span className="text-text_muted">Transits Observed</span> <span className="font-mono">{candidate.transit_features.n_transits || 'N/A'}</span></li>
              </ul>
            )}

            {isRadio && candidate.radio_features && (
              <ul className="space-y-3 text-sm">
                <li className="flex justify-between"><span className="text-text_muted">Center Freq</span> <span className="font-mono">{candidate.radio_features.frequency_mhz?.toFixed(4) || 'N/A'} MHz</span></li>
                <li className="flex justify-between"><span className="text-text_muted">Bandwidth</span> <span className="font-mono">{candidate.radio_features.bandwidth_hz?.toFixed(1) || 'N/A'} Hz</span></li>
                <li className="flex justify-between"><span className="text-text_muted">Duration</span> <span className="font-mono">{candidate.radio_features.duration_seconds?.toFixed(1) || 'N/A'} s</span></li>
                <li className="flex justify-between"><span className="text-text_muted">Signal/Noise</span> <span className="font-mono">{candidate.radio_features.signal_strength?.toFixed(1) || 'N/A'}</span></li>
                <li className="flex justify-between"><span className="text-text_muted">Drift Rate</span> <span className="font-mono">{candidate.radio_features.drift_rate?.toFixed(3) || '0'} Hz/s</span></li>
              </ul>
            )}
          </div>
        </div>

        {/* Right Column: Visualizations */}
        <div className="lg:col-span-2 space-y-6">
          
          {isTransit && candidate.light_curve_data && (
            <>
              <div className="glass-card p-4">
                <LightCurveChart 
                  time={candidate.light_curve_data.time}
                  flux={candidate.light_curve_data.flux}
                  type="timeseries"
                  title="Processed Light Curve"
                  inTransitMask={candidate.metadata?.in_transit_mask}
                />
              </div>

              {candidate.phase_folded_data && (
                <div className="glass-card p-4">
                  <LightCurveChart 
                    phase={candidate.phase_folded_data.phase}
                    foldedFlux={candidate.phase_folded_data.flux}
                    type="phase_folded"
                    title={`Phase-Folded Curve (Period: ${candidate.transit_features?.period?.toFixed(3)} d)`}
                  />
                </div>
              )}
            </>
          )}

          {isRadio && candidate.spectrogram_data && (
            <div className="glass-card p-4">
              <SpectrogramChart 
                spectrogram={candidate.spectrogram_data.spectrogram}
                frequencies={candidate.spectrogram_data.frequencies}
                times={candidate.spectrogram_data.times}
                title="Dynamic Spectrum"
              />
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default CandidateDetail;
