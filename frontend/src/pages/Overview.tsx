import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import StatsCards from '../components/StatsCards';
import LiveFeed from '../components/LiveFeed';

const Overview = () => {
  const [stats, setStats] = useState<any>(null);

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/pipeline/stats');
      const data = await res.json();
      setStats(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchStats();
    // Poll stats every 5 seconds
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  if (!stats) return <div className="p-8 text-center text-text_muted">Loading dashboard...</div>;

  // Format data for Recharts
  const classData = Object.entries(stats.classification_distribution || {}).map(([name, value]) => ({
    name: name.replace('_', ' ').toUpperCase(),
    value
  }));

  const sourceData = Object.entries(stats.source_distribution || {}).map(([name, value]) => ({
    name: name.toUpperCase(),
    value
  }));

  const COLORS = ['#38BDF8', '#818CF8', '#34D399', '#FBBF24', '#F87171', '#9CA3AF'];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      <header className="mb-8">
        <h2 className="text-3xl font-bold text-white tracking-tight">Mission Control</h2>
        <p className="text-text_muted mt-1">Real-time overview of the ANVESHAK pipeline</p>
      </header>

      <StatsCards stats={stats} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[500px]">
        {/* Left Column: Charts */}
        <div className="lg:col-span-2 space-y-6 flex flex-col h-full">
          
          {/* Classification Chart */}
          <div className="glass-card p-6 flex-1 flex flex-col">
            <h3 className="text-lg font-medium mb-4">Candidate Classifications</h3>
            <div className="flex-1 w-full min-h-[150px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={classData} layout="vertical" margin={{ left: 50, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E2532" horizontal={false} />
                  <XAxis type="number" stroke="#9CA3AF" fontSize={12} />
                  <YAxis dataKey="name" type="category" stroke="#9CA3AF" fontSize={10} width={100} />
                  <Tooltip cursor={{fill: '#1E2532'}} contentStyle={{backgroundColor: '#151A24', border: '1px solid #1E2532'}} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {classData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Sources Chart */}
          <div className="glass-card p-6 flex-1 flex flex-col">
            <h3 className="text-lg font-medium mb-4">Observation Sources</h3>
            <div className="flex-1 w-full min-h-[150px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sourceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E2532" vertical={false} />
                  <XAxis dataKey="name" stroke="#9CA3AF" fontSize={12} />
                  <YAxis stroke="#9CA3AF" fontSize={12} />
                  <Tooltip cursor={{fill: '#1E2532'}} contentStyle={{backgroundColor: '#151A24', border: '1px solid #1E2532'}} />
                  <Bar dataKey="value" fill="#38BDF8" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          
        </div>

        {/* Right Column: Live Feed */}
        <div className="lg:col-span-1 h-full">
          <LiveFeed />
        </div>
      </div>
    </div>
  );
};

export default Overview;
