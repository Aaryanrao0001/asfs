import React, { useState, useEffect, useRef } from 'react';
import { GlassPanel, GlassPanelBody } from '../components/GlassPanel';
import { ProgressBar, LogViewer, StatusBadge } from '../components/UIComponents';
import { GlowButton, SecondaryButton, GhostButton } from '../components/Buttons';
import { Play, Square, Trash2, Copy, Download, AlertCircle } from 'lucide-react';
import { useToast } from '../components/Toast';
import api from '../services/api';
import './RunTab.css';

const RunTab = () => {
  const [status, setStatus] = useState({
    running: false,
    progress: 0,
    stage: 'idle',
    video_path: null,
    output_dir: null,
    error: null
  });
  const [logs, setLogs] = useState([]);
  const [settings, setSettings] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);
  const wsCleanupRef = useRef(null);
  const toast = useToast();

  useEffect(() => {
    loadStatus();
    loadSettings();
    
    // Poll status every 2 seconds when pipeline is running
    let interval = null;
    if (status.running) {
      interval = setInterval(loadStatus, 2000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
      if (wsCleanupRef.current) {
        wsCleanupRef.current();
      }
    };
  }, [status.running]);

  // Connect WebSocket when pipeline starts
  useEffect(() => {
    if (status.running && !wsCleanupRef.current) {
      connectWebSocket();
    } else if (!status.running && wsCleanupRef.current) {
      wsCleanupRef.current();
      wsCleanupRef.current = null;
    }
  }, [status.running]);

  const loadStatus = async () => {
    try {
      const data = await api.getPipelineStatus();
      setStatus(data);
      
      // Show error toast if pipeline errored
      if (data.stage === 'error' && data.error) {
        toast.error('Pipeline error: ' + data.error);
      }
    } catch (error) {
      console.error('Failed to load status:', error);
    }
  };

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      setSettings(data);
      validateSettings(data);
    } catch (error) {
      console.error('Failed to load settings:', error);
      toast.error('Failed to load settings');
    }
  };

  const validateSettings = (settingsData) => {
    const errors = [];
    
    if (!settingsData) {
      errors.push('Settings not loaded');
      setValidationErrors(errors);
      return;
    }

    // Check if video is uploaded
    if (!settingsData.input?.video_path) {
      errors.push('No video uploaded (go to Input tab)');
    }

    // Check if output directory is set
    if (!settingsData.input?.output_dir) {
      errors.push('Output directory not set (go to Input tab)');
    }

    // Check if at least one platform is selected
    const platforms = settingsData.upload?.platforms || {};
    const hasSelectedPlatform = Object.values(platforms).some(Boolean);
    if (!hasSelectedPlatform) {
      errors.push('No upload platforms selected (go to Upload tab)');
    }

    setValidationErrors(errors);
  };

  const connectWebSocket = () => {
    try {
      const cleanup = api.connectWebSocket((log) => {
        setLogs(prev => [...prev, log]);
      });
      wsCleanupRef.current = cleanup;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      toast.error('Failed to connect to log stream');
    }
  };

  const startPipeline = async () => {
    // Reload settings to ensure we have latest
    await loadSettings();
    
    if (validationErrors.length > 0) {
      toast.error('Cannot start pipeline: ' + validationErrors[0]);
      return;
    }

    if (!settings) {
      toast.error('Settings not loaded');
      return;
    }

    const videoPath = settings.input.video_path;
    const outputDir = settings.input.output_dir;
    const useCache = settings.input.use_cache;

    try {
      toast.info('Starting pipeline...');
      
      await api.startPipeline(videoPath, outputDir, useCache);
      
      toast.success('Pipeline started successfully');
      
      // Clear logs and start fresh
      setLogs([]);
      
      // Load status immediately
      await loadStatus();
      
    } catch (error) {
      console.error('Failed to start pipeline:', error);
      toast.error('Failed to start pipeline: ' + error.message);
    }
  };

  const stopPipeline = async () => {
    try {
      await api.stopPipeline();
      toast.info('Pipeline stop requested');
      
      // Disconnect WebSocket
      if (wsCleanupRef.current) {
        wsCleanupRef.current();
        wsCleanupRef.current = null;
      }
      
      // Load status
      await loadStatus();
    } catch (error) {
      console.error('Failed to stop pipeline:', error);
      toast.error('Failed to stop pipeline: ' + error.message);
    }
  };

  const clearLogs = () => {
    setLogs([]);
    toast.info('Logs cleared');
  };

  const copyLogs = () => {
    const logText = logs.map(log => `[${log.timestamp}] ${log.level}: ${log.message}`).join('\n');
    navigator.clipboard.writeText(logText);
    toast.success('Logs copied to clipboard!');
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
    toast.success('Logs saved');
  };

  const getStatusBadgeType = () => {
    if (status.stage === 'completed') return 'success';
    if (status.stage === 'error') return 'error';
    if (status.running) return 'processing';
    return 'idle';
  };

  const getStageLabel = (stage) => {
    const labels = {
      'idle': 'Idle',
      'starting': 'Starting...',
      'transcribing': 'Transcribing Audio',
      'analyzing': 'Analyzing Content',
      'extracting': 'Extracting Clips',
      'uploading': 'Uploading to Platforms',
      'completed': 'Completed',
      'stopped': 'Stopped',
      'stopping': 'Stopping...',
      'error': 'Error'
    };
    return labels[stage] || stage;
  };

  return (
    <div className="run-tab">
      <div className="page-header">
        <h1 className="page-title">Run & Monitor</h1>
        <p className="page-description">
          Execute pipeline and monitor progress in real-time
        </p>
      </div>

      {/* Validation Warnings */}
      {validationErrors.length > 0 && !status.running && (
        <div style={{ 
          marginBottom: 'var(--spacing-xl)',
          padding: 'var(--spacing-lg)',
          background: 'rgba(255, 193, 7, 0.1)',
          border: '1px solid rgba(255, 193, 7, 0.3)',
          borderRadius: 'var(--radius-lg)',
          display: 'flex',
          gap: 'var(--spacing-md)',
          alignItems: 'flex-start'
        }}>
          <AlertCircle size={24} style={{ color: '#ffc107', flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h4 style={{ color: '#ffc107', marginBottom: 'var(--spacing-sm)' }}>
              Configuration Required
            </h4>
            <ul style={{ 
              margin: 0, 
              paddingLeft: '20px',
              color: 'var(--text-secondary)',
              fontSize: '14px',
              lineHeight: '1.6'
            }}>
              {validationErrors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <GlassPanel style={{ marginBottom: 'var(--spacing-xl)' }}>
        <GlassPanelBody>
          <div className="status-section">
            <div className="status-info">
              <h3 style={{ marginBottom: 'var(--spacing-md)' }}>Pipeline Status</h3>
              <StatusBadge status={getStatusBadgeType()}>
                {getStageLabel(status.stage)}
              </StatusBadge>
              {settings && settings.input?.video_path && (
                <div style={{ marginTop: 'var(--spacing-md)', fontSize: '13px', color: 'var(--text-secondary)' }}>
                  <div style={{ marginBottom: '4px' }}>
                    <span style={{ color: 'var(--text-tertiary)' }}>Video:</span> {settings.input.video_info?.filename || 'Unknown'}
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-tertiary)' }}>Output:</span> {settings.input.output_dir}
                  </div>
                </div>
              )}
              {status.error && (
                <div style={{ 
                  marginTop: 'var(--spacing-md)', 
                  padding: 'var(--spacing-sm)',
                  background: 'rgba(255, 82, 82, 0.1)',
                  border: '1px solid rgba(255, 82, 82, 0.3)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '13px',
                  color: '#ff5252'
                }}>
                  {status.error}
                </div>
              )}
            </div>
            
            <div className="status-controls">
              {!status.running ? (
                <GlowButton 
                  onClick={startPipeline}
                  disabled={validationErrors.length > 0}
                >
                  <Play size={16} />
                  Start Pipeline
                </GlowButton>
              ) : (
                <SecondaryButton onClick={stopPipeline}>
                  <Square size={16} />
                  Stop Pipeline
                </SecondaryButton>
              )}
              <GhostButton onClick={clearLogs} disabled={logs.length === 0}>
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
            <div>
              <h3 style={{ marginBottom: '4px' }}>Live Logs</h3>
              <span style={{ fontSize: '13px', color: 'var(--text-tertiary)' }}>
                {logs.length} entries
              </span>
            </div>
            <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
              <GhostButton size="sm" onClick={copyLogs} disabled={logs.length === 0}>
                <Copy size={14} />
                Copy
              </GhostButton>
              <GhostButton size="sm" onClick={saveLogs} disabled={logs.length === 0}>
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
