import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import InputTab from './pages/InputTab';
import AITab from './pages/AITab';
import MetadataTab from './pages/MetadataTab';
import UploadTab from './pages/UploadTab';
import VideosTab from './pages/VideosTab';
import RunTab from './pages/RunTab';
import './styles/globals.css';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/input" replace />} />
          <Route path="/input" element={<InputTab />} />
          <Route path="/ai" element={<AITab />} />
          <Route path="/metadata" element={<MetadataTab />} />
          <Route path="/upload" element={<UploadTab />} />
          <Route path="/videos" element={<VideosTab />} />
          <Route path="/run" element={<RunTab />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
