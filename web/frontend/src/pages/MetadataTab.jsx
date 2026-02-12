import React, { useState, useEffect, useRef } from 'react';
import { GlassPanel, GlassPanelBody } from '../components/GlassPanel';
import { TextInput, TextArea, Radio, Toggle } from '../components/FormInputs';
import { SecondaryButton } from '../components/Buttons';
import { FileText, Eye } from 'lucide-react';
import { useToast } from '../components/Toast';
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
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const toast = useToast();
  const saveTimeoutRef = useRef(null);

  useEffect(() => {
    loadSettings();
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
  }, [mode, settings]);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      if (data.metadata) {
        setSettings({
          title: data.metadata.title || '',
          description: data.metadata.description || '',
          tags: data.metadata.tags || '',
          hashtag_prefix: data.metadata.hashtag_prefix !== undefined ? data.metadata.hashtag_prefix : true,
          caption: data.metadata.caption || ''
        });
        setMode(data.metadata.mode || 'uniform');
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
      toast.error('Failed to load settings');
    }
  };

  const saveSettings = async () => {
    try {
      await api.saveMetadata({
        mode,
        ...settings
      });
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const handlePreview = async () => {
    setLoading(true);
    try {
      // First save current settings
      await api.saveMetadata({
        mode,
        ...settings
      });
      
      // Then get preview
      const response = await api.previewMetadata();
      if (response.success && response.preview) {
        setPreview(response.preview);
        toast.success('Preview generated successfully');
      } else {
        toast.error('Failed to generate preview');
      }
    } catch (error) {
      console.error('Failed to preview metadata:', error);
      toast.error('Failed to generate preview: ' + error.message);
    } finally {
      setLoading(false);
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

      <div style={{ maxWidth: '1200px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-xl)' }}>
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
              <div className="form-helper" style={{ marginTop: 'var(--spacing-sm)' }}>
                {mode === 'uniform' 
                  ? 'Use same metadata for all clips'
                  : 'Randomize metadata selection for each clip'}
              </div>
            </div>

            <TextArea
              label="Title"
              value={settings.title}
              onChange={(e) => setSettings({ ...settings, title: e.target.value })}
              placeholder="Enter video title..."
              helper="Title for generated clips"
              rows={2}
            />

            <TextArea
              label="Description"
              value={settings.description}
              onChange={(e) => setSettings({ ...settings, description: e.target.value })}
              placeholder="Enter video description..."
              helper="Description text for clips"
              rows={4}
            />

            <TextInput
              label="Tags"
              value={settings.tags}
              onChange={(e) => setSettings({ ...settings, tags: e.target.value })}
              placeholder="tag1 tag2 tag3"
              helper="Space-separated list of tags"
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
              rows={3}
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

            <div style={{ marginTop: 'var(--spacing-xl)' }}>
              <SecondaryButton onClick={handlePreview} disabled={loading}>
                <Eye size={16} />
                {loading ? 'Generating...' : 'Preview Metadata'}
              </SecondaryButton>
            </div>
          </GlassPanelBody>
        </GlassPanel>

        {/* Preview Panel */}
        <GlassPanel>
          <GlassPanelBody>
            <h3 style={{ marginBottom: 'var(--spacing-lg)' }}>Preview</h3>
            
            {preview ? (
              <div>
                {preview.title && (
                  <div style={{ marginBottom: 'var(--spacing-lg)' }}>
                    <label className="form-label">Title</label>
                    <div style={{ 
                      marginTop: 'var(--spacing-sm)',
                      padding: 'var(--spacing-md)',
                      background: 'rgba(11, 36, 28, 0.4)',
                      border: '1px solid var(--glass-border)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--text-primary)',
                      fontSize: '14px'
                    }}>
                      {preview.title}
                    </div>
                  </div>
                )}

                {preview.description && (
                  <div style={{ marginBottom: 'var(--spacing-lg)' }}>
                    <label className="form-label">Description</label>
                    <div style={{ 
                      marginTop: 'var(--spacing-sm)',
                      padding: 'var(--spacing-md)',
                      background: 'rgba(11, 36, 28, 0.4)',
                      border: '1px solid var(--glass-border)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--text-primary)',
                      fontSize: '14px',
                      lineHeight: '1.5'
                    }}>
                      {preview.description}
                    </div>
                  </div>
                )}

                {preview.tags && (
                  <div style={{ marginBottom: 'var(--spacing-lg)' }}>
                    <label className="form-label">Tags</label>
                    <div style={{ 
                      marginTop: 'var(--spacing-sm)',
                      padding: 'var(--spacing-md)',
                      background: 'rgba(11, 36, 28, 0.4)',
                      border: '1px solid var(--glass-border)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--accent-primary)',
                      fontSize: '14px',
                      fontFamily: 'monospace'
                    }}>
                      {preview.tags}
                    </div>
                  </div>
                )}

                {preview.caption && (
                  <div style={{ marginBottom: 'var(--spacing-lg)' }}>
                    <label className="form-label">Caption</label>
                    <div style={{ 
                      marginTop: 'var(--spacing-sm)',
                      padding: 'var(--spacing-md)',
                      background: 'rgba(11, 36, 28, 0.4)',
                      border: '1px solid var(--glass-border)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--text-primary)',
                      fontSize: '14px',
                      lineHeight: '1.5'
                    }}>
                      {preview.caption}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ 
                textAlign: 'center',
                padding: 'var(--spacing-3xl)',
                color: 'var(--text-tertiary)'
              }}>
                <Eye size={48} style={{ marginBottom: 'var(--spacing-md)', opacity: 0.5 }} />
                <p>Click "Preview Metadata" to see how your metadata will look</p>
              </div>
            )}
          </GlassPanelBody>
        </GlassPanel>
      </div>
    </div>
  );
};

export default MetadataTab;
