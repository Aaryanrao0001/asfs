import React, { useState, useEffect } from 'react';
import { GlassPanel, GlassPanelBody } from '../components/GlassPanel';
import { TextInput } from '../components/FormInputs';
import { GlowButton } from '../components/Buttons';
import { Brain, Zap } from 'lucide-react';
import api from '../services/api';

const AITab = () => {
  const [settings, setSettings] = useState({
    model_name: 'gpt-4o',
    api_endpoint: '',
    scoring_threshold: 7.0,
    max_clips: 10,
    segment_duration: 60
  });

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      if (data.ai) {
        setSettings(data.ai);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const handleSave = async () => {
    try {
      await api.saveSettings('ai', settings);
      alert('AI settings saved successfully!');
    } catch (error) {
      alert('Failed to save settings: ' + error.message);
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

      <div style={{ maxWidth: '800px' }}>
        <GlassPanel>
          <GlassPanelBody>
            <h3 style={{ marginBottom: 'var(--spacing-lg)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Brain size={24} style={{ color: 'var(--accent-primary)' }} />
              Model Settings
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

            <div style={{ marginTop: 'var(--spacing-xl)' }}>
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

            <div style={{ marginTop: 'var(--spacing-2xl)' }}>
              <GlowButton onClick={handleSave}>
                <Zap size={16} />
                Save AI Settings
              </GlowButton>
            </div>
          </GlassPanelBody>
        </GlassPanel>
      </div>
    </div>
  );
};

export default AITab;
