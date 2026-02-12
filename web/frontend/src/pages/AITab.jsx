import React, { useState, useEffect, useRef } from 'react';
import { GlassPanel, GlassPanelBody } from '../components/GlassPanel';
import { TextInput } from '../components/FormInputs';
import { GlowButton, SecondaryButton } from '../components/Buttons';
import { StatusBadge } from '../components/UIComponents';
import { Brain, Zap, Play, Square, RefreshCw, Download } from 'lucide-react';
import { useToast } from '../components/Toast';
import api from '../services/api';

const AITab = () => {
  const [settings, setSettings] = useState({
    model_name: 'gpt-4o',
    api_endpoint: '',
    scoring_threshold: 7.0,
    max_clips: 10,
    segment_duration: 60
  });
  const [ollamaStatus, setOllamaStatus] = useState('stopped');
  const [ollamaAvailable, setOllamaAvailable] = useState(false);
  const [ollamaModels, setOllamaModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [loading, setLoading] = useState(false);
  const toast = useToast();
  const saveTimeoutRef = useRef(null);

  useEffect(() => {
    loadSettings();
    checkOllamaStatus();
    
    // Poll Ollama status every 10 seconds
    const interval = setInterval(checkOllamaStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  // Auto-save settings with debounce
  useEffect(() => {
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }
    
    saveTimeoutRef.current = setTimeout(() => {
      saveSettings();
    }, 500);

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [settings]);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      if (data.ai) {
        setSettings(data.ai);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
      toast.error('Failed to load settings');
    }
  };

  const saveSettings = async () => {
    try {
      await api.saveSettings('ai', settings);
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const checkOllamaStatus = async () => {
    try {
      const response = await api.getOllamaStatus();
      setOllamaStatus(response.status);
      setOllamaAvailable(response.available);
      
      // If running, fetch models
      if (response.status === 'running') {
        fetchOllamaModels();
      }
    } catch (error) {
      console.error('Failed to check Ollama status:', error);
      setOllamaStatus('stopped');
      setOllamaAvailable(false);
    }
  };

  const fetchOllamaModels = async () => {
    try {
      const response = await api.listOllamaModels();
      if (response.success && response.models) {
        setOllamaModels(response.models);
      }
    } catch (error) {
      console.error('Failed to fetch Ollama models:', error);
    }
  };

  const handleStartOllama = async () => {
    setLoading(true);
    try {
      await api.startOllama();
      toast.success('Ollama server start requested');
      
      // Wait a bit then check status
      setTimeout(checkOllamaStatus, 2000);
    } catch (error) {
      toast.error('Failed to start Ollama: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStopOllama = async () => {
    setLoading(true);
    try {
      await api.stopOllama();
      toast.success('Ollama server stop requested');
      
      // Wait a bit then check status
      setTimeout(checkOllamaStatus, 2000);
    } catch (error) {
      toast.error('Failed to stop Ollama: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadModel = async () => {
    if (!selectedModel) {
      toast.error('Please enter a model name');
      return;
    }

    setLoading(true);
    toast.info('Loading model... This may take a few minutes');
    
    try {
      const response = await api.loadOllamaModel(selectedModel);
      if (response.success) {
        toast.success('Model loaded successfully!');
        fetchOllamaModels();
      } else {
        toast.error('Failed to load model: ' + (response.error || 'Unknown error'));
      }
    } catch (error) {
      toast.error('Failed to load model: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-tab">
      <div className="page-header">
        <h1 className="page-title">AI & Model Configuration</h1>
        <p className="page-description">
          Configure AI model and scoring parameters for content analysis
        </p>
      </div>

      <div style={{ maxWidth: '1000px', display: 'flex', flexDirection: 'column', gap: 'var(--spacing-xl)' }}>
        {/* Ollama Server Control */}
        <GlassPanel>
          <GlassPanelBody>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-lg)' }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                <Brain size={24} style={{ color: 'var(--accent-primary)' }} />
                Ollama Local LLM Server
              </h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)' }}>
                <StatusBadge 
                  status={ollamaStatus === 'running' ? 'success' : 'idle'} 
                  label={ollamaStatus === 'running' ? 'Running' : 'Stopped'} 
                />
                <SecondaryButton onClick={checkOllamaStatus} disabled={loading}>
                  <RefreshCw size={16} />
                </SecondaryButton>
              </div>
            </div>

            {!ollamaAvailable && (
              <div style={{ 
                padding: 'var(--spacing-md)', 
                background: 'rgba(255, 193, 7, 0.1)', 
                border: '1px solid rgba(255, 193, 7, 0.3)',
                borderRadius: 'var(--radius-md)',
                marginBottom: 'var(--spacing-lg)',
                fontSize: '14px',
                color: 'var(--text-secondary)'
              }}>
                Ollama is not installed or not in PATH. Install from ollama.ai to use local LLM models.
              </div>
            )}

            <div style={{ display: 'flex', gap: 'var(--spacing-md)', marginBottom: 'var(--spacing-lg)' }}>
              <GlowButton 
                onClick={handleStartOllama} 
                disabled={loading || !ollamaAvailable || ollamaStatus === 'running'}
              >
                <Play size={16} />
                Start Server
              </GlowButton>
              <SecondaryButton 
                onClick={handleStopOllama}
                disabled={loading || !ollamaAvailable || ollamaStatus !== 'running'}
              >
                <Square size={16} />
                Stop Server
              </SecondaryButton>
            </div>

            {ollamaStatus === 'running' && (
              <>
                <div style={{ marginTop: 'var(--spacing-xl)' }}>
                  <label className="form-label">Load/Pull Model</label>
                  <div style={{ display: 'flex', gap: 'var(--spacing-md)', marginTop: 'var(--spacing-sm)' }}>
                    <TextInput
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      placeholder="e.g., llama2, mistral, codellama"
                      helper="Enter model name to download and use"
                    />
                    <SecondaryButton onClick={handleLoadModel} disabled={loading}>
                      <Download size={16} />
                      Load
                    </SecondaryButton>
                  </div>
                </div>

                {ollamaModels.length > 0 && (
                  <div style={{ marginTop: 'var(--spacing-lg)' }}>
                    <label className="form-label">Available Models</label>
                    <div style={{ 
                      marginTop: 'var(--spacing-sm)',
                      padding: 'var(--spacing-md)',
                      background: 'rgba(11, 36, 28, 0.4)',
                      border: '1px solid var(--glass-border)',
                      borderRadius: 'var(--radius-md)',
                      maxHeight: '200px',
                      overflowY: 'auto'
                    }}>
                      {ollamaModels.map((model, index) => (
                        <div 
                          key={index}
                          style={{ 
                            padding: 'var(--spacing-sm)',
                            color: 'var(--text-secondary)',
                            fontSize: '14px',
                            fontFamily: 'monospace'
                          }}
                        >
                          {model.name}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </GlassPanelBody>
        </GlassPanel>

        {/* GitHub Models API Settings */}
        <GlassPanel>
          <GlassPanelBody>
            <h3 style={{ marginBottom: 'var(--spacing-lg)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Zap size={24} style={{ color: 'var(--accent-primary)' }} />
              GitHub Models API (Primary)
            </h3>
            
            <TextInput
              label="Model Name"
              value={settings.model_name}
              onChange={(e) => setSettings({ ...settings, model_name: e.target.value })}
              helper="GitHub Models API model (e.g., gpt-4o, gpt-4o-mini)"
            />

            <TextInput
              label="API Endpoint (Optional)"
              value={settings.api_endpoint}
              onChange={(e) => setSettings({ ...settings, api_endpoint: e.target.value })}
              helper="Leave empty for default GitHub Models endpoint"
            />
          </GlassPanelBody>
        </GlassPanel>

        {/* Scoring Parameters */}
        <GlassPanel>
          <GlassPanelBody>
            <h3 style={{ marginBottom: 'var(--spacing-lg)' }}>Scoring & Analysis Parameters</h3>

            <div style={{ marginTop: 'var(--spacing-lg)' }}>
              <label className="form-label">
                Scoring Threshold: {settings.scoring_threshold}
              </label>
              <input
                type="range"
                min="0"
                max="10"
                step="0.5"
                value={settings.scoring_threshold}
                onChange={(e) => setSettings({ ...settings, scoring_threshold: parseFloat(e.target.value) })}
                style={{ width: '100%', marginTop: 'var(--spacing-sm)' }}
              />
              <div className="form-helper">
                Minimum virality score (0-10) required for clips
              </div>
            </div>

            <div style={{ marginTop: 'var(--spacing-xl)' }}>
              <label className="form-label">
                Max Clips Per Video: {settings.max_clips}
              </label>
              <input
                type="range"
                min="1"
                max="50"
                step="1"
                value={settings.max_clips}
                onChange={(e) => setSettings({ ...settings, max_clips: parseInt(e.target.value) })}
                style={{ width: '100%', marginTop: 'var(--spacing-sm)' }}
              />
              <div className="form-helper">
                Maximum number of clips to extract per video
              </div>
            </div>

            <TextInput
              label="Segment Duration (seconds)"
              type="number"
              value={settings.segment_duration}
              onChange={(e) => setSettings({ ...settings, segment_duration: parseInt(e.target.value) })}
              helper="Duration of each analyzed segment"
            />

            <div style={{ 
              marginTop: 'var(--spacing-lg)',
              padding: 'var(--spacing-sm)',
              fontSize: '13px',
              color: 'var(--text-tertiary)',
              fontStyle: 'italic'
            }}>
              Settings are automatically saved
            </div>
          </GlassPanelBody>
        </GlassPanel>
      </div>
    </div>
  );
};

export default AITab;
