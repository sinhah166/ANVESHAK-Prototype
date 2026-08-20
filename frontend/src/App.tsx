import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Overview from './pages/Overview';
import CandidatesList from './pages/CandidatesList';
import CandidateDetail from './pages/CandidateDetail';
import PipelinePage from './pages/PipelinePage';
import SourcesPage from './pages/SourcesPage';
import SystemPage from './pages/SystemPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Overview />} />
        <Route path="candidates" element={<CandidatesList />} />
        <Route path="candidates/:id" element={<CandidateDetail />} />
        <Route path="pipeline" element={<PipelinePage />} />
        <Route path="sources" element={<SourcesPage />} />
        <Route path="system" element={<SystemPage />} />
        {/* Aliased routes for sidebar navigation */}
        <Route path="live-events" element={<Overview />} />
        <Route path="radio-signals" element={<Overview />} />
        <Route path="ai-analysis" element={<Overview />} />
        <Route path="research" element={<Overview />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default App;
