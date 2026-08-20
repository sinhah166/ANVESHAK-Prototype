import { useState } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Zap, Globe2, Radio, Brain, Database,
  Activity, FlaskConical, Settings, Search, Bell, ChevronRight,
  Satellite, CalendarClock, ArrowUpRight, Gauge, HardDrive, Timer, Cpu
} from 'lucide-react';

const sidebarNavItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/live-events', icon: Zap, label: 'Live Events' },
  { path: '/candidates', icon: Globe2, label: 'Exoplanet Analysis' },
  { path: '/radio-signals', icon: Radio, label: 'Radio Signals' },
  { path: '/ai-analysis', icon: Brain, label: 'AI Analysis' },
  { path: '/sources', icon: Database, label: 'Data Sources' },
  { path: '/pipeline', icon: Activity, label: 'Pipeline Monitor' },
  { path: '/research', icon: FlaskConical, label: 'Research' },
  { path: '/system', icon: Settings, label: 'Settings' },
];

const topNavItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/live-events', label: 'Live Events' },
  { path: '/candidates', label: 'Exoplanets' },
  { path: '/radio-signals', label: 'Radio Signals' },
  { path: '/ai-analysis', label: 'AI Analysis ▾' },
  { path: '/sources', label: 'Data Sources' },
  { path: '/pipeline', label: 'Pipeline' },
  { path: '/research', label: 'Research' },
];

export default function Layout() {
  const location = useLocation();
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="flex flex-col h-screen w-screen bg-bg overflow-hidden">
      {/* Top Navbar */}
      <header className="top-navbar flex items-center justify-between px-5 h-[52px] flex-shrink-0 z-30">
        <div className="flex items-center gap-8">
          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gold/10 border border-gold/20 flex items-center justify-center">
              <Satellite className="w-4 h-4 text-gold" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-text tracking-wide leading-none">ANVESHAK</h1>
              <p className="text-[9px] text-gold-dim italic tracking-widest">Cosmic Sleuths</p>
            </div>
          </div>

          {/* Top Nav Links */}
          <nav className="hidden lg:flex items-center gap-1">
            {topNavItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `px-3 py-1.5 text-[13px] rounded-md transition-all duration-200 ${
                    isActive
                      ? 'text-gold font-medium bg-gold/8 border border-gold/15'
                      : 'text-text-muted hover:text-text hover:bg-white/3'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted" />
            <input
              type="text"
              placeholder="Search events, sources, planets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-64 pl-9 pr-4 py-1.5 text-xs bg-surface border border-surface-border rounded-lg text-text placeholder-text-dim focus:outline-none focus:border-gold/30 transition-colors"
            />
          </div>
          <button className="relative p-2 rounded-lg hover:bg-surface-light transition-colors">
            <Bell className="w-4 h-4 text-text-muted" />
            <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-status-danger rounded-full"></span>
          </button>
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gold/30 to-copper/30 border border-gold/20 flex items-center justify-center">
            <span className="text-xs font-semibold text-gold">BS</span>
          </div>
        </div>
      </header>

      {/* Main Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="sidebar w-[200px] flex-shrink-0 flex flex-col z-20">
          {/* Live System Status */}
          <div className="px-4 pt-4 pb-3">
            <div className="flex items-center gap-1.5 mb-1">
              <div className="w-1.5 h-1.5 rounded-full bg-status-success live-pulse"></div>
              <span className="text-[10px] font-medium uppercase tracking-wider text-text-muted">Live System</span>
            </div>
            <p className="text-[11px] text-status-success font-medium">All Systems Nominal</p>
          </div>

          {/* Satellite Visualization */}
          <div className="px-4 py-3">
            <div className="w-full h-28 rounded-xl bg-surface border border-surface-border overflow-hidden relative flex items-center justify-center">
              <div className="absolute inset-0 bg-gradient-to-br from-gold/5 to-transparent"></div>
              <svg viewBox="0 0 120 100" className="w-24 h-20 relative z-10" fill="none">
                {/* Satellite body */}
                <rect x="45" y="35" width="30" height="20" rx="3" fill="rgba(200,164,92,0.15)" stroke="rgba(200,164,92,0.4)" strokeWidth="1"/>
                {/* Solar panels */}
                <rect x="8" y="38" width="35" height="14" rx="2" fill="rgba(200,164,92,0.08)" stroke="rgba(200,164,92,0.25)" strokeWidth="0.8"/>
                <rect x="77" y="38" width="35" height="14" rx="2" fill="rgba(200,164,92,0.08)" stroke="rgba(200,164,92,0.25)" strokeWidth="0.8"/>
                {/* Panel lines */}
                <line x1="19" y1="38" x2="19" y2="52" stroke="rgba(200,164,92,0.15)" strokeWidth="0.5"/>
                <line x1="30" y1="38" x2="30" y2="52" stroke="rgba(200,164,92,0.15)" strokeWidth="0.5"/>
                <line x1="88" y1="38" x2="88" y2="52" stroke="rgba(200,164,92,0.15)" strokeWidth="0.5"/>
                <line x1="99" y1="38" x2="99" y2="52" stroke="rgba(200,164,92,0.15)" strokeWidth="0.5"/>
                {/* Antenna */}
                <line x1="60" y1="35" x2="60" y2="22" stroke="rgba(200,164,92,0.4)" strokeWidth="1"/>
                <circle cx="60" cy="20" r="3" fill="rgba(200,164,92,0.2)" stroke="rgba(200,164,92,0.4)" strokeWidth="0.8"/>
                {/* Signal waves */}
                <path d="M 52 18 Q 48 12 52 6" stroke="rgba(200,164,92,0.2)" strokeWidth="0.6" fill="none"/>
                <path d="M 68 18 Q 72 12 68 6" stroke="rgba(200,164,92,0.2)" strokeWidth="0.6" fill="none"/>
                {/* Orbit ring */}
                <ellipse cx="60" cy="65" rx="45" ry="8" stroke="rgba(200,164,92,0.1)" strokeWidth="0.5" fill="none" strokeDasharray="3 3"/>
              </svg>
              {/* Glow effect */}
              <div className="absolute bottom-2 left-1/2 -translate-x-1/2 w-16 h-4 bg-gold/10 rounded-full blur-xl"></div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="px-4 pb-3 flex gap-3">
            <div>
              <p className="text-[9px] text-text-muted uppercase tracking-wider">Data Sources</p>
              <p className="text-sm font-semibold text-text">3 <span className="text-status-success text-[9px]">Active</span></p>
            </div>
            <div>
              <p className="text-[9px] text-text-muted uppercase tracking-wider">Pipeline Status</p>
              <p className="text-sm font-semibold text-text">Nominal</p>
            </div>
          </div>

          <div className="px-4 pb-4">
            <p className="text-[9px] text-text-muted uppercase tracking-wider">Uptime</p>
            <p className="text-sm font-semibold text-text font-mono">12d 4h 32m</p>
          </div>

          {/* Separator */}
          <div className="mx-4 h-px bg-gradient-to-r from-transparent via-gold/10 to-transparent"></div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto">
            {sidebarNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = item.path === '/'
                ? location.pathname === '/'
                : location.pathname.startsWith(item.path);
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={`nav-link ${isActive ? 'active' : ''}`}
                >
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>

          {/* Maintenance */}
          <div className="px-4 py-3 border-t border-surface-border">
            <div className="flex items-center gap-1.5 mb-1.5">
              <CalendarClock className="w-3 h-3 text-text-muted" />
              <span className="text-[9px] text-text-muted uppercase tracking-wider font-medium">Next Scheduled Maintenance</span>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[11px] text-text font-medium flex items-center gap-1">
                  <CalendarClock className="w-3 h-3 text-text-muted" />
                  JUN 22, 02:00 UTC
                </p>
                <p className="text-[9px] text-text-muted mt-0.5">System update<br/>& cache refresh</p>
              </div>
              <ChevronRight className="w-4 h-4 text-text-muted" />
            </div>
          </div>

          {/* Footer */}
          <div className="px-4 py-2 border-t border-surface-border">
            <p className="text-[9px] text-text-dim">© 2026 Anveshak Platform</p>
            <p className="text-[8px] text-text-dim">All rights reserved</p>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto overflow-x-hidden p-5">
          <Outlet />
        </main>
      </div>

      {/* Bottom Status Bar */}
      <footer className="status-bar flex items-center justify-between px-5 h-[40px] flex-shrink-0 z-30">
        <StatusBarItem
          icon={<Zap className="w-3 h-3" />}
          label="EVENTS TODAY"
          value="128"
          change="+18.4%"
          changeColor="text-status-success"
        />
        <StatusBarSep />
        <StatusBarItem
          icon={<HardDrive className="w-3 h-3" />}
          label="DATA PROCESSED"
          value="3.42 TB"
        />
        <StatusBarSep />
        <StatusBarItem
          icon={<Cpu className="w-3 h-3" />}
          label="AI MODELS"
          value="Active"
          valueColor="text-status-success"
        />
        <StatusBarSep />
        <StatusBarItem
          icon={<Database className="w-3 h-3" />}
          label="STORAGE USED"
          value="2.48 TB / 10 TB"
        />
        <StatusBarSep />
        <StatusBarItem
          icon={<Gauge className="w-3 h-3" />}
          label="ACCURACY (AI MODEL)"
          value="96.7%"
        />
        <StatusBarSep />
        <StatusBarItem
          icon={<Timer className="w-3 h-3" />}
          label="LATENCY"
          value="1.24 sec"
        />
      </footer>
    </div>
  );
}

function StatusBarItem({
  icon,
  label,
  value,
  change,
  changeColor,
  valueColor,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  change?: string;
  changeColor?: string;
  valueColor?: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-text-muted">{icon}</span>
      <span className="text-[9px] text-text-muted uppercase tracking-wider">{label}</span>
      <span className={`text-sm font-semibold font-mono ${valueColor || 'text-text'}`}>{value}</span>
      {change && (
        <span className={`text-[10px] font-medium ${changeColor || 'text-text-muted'} flex items-center gap-0.5`}>
          <ArrowUpRight className="w-2.5 h-2.5" />
          {change}
        </span>
      )}
    </div>
  );
}

function StatusBarSep() {
  return <div className="w-px h-5 bg-surface-border"></div>;
}
