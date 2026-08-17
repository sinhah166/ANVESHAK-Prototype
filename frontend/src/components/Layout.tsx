import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { 
  Telescope, 
  Activity, 
  List, 
  Server, 
  Cpu,
  RadioTower,
  Play
} from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';

const Layout = () => {
  const { isConnected } = useWebSocket();
  const [isDemoRunning, setIsDemoRunning] = React.useState(false);

  const runDemo = async () => {
    setIsDemoRunning(true);
    try {
      await fetch('/api/pipeline/demo', { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
    setTimeout(() => setIsDemoRunning(false), 2000);
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      
      {/* Sidebar */}
      <aside className="w-64 border-r border-white/5 flex flex-col bg-surface/30">
        
        {/* Brand */}
        <div className="p-6 border-b border-white/5">
          <div className="flex items-center gap-3 text-primary mb-1">
            <Telescope size={28} className="stroke-[1.5]" />
            <h1 className="text-2xl font-bold tracking-wider">ANVESHAK</h1>
          </div>
          <p className="text-xs text-text_muted font-mono tracking-wide uppercase">
            Autonomous Signal Pipeline
          </p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          <NavLink to="/" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
            <Activity size={20} /> Overview
          </NavLink>
          <NavLink to="/candidates" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
            <List size={20} /> Candidates
          </NavLink>
          <NavLink to="/pipeline" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
            <Cpu size={20} /> Pipeline Status
          </NavLink>
          <NavLink to="/sources" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
            <RadioTower size={20} /> Data Sources
          </NavLink>
          <NavLink to="/system" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
            <Server size={20} /> System Health
          </NavLink>
        </nav>

        {/* Demo Button */}
        <div className="p-4 border-t border-white/5">
          <button 
            onClick={runDemo}
            disabled={isDemoRunning}
            className="w-full btn-primary flex items-center justify-center gap-2 group"
          >
            <Play size={18} className={`fill-current ${isDemoRunning ? 'animate-pulse' : 'group-hover:scale-110 transition-transform'}`} />
            {isDemoRunning ? 'Starting...' : 'RUN DEMO PIPELINE'}
          </button>
        </div>

        {/* Status */}
        <div className="p-4 border-t border-white/5 bg-surface/50 text-sm font-mono flex items-center justify-between">
          <span className="text-text_muted">STREAM</span>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-success animate-pulse' : 'bg-danger'}`}></span>
            <span className={isConnected ? 'text-success' : 'text-danger'}>
              {isConnected ? 'LIVE' : 'OFFLINE'}
            </span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Glow effects in background */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-[100px] -z-10 pointer-events-none"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-accent/5 rounded-full blur-[100px] -z-10 pointer-events-none"></div>
        
        <div className="flex-1 overflow-y-auto p-8">
          <Outlet />
        </div>
      </main>

    </div>
  );
};

export default Layout;
