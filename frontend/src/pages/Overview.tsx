import { useMemo } from 'react';
import {
  Activity, Target, Radio, ShieldCheck, Loader2, ChevronLeft,
  ChevronRight, Play, ExternalLink, Globe2, Moon, Orbit,
  Telescope, Satellite, Rocket, ArrowUpRight,
  CheckCircle2
} from 'lucide-react';
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis } from 'recharts';

/* ─── Mock Data ──────────────────────────────────────────── */

const statCards = [
  { icon: Activity, label: 'TOTAL EVENTS', value: '1,248', change: '+12.6%', color: 'text-gold' },
  { icon: Target, label: 'TRANSIT CANDIDATES', value: '342', change: '+8.3%', color: 'text-teal' },
  { icon: Radio, label: 'RADIO ANOMALIES', value: '86', change: '+15.1%', color: 'text-status-warning' },
  { icon: ShieldCheck, label: 'HIGH CONFIDENCE', value: '124', change: '+19.2%', color: 'text-status-success' },
  { icon: Loader2, label: 'PROCESSING', value: '23', subtext: 'Live in pipeline', color: 'text-gold-dim' },
];

const eventStreamData = [
  { time: '12:41:03', source: 'TESS', sourceIcon: 'tess', eventType: 'Transit Candidate', eventClass: 'transit', confidence: '97.4%', status: 'High Priority', statusClass: 'high-priority' },
  { time: '12:40:51', source: 'Kepler', sourceIcon: 'kepler', eventType: 'Transit Candidate', eventClass: 'transit', confidence: '94.8%', status: 'Review', statusClass: 'review' },
  { time: '12:40:32', source: 'Breakthrough Listen', sourceIcon: 'btl', eventType: 'Radio Anomaly', eventClass: 'radio', confidence: '91.2%', status: 'Detected', statusClass: 'detected' },
  { time: '12:39:18', source: 'TESS', sourceIcon: 'tess', eventType: 'Transit Candidate', eventClass: 'transit', confidence: '88.6%', status: 'Processing', statusClass: 'processing' },
  { time: '12:38:47', source: 'Kepler', sourceIcon: 'kepler', eventType: 'Transit Candidate', eventClass: 'transit', confidence: '85.1%', status: 'Processing', statusClass: 'processing' },
];

const dataSources = [
  { name: 'TESS', full: 'Transiting Exoplanet Survey Satellite', type: 'Optical', color: '#2dd4bf' },
  { name: 'Kepler Space Telescope', full: '', type: 'Optical', color: '#c8a45c' },
  { name: 'Breakthrough Listen (GBT)', full: '', type: 'Radio', color: '#f59e0b' },
];

const pipelineSteps = ['Ingestion', 'Preprocessing', 'Detection', 'AI Classification', 'Delivery'];

const universeStats = [
  { icon: Globe2, label: 'Planets', value: '8' },
  { icon: Moon, label: 'Moons', value: '146' },
  { icon: Orbit, label: 'Asteroids', value: '12,043' },
  { icon: Telescope, label: 'Galaxies', value: '2.1M' },
  { icon: Satellite, label: 'Exoplanets', value: '5,672' },
];

/* ─── Telemetry Chart Data Generator ─────────────────────── */

function generateTelemetryData() {
  const data = [];
  for (let i = 0; i < 60; i++) {
    const minute = i;
    const base = 70 + Math.sin(i * 0.15) * 15;
    const noise = (Math.random() - 0.5) * 10;
    data.push({
      time: `${String(Math.floor(minute / 60)).padStart(2, '0')}:${String(minute % 60).padStart(2, '0')}`,
      signal: Math.max(40, Math.min(100, base + noise)),
      dataRate: Math.max(30, Math.min(100, 60 + Math.cos(i * 0.2) * 20 + (Math.random() - 0.5) * 8)),
    });
  }
  return data;
}

/* ─── Component ──────────────────────────────────────────── */

export default function Overview() {
  const telemetryData = useMemo(() => generateTelemetryData(), []);

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Rocket className="w-4 h-4 text-gold" />
            <h2 className="text-lg font-bold text-text tracking-wide">MISSION OVERVIEW</h2>
          </div>
          <p className="text-xs text-text-muted">Real-time overview of astronomical event detection & classification</p>
        </div>
      </div>

      {/* Main Grid Layout */}
      <div className="flex gap-5">
        {/* Left + Center Column */}
        <div className="flex-1 min-w-0 space-y-5">
          {/* Stat Cards */}
          <div className="grid grid-cols-5 gap-3">
            {statCards.map((card) => {
              const Icon = card.icon;
              return (
                <div key={card.label} className="stat-card animate-slide-up">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-7 h-7 rounded-lg bg-surface-light border border-surface-border flex items-center justify-center">
                      <Icon className={`w-3.5 h-3.5 ${card.color}`} />
                    </div>
                    <span className="text-[9px] text-text-muted uppercase tracking-wider font-medium leading-tight">{card.label}</span>
                  </div>
                  <p className="text-2xl font-bold text-text font-mono tracking-tight">{card.value}</p>
                  {card.change && (
                    <p className="text-[10px] text-status-success mt-1 flex items-center gap-0.5">
                      <ArrowUpRight className="w-2.5 h-2.5" />
                      {card.change} <span className="text-text-dim ml-1">vs yesterday</span>
                    </p>
                  )}
                  {card.subtext && (
                    <p className="text-[10px] text-text-muted mt-1">{card.subtext}</p>
                  )}
                </div>
              );
            })}
          </div>

          {/* Live Event Stream */}
          <div className="glass-card">
            <div className="flex items-center justify-between px-5 pt-4 pb-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-status-danger red-pulse"></div>
                <h3 className="section-title">LIVE EVENT STREAM</h3>
              </div>
              <button className="text-[11px] text-gold-dim hover:text-gold transition-colors flex items-center gap-1">
                View all <ExternalLink className="w-3 h-3" />
              </button>
            </div>
            <table className="event-table w-full">
              <thead>
                <tr className="border-b border-surface-border">
                  <th className="text-left pl-5 w-8"></th>
                  <th className="text-left">Time (UTC)</th>
                  <th className="text-left">Source</th>
                  <th className="text-left">Event Type</th>
                  <th className="text-left">Confidence</th>
                  <th className="text-left">Status</th>
                </tr>
              </thead>
              <tbody>
                {eventStreamData.map((event, idx) => (
                  <tr key={idx} className="transition-colors cursor-pointer">
                    <td className="pl-5">
                      <div className="w-2 h-2 rounded-full bg-status-danger red-pulse"></div>
                    </td>
                    <td className="font-mono text-text-muted text-xs">{event.time}</td>
                    <td>
                      <div className="flex items-center gap-2">
                        <SourceIcon type={event.sourceIcon} />
                        <span className="text-text text-sm">{event.source}</span>
                      </div>
                    </td>
                    <td>
                      <span className={`badge badge-${event.eventClass}`}>{event.eventType}</span>
                    </td>
                    <td className="font-mono text-sm text-text">{event.confidence}</td>
                    <td>
                      <span className={`badge badge-${event.statusClass}`}>{event.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="flex items-center justify-between px-5 py-3 border-t border-surface-border">
              <span className="text-[10px] text-text-muted">Connected to 3 data sources</span>
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] text-text-muted">Last updated: 12:41:03 UTC</span>
                <div className="w-1.5 h-1.5 rounded-full bg-status-success live-pulse"></div>
              </div>
            </div>
          </div>

          {/* Bottom Row: Image of the Day + Explore Universe */}
          <div className="grid grid-cols-2 gap-5">
            {/* Image of the Day */}
            <div className="glass-card overflow-hidden">
              <div className="px-4 pt-3 pb-2">
                <div className="flex items-center gap-1.5">
                  <Telescope className="w-3 h-3 text-gold-dim" />
                  <h3 className="section-title">IMAGE OF THE DAY</h3>
                </div>
              </div>
              <div className="relative mx-3 mb-3 rounded-lg overflow-hidden group">
                <img
                  src="/eagle_nebula.jpg"
                  alt="Eagle Nebula M16"
                  className="w-full h-48 object-cover transition-transform duration-700 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent"></div>
                {/* Navigation arrows */}
                <button className="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/50 border border-white/10 flex items-center justify-center text-white/70 hover:text-white hover:bg-black/70 transition-all">
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/50 border border-white/10 flex items-center justify-center text-white/70 hover:text-white hover:bg-black/70 transition-all">
                  <ChevronRight className="w-4 h-4" />
                </button>
                {/* Info overlay */}
                <div className="absolute bottom-3 left-3 right-3 flex items-end justify-between">
                  <div>
                    <p className="text-white text-sm font-semibold">Eagle Nebula (M16)</p>
                  </div>
                  <span className="text-white/50 text-[10px] font-mono">16.06.2026</span>
                </div>
              </div>
              {/* Dot indicators */}
              <div className="flex items-center justify-center gap-1.5 pb-3">
                <div className="w-1.5 h-1.5 rounded-full bg-status-success"></div>
                <div className="w-1.5 h-1.5 rounded-full bg-text-dim"></div>
                <div className="w-1.5 h-1.5 rounded-full bg-text-dim"></div>
                <div className="w-1.5 h-1.5 rounded-full bg-text-dim"></div>
                <div className="w-1.5 h-1.5 rounded-full bg-text-dim"></div>
              </div>
            </div>

            {/* Explore Universe */}
            <div className="glass-card p-4">
              <div className="flex items-center gap-1.5 mb-4">
                <Rocket className="w-3 h-3 text-gold-dim" />
                <h3 className="section-title">EXPLORE UNIVERSE</h3>
              </div>
              <div className="space-y-3">
                {universeStats.map((stat) => {
                  const Icon = stat.icon;
                  return (
                    <div key={stat.label} className="flex items-center justify-between group cursor-pointer">
                      <div className="flex items-center gap-3">
                        <div className="w-7 h-7 rounded-lg bg-gold/5 border border-gold/10 flex items-center justify-center group-hover:border-gold/25 transition-colors">
                          <Icon className="w-3.5 h-3.5 text-gold-dim group-hover:text-gold transition-colors" />
                        </div>
                        <span className="text-sm text-text group-hover:text-gold transition-colors">{stat.label}</span>
                      </div>
                      <span className="text-sm font-bold font-mono text-text">{stat.value}</span>
                    </div>
                  );
                })}
              </div>
              <button className="w-full mt-4 py-2.5 rounded-lg bg-gold/10 border border-gold/15 text-gold text-sm font-medium hover:bg-gold/15 hover:border-gold/25 transition-all flex items-center justify-center gap-2">
                Explore All
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Right Sidebar Column */}
        <div className="w-[280px] flex-shrink-0 space-y-5">
          {/* Featured Documentary */}
          <div className="glass-card overflow-hidden">
            <div className="flex items-center justify-between px-4 pt-3 pb-2">
              <h3 className="section-title">FEATURED DOCUMENTARY</h3>
              <button className="text-[10px] text-gold-dim hover:text-gold transition-colors">View all</button>
            </div>
            <div className="relative mx-3 mb-3 rounded-lg overflow-hidden group cursor-pointer">
              <img
                src="/moon_documentary.jpg"
                alt="Exploring Exoplanets"
                className="w-full h-44 object-cover transition-transform duration-700 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent"></div>
              <div className="absolute inset-0 flex flex-col justify-between p-4">
                <div className="self-end">
                  {/* intentionally empty top-right */}
                </div>
                <div>
                  <p className="text-white text-lg font-bold leading-tight">Exploring<br/>Exoplanets</p>
                  <p className="text-white/50 text-xs mt-1">Beyond Our Solar System</p>
                </div>
              </div>
              {/* Play button */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white/10 border border-white/20 flex items-center justify-center group-hover:bg-white/20 transition-all backdrop-blur-sm">
                <Play className="w-5 h-5 text-white ml-0.5" fill="white" />
              </div>
            </div>
            <div className="flex items-center justify-between px-4 pb-3 text-[10px] text-text-muted">
              <span className="font-mono">1h 24m</span>
              <span className="font-mono">2026</span>
            </div>
          </div>

          {/* Data Sources */}
          <div className="glass-card p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="section-title">DATA SOURCES</h3>
              <button className="text-[10px] text-gold-dim hover:text-gold transition-colors">View all</button>
            </div>
            <div className="space-y-3">
              {dataSources.map((source) => (
                <div key={source.name} className="flex items-start gap-3 group cursor-pointer">
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
                    style={{ background: `${source.color}15`, border: `1px solid ${source.color}30` }}
                  >
                    <Satellite className="w-4 h-4" style={{ color: source.color }} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm text-text font-medium group-hover:text-gold transition-colors truncate">
                      {source.name}
                      {source.full && (
                        <span className="text-[9px] text-text-muted ml-1 font-normal">({source.full})</span>
                      )}
                    </p>
                    <p className="text-[10px] text-text-muted">{source.type}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Pipeline Status */}
          <div className="glass-card p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="section-title">PIPELINE STATUS</h3>
              <button className="text-[10px] text-gold-dim hover:text-gold transition-colors">View all</button>
            </div>
            <div className="flex items-center justify-between">
              {pipelineSteps.map((step, idx) => (
                <div key={step} className="flex items-center">
                  <div className="flex flex-col items-center gap-1.5">
                    <div className="w-7 h-7 rounded-full bg-status-success/10 border border-status-success/30 flex items-center justify-center">
                      <CheckCircle2 className="w-3.5 h-3.5 text-status-success" />
                    </div>
                    <span className="text-[8px] text-text-muted text-center leading-tight max-w-[50px]">{step}</span>
                  </div>
                  {idx < pipelineSteps.length - 1 && (
                    <div className="w-4 h-px bg-status-success/30 mx-0.5 mb-4"></div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Live Telemetry */}
          <div className="glass-card p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="section-title">LIVE TELEMETRY</h3>
              <button className="text-[10px] text-gold-dim hover:text-gold transition-colors">View all</button>
            </div>
            {/* Telemetry Stats */}
            <div className="grid grid-cols-3 gap-3 mb-3">
              <div>
                <p className="text-[9px] text-text-muted uppercase tracking-wider">Signal Strength</p>
                <p className="text-lg font-bold text-gold font-mono">92%</p>
              </div>
              <div>
                <p className="text-[9px] text-text-muted uppercase tracking-wider">Data Rate</p>
                <p className="text-lg font-bold text-teal font-mono">2.48 <span className="text-[10px] font-normal text-text-muted">Mbps</span></p>
              </div>
              <div>
                <p className="text-[9px] text-text-muted uppercase tracking-wider">System Temp</p>
                <p className="text-lg font-bold text-status-info font-mono">-120°C</p>
              </div>
            </div>
            {/* Mini Chart */}
            <div className="h-24 -mx-1">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={telemetryData}>
                  <XAxis
                    dataKey="time"
                    tick={{ fontSize: 8, fill: '#4d4940' }}
                    axisLine={{ stroke: 'rgba(200,164,92,0.08)' }}
                    tickLine={false}
                    interval={9}
                  />
                  <YAxis
                    tick={{ fontSize: 7, fill: '#4d4940' }}
                    axisLine={false}
                    tickLine={false}
                    domain={[40, 100]}
                    width={30}
                    ticks={[50, 75, 100]}
                    tickFormatter={(v: number) => `${v}%`}
                  />
                  <Line
                    type="monotone"
                    dataKey="signal"
                    stroke="#c8a45c"
                    strokeWidth={1.5}
                    dot={false}
                    animationDuration={1500}
                  />
                  <Line
                    type="monotone"
                    dataKey="dataRate"
                    stroke="#ef4444"
                    strokeWidth={1}
                    dot={false}
                    strokeDasharray="3 3"
                    animationDuration={1500}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="flex items-center gap-1.5 mt-2">
              <div className="w-1.5 h-1.5 rounded-full bg-status-success live-pulse"></div>
              <span className="text-[10px] text-text-muted">Streaming live data from deep space...</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Source Icon Component ──────────────────────────────── */

function SourceIcon({ type }: { type: string }) {
  const colors: Record<string, string> = {
    tess: '#2dd4bf',
    kepler: '#c8a45c',
    btl: '#f59e0b',
  };
  const color = colors[type] || '#7a7569';

  return (
    <div
      className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0"
      style={{ background: `${color}18`, border: `1px solid ${color}30` }}
    >
      {type === 'btl' ? (
        <Radio className="w-3 h-3" style={{ color }} />
      ) : (
        <Satellite className="w-3 h-3" style={{ color }} />
      )}
    </div>
  );
}
