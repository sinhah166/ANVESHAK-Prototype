import React from 'react';
import { Activity, Star, Zap, Database } from 'lucide-react';

interface StatsProps {
  stats: {
    total_observations: number;
    total_candidates: number;
    high_confidence_candidates: number;
    active_sources: number;
  };
}

const StatCard = ({ title, value, icon: Icon, colorClass }: { title: string, value: number, icon: any, colorClass: string }) => (
  <div className="glass-card p-6 relative overflow-hidden group">
    <div className={`absolute top-0 right-0 w-32 h-32 -mr-8 -mt-8 rounded-full blur-3xl opacity-20 transition-opacity group-hover:opacity-40 ${colorClass}`}></div>
    
    <div className="flex items-start justify-between relative z-10">
      <div>
        <p className="text-text_muted font-medium mb-2">{title}</p>
        <h3 className="text-3xl font-bold font-mono tracking-tight">{value.toLocaleString()}</h3>
      </div>
      <div className={`p-3 rounded-xl bg-surface_hover border border-white/5`}>
        <Icon size={24} className={colorClass.replace('bg-', 'text-')} />
      </div>
    </div>
  </div>
);

const StatsCards: React.FC<StatsProps> = ({ stats }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard 
        title="Total Observations" 
        value={stats.total_observations} 
        icon={Database} 
        colorClass="bg-primary text-primary" 
      />
      <StatCard 
        title="Detected Candidates" 
        value={stats.total_candidates} 
        icon={Activity} 
        colorClass="bg-accent text-accent" 
      />
      <StatCard 
        title="High Confidence" 
        value={stats.high_confidence_candidates} 
        icon={Star} 
        colorClass="bg-warning text-warning" 
      />
      <StatCard 
        title="Active Sources" 
        value={stats.active_sources} 
        icon={Zap} 
        colorClass="bg-success text-success" 
      />
    </div>
  );
};

export default StatsCards;
