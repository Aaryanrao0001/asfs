import React, { useState } from 'react';
import { GlassPanel, GlassPanelBody } from '../components/GlassPanel';
import { SecondaryButton } from '../components/Buttons';
import { TextInput, Radio, Toggle } from '../components/FormInputs';
import { Upload, Folder } from 'lucide-react';
import './InputTab.css';

const InputTab = () => {
  const [selectionMode, setSelectionMode] = useState('single');
  const [videoPath, setVideoPath] = useState('');
  const [outputDir, setOutputDir] = useState('output');
  const [useCache, setUseCache] = useState(true);
  const [videoInfo] = useState(null);

  const handleBrowse = () => {
    // In a real implementation, this would open a file dialog
    // For web, we'd need to use the File API
    alert('File selection dialog would open here. In production, use <input type="file">');
  };

  return (
    <div className="input-tab">
      <div className="page-header">
        <h1 className="page-title">Input Video & Output Settings</h1>
        <p className="page-description">
          Select video files and configure output destination for processed clips
        </p>
      </div>

      <div className="tab-grid">
        <GlassPanel>
          <GlassPanelBody>
            <h3 style={{ marginBottom: 'var(--spacing-lg)' }}>Video Selection</h3>
            
            <div style={{ marginBottom: 'var(--spacing-lg)' }}>
              <label className="form-label">Selection Mode</label>
              <div style={{ display: 'flex', gap: 'var(--spacing-md)', marginTop: 'var(--spacing-sm)' }}>
                <Radio
                  label="Single File"
                  name="mode"
                  value="single"
                  checked={selectionMode === 'single'}
                  onChange={(e) => setSelectionMode('single')}
                />
                <Radio
                  label="Multiple Files"
                  name="mode"
                  value="multiple"
                  checked={selectionMode === 'multiple'}
                  onChange={(e) => setSelectionMode('multiple')}
                />
                <Radio
                  label="Folder"
                  name="mode"
                  value="folder"
                  checked={selectionMode === 'folder'}
                  onChange={(e) => setSelectionMode('folder')}
                />
              </div>
            </div>

            <div className="file-drop-zone" onClick={handleBrowse}>
              <Upload size={48} style={{ color: 'var(--accent-primary)', marginBottom: 'var(--spacing-md)' }} />
              <p style={{ fontSize: '16px', fontWeight: 500, marginBottom: 'var(--spacing-sm)' }}>
                Drop files here or click to browse
              </p>
              <p style={{ fontSize: '14px', color: 'var(--text-tertiary)' }}>
                Supports MP4, MOV, AVI, MKV formats
              </p>
            </div>

            {videoPath && (
              <div style={{ marginTop: 'var(--spacing-lg)' }}>
                <TextInput
                  label="Selected Path"
                  value={videoPath}
                  readOnly
                />
              </div>
            )}

            {videoInfo && (
              <div className="video-info-card">
                <h4>Video Information</h4>
                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-label">Duration</span>
                    <span className="info-value">{videoInfo.duration}s</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Resolution</span>
                    <span className="info-value">{videoInfo.width}x{videoInfo.height}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Size</span>
                    <span className="info-value">{(videoInfo.size / 1024 / 1024).toFixed(2)} MB</span>
                  </div>
                </div>
              </div>
            )}
          </GlassPanelBody>
        </GlassPanel>

        <GlassPanel>
          <GlassPanelBody>
            <h3 style={{ marginBottom: 'var(--spacing-lg)' }}>Output Configuration</h3>
            
            <TextInput
              label="Output Directory"
              value={outputDir}
              onChange={(e) => setOutputDir(e.target.value)}
              placeholder="output"
              helper="Clips and work files will be saved here"
            />

            <div style={{ marginTop: 'var(--spacing-xl)' }}>
              <Toggle
                label="Use Cache (faster re-runs)"
                checked={useCache}
                onChange={(e) => setUseCache(e.target.checked)}
              />
              <p style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginTop: 'var(--spacing-xs)', marginLeft: '60px' }}>
                Reuse transcripts and analysis from previous runs
              </p>
            </div>

            <div style={{ marginTop: 'var(--spacing-2xl)', display: 'flex', gap: 'var(--spacing-md)' }}>
              <SecondaryButton onClick={() => setVideoPath('')}>
                <Folder size={16} />
                Reset
              </SecondaryButton>
            </div>
          </GlassPanelBody>
        </GlassPanel>
      </div>
    </div>
  );
};

export default InputTab;
