import React, { useState, useEffect, useRef } from 'react';
import { GlassPanel, GlassPanelBody } from '../components/GlassPanel';
import { ProgressBar, LogViewer, StatusBadge } from '../components/UIComponents';
import { GlowButton, SecondaryButton, GhostButton } from '../components/Buttons';
import { Play, Square, Trash2, Copy, Download } from 'lucide-react';
import api from '../services/api';
import './RunTab.css';

const RunTab = () => {
  const [status, setStatus] = useState({
    running: false,
    progress: 0,
    stage: 'idle',
    video_path: null,
    output_dir: null
  });
  const [logs, setLogs] = useState([]);
  const [settings, setSettings] = useState(null);
  const logStreamRef = useRef(null);

  useEffect(() => {
    loadStatus();
    loadSettings();
    
    // Poll status every 2 seconds
    const interval = setInterval(loadStatus, 2000);
    
    return () => {
      clearInterval(interval);
      if (logStreamRef.current) {
        logStreamRef.current();
      }
    };
  }, []);

  const loadStatus = async () => {
    try {
      const data = await api.getPipelineStatus();
      setStatus(data);
    } catch (error) {
      console.error('Failed to load status:', error);
    }
  };

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      setSettings(data);
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const startPipeline = async () => {
    if (!settings || !settings.input.output_dir) {
      alert('Please configure settings first');
      return;
    }

    // Get video path from settings or prompt
    const videoPath = prompt('Enter video path:');
    if (!videoPath) return;

    try {
      await api.startPipeline(
        videoPath,
        settings.input.output_dir,
        settings.input.use_cache
      );
      
      // Start log streaming
      if (logStreamRef.current) {
        logStreamRef.current();
      }
      
      logStreamRef.current = api.streamLogs((log) => {
        setLogs(prev => [...prev, log]);
      });
      
      loadStatus();
    } catch (error) {
      alert('Failed to start pipeline: ' + error.message);
    }
  };

  const stopPipeline = async () => {
    try {
      await api.stopPipeline();
      if (logStreamRef.current) {
        logStreamRef.current();
        logStreamRef.current = null;
      }
      loadStatus();
    } catch (error) {
      alert('Failed to stop pipeline: ' + error.message);
    }
  };

  const clearLogs = () => {
    setLogs([]);
  };

  const copyLogs = () => {
    const logText = logs.map(log => `[${log.timestamp}] ${log.level}: ${log.message}`).join('\n');
    navigator.clipboard.writeText(logText);
    alert('Logs copied to clipboard!');
  };

  const saveLogs = () => {
    const logText = logs.map(log => `[${log.timestamp}] ${log.level}: ${log.message}`).join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `asfs-logs-${new Date().toISOString()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getStatusBadgeType = () => {
    if (status.stage === 'completed') return 'success';
    if (status.stage === 'error') return 'error';
    if (status.running) return 'processing';
    return 'info';
  };

  return (
    <div className="run-tab">
      <div className="page-header">
        <h1 className="page-title">Run & Monitor</h1>
        <p className="page-description">
          Execute pipeline and monitor progress in real-time
        </p>
      </div>

      <GlassPanel style={{ marginBottom: 'var(--spacing-xl)' }}>
        <GlassPanelBody>
          <div className="status-section">
            <div className="status-info">
              <h3 style={{ marginBottom: 'var(--spacing-md)' }}>Pipeline Status</h3>
              <StatusBadge status={getStatusBadgeType()}>
                {status.stage}
              </StatusBadge>
              {status.video_path && (
                <div style={{ marginTop: 'var(--spacing-md)', fontSize: '14px', color: 'var(--text-secondary)' }}>
                  <div>Video: {status.video_path}</div>
                  <div>Output: {status.output_dir}</div>
                </div>
              )}
            </div>
            
            <div className="status-controls">
              {!status.running ? (
                <GlowButton onClick={startPipeline}>
                  <Play size={16} />
                  Start Pipeline
                </GlowButton>
              ) : (
                <SecondaryButton onClick={stopPipeline}>
                  <Square size={16} />
                  Stop Pipeline
                </SecondaryButton>
              )}
              <GhostButton onClick={clearLogs}>
                <Trash2 size={16} />
                Clear Logs
              </GhostButton>
            </div>
          </div>

          {status.running && (
            <div style={{ marginTop: 'var(--spacing-xl)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--spacing-sm)' }}>
                <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Progress</span>
                <span style={{ fontSize: '14px', color: 'var(--accent-primary)', fontWeight: 500 }}>
                  {status.progress}%
                </span>
              </div>
              <ProgressBar value={status.progress} max={100} />
            </div>
          )}
        </GlassPanelBody>
      </GlassPanel>

      <GlassPanel>
        <GlassPanelBody>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-lg)' }}>
            <h3>Live Logs</h3>
            <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
              <GhostButton size="sm" onClick={copyLogs}>
                <Copy size={14} />
                Copy
              </GhostButton>
              <GhostButton size="sm" onClick={saveLogs}>
                <Download size={14} />
                Save
              </GhostButton>
            </div>
          </div>
          
          <LogViewer logs={logs} />
        </GlassPanelBody>
      </GlassPanel>
    </div>
  );
};

export default RunTab;
