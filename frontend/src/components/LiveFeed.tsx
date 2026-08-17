import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useWebSocket } from '../hooks/useWebSocket';

const getClassificationColor = (classification: string) => {
  if (classification === 'planet_candidate' || classification === 'narrowband_candidate') return 'badge-success';
  if (classification === 'false_positive' || classification === 'noise') return 'badge-danger';
  if (classification === 'anomaly' || classification === 'rfi') return 'badge-warning';
  return 'badge-primary';
};

const LiveFeed: React.FC = () => {
  const { eventHistory } = useWebSocket();
  const navigate = useNavigate();

  return (
    <div className="glass-card flex flex-col h-full">
      <div className="p-5 border-b border-white/5 flex items-center justify-between">
        <h3 className="font-semibold tracking-wide flex items-center gap-2">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-primary"></span>
          </span>
          LIVE DETECTION FEED
        </h3>
        <span className="text-xs text-text_muted font-mono">{eventHistory.length} events</span>
      </div>
      
      <div className="flex-1 overflow-y-auto p-2">
        {eventHistory.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-text_muted p-8 text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-surface_hover flex items-center justify-center animate-pulse">
              <span className="text-2xl">📡</span>
            </div>
            <p>Waiting for signals...<br/>Run the Demo Pipeline to see live events.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {eventHistory.map((event, i) => (
              <div 
                key={`${event.candidate_id}-${i}`}
                onClick={() => navigate(`/candidates/${event.candidate_id}`)}
                className="p-4 rounded-lg bg-surface_hover border border-white/5 hover:border-primary/30 hover:bg-white/5 transition-all cursor-pointer group animate-[slideIn_0.3s_ease-out]"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-mono text-text_muted">{new Date(event.timestamp).toLocaleTimeString()}</span>
                    <span className="text-xs font-bold px-2 py-1 bg-surface rounded text-primary">{event.source_id.toUpperCase()}</span>
                  </div>
                  <span className={`badge ${getClassificationColor(event.classification)}`}>
                    {event.classification.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
                
                <div className="flex items-end justify-between mt-3">
                  <div>
                    <p className="text-sm text-text_muted">Target</p>
                    <p className="font-medium">{event.target_name}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-text_muted">Confidence</p>
                    <p className="font-mono font-medium text-primary">{(event.confidence * 100).toFixed(1)}%</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default LiveFeed;
