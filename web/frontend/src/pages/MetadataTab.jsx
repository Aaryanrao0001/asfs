import React, { useState, useEffect } from 'react';
import { GlassPanel, GlassPanelBody } from '../components/GlassPanel';
import { TextInput, TextArea, Radio, Toggle } from '../components/FormInputs';
import { GlowButton } from '../components/Buttons';
import { FileText, Save } from 'lucide-react';
import api from '../services/api';

const MetadataTab = () => {
  const [mode, setMode] = useState('uniform');
  const [settings, setSettings] = useState({
    title: '',
    description: '',
    tags: '',
    hashtag_prefix: true,
    caption: ''
  });

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      if (data.metadata) {
        setSettings(data.metadata);
        setMode(data.metadata.mode || 'uniform');
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const handleSave = async () => {
    try {
      await api.saveSettings('metadata', { ...settings, mode });
      alert('Metadata settings saved successfully!');
    } catch (error) {
      alert('Failed to save settings: ' + error.message);
    }
  };

  return (
    <div className="metadata-tab">
      <div className="page-header">
        <h1 className="page-title">Metadata Configuration</h1>
        <p className="page-description">
          Configure titles, descriptions, tags, and captions for clips
        </p>
      </div>

      <div style={{ maxWidth: '800px' }}>
        <GlassPanel>
          <GlassPanelBody>
            <h3 style={{ marginBottom: 'var(--spacing-lg)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={24} style={{ color: 'var(--accent-primary)' }} />
              Metadata Settings
            </h3>
            
            <div style={{ marginBottom: 'var(--spacing-xl)' }}>
              <label className="form-label">Metadata Mode</label>
              <div style={{ display: 'flex', gap: 'var(--spacing-md)', marginTop: 'var(--spacing-sm)' }}>
                <Radio
                  label="Uniform (Same for all)"
                  name="mode"
                  checked={mode === 'uniform'}
                  onChange={() => setMode('uniform')}
                />
                <Radio
                  label="Randomized"
                  name="mode"
                  checked={mode === 'randomized'}
                  onChange={() => setMode('randomized')}
                />
              </div>
            </div>

            <TextArea
              label="Title"
              value={settings.title}
              onChange={(e) => setSettings({ ...settings, title: e.target.value })}
              placeholder="Enter video title..."
              helper="Title for generated clips"
            />

            <TextArea
              label="Description"
              value={settings.description}
              onChange={(e) => setSettings({ ...settings, description: e.target.value })}
              placeholder="Enter video description..."
              helper="Description text for clips"
            />

            <TextInput
              label="Tags"
              value={settings.tags}
              onChange={(e) => setSettings({ ...settings, tags: e.target.value })}
              placeholder="tag1, tag2, tag3"
              helper="Comma-separated list of tags"
            />

            <Toggle
              label="Add # prefix to tags"
              checked={settings.hashtag_prefix}
              onChange={(e) => setSettings({ ...settings, hashtag_prefix: e.target.checked })}
            />

            <TextArea
              label="Caption"
              value={settings.caption}
              onChange={(e) => setSettings({ ...settings, caption: e.target.value })}
              placeholder="Enter caption text..."
              helper="Optional caption for social media posts"
            />

            <div style={{ marginTop: 'var(--spacing-2xl)' }}>
              <GlowButton onClick={handleSave}>
                <Save size={16} />
                Save Metadata Settings
              </GlowButton>
            </div>
          </GlassPanelBody>
        </GlassPanel>
      </div>
    </div>
  );
};

export default MetadataTab;
