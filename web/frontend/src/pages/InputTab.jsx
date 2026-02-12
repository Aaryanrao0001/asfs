import React, { useState, useEffect, useRef } from 'react';
import { GlassPanel, GlassPanelBody } from '../components/GlassPanel';
import { SecondaryButton, GlowButton } from '../components/Buttons';
import { TextInput, Radio, Toggle } from '../components/FormInputs';
import { Upload, Folder, FileVideo, X } from 'lucide-react';
import { useToast } from '../components/Toast';
import api from '../services/api';
import './InputTab.css';

const InputTab = () => {
  const [selectionMode, setSelectionMode] = useState('single');
  const [videoPath, setVideoPath] = useState('');
  const [outputDir, setOutputDir] = useState('output');
  const [useCache, setUseCache] = useState(true);
  const [videoInfo, setVideoInfo] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);
  const toast = useToast();
  const saveTimeoutRef = useRef(null);

  // Load settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  // Save settings with debounce
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
  }, [outputDir, useCache, selectionMode]);

  const loadSettings = async () => {
    try {
      const settings = await api.getSettings();
      if (settings.input) {
        setSelectionMode(settings.input.selection_mode || 'single');
        setOutputDir(settings.input.output_dir || 'output');
        setUseCache(settings.input.use_cache !== undefined ? settings.input.use_cache : true);
        setVideoPath(settings.input.video_path || '');
        setVideoInfo(settings.input.video_info || null);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
      toast.error('Failed to load settings');
    }
  };

  const saveSettings = async () => {
    try {
      await api.saveSettings('input', {
        selection_mode: selectionMode,
        video_path: videoPath,
        output_dir: outputDir,
        use_cache: useCache,
        video_info: videoInfo
      });
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const handleFileSelect = async (file) => {
    if (!file) return;

    // Validate file type
    const validTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(mp4|mov|avi|mkv)$/i)) {
      toast.error('Invalid file type. Please upload MP4, MOV, AVI, or MKV');
      return;
    }

    setUploading(true);
    toast.info('Uploading video...');

    try {
      const response = await api.uploadVideo(file);
      
      if (response.success && response.video) {
        setVideoPath(response.video.path);
        setVideoInfo(response.video);
        toast.success('Video uploaded successfully!');
      } else {
        toast.error('Upload failed: ' + (response.message || 'Unknown error'));
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to upload video: ' + error.message);
    } finally {
      setUploading(false);
    }
  };

  const handleBrowse = () => {
    fileInputRef.current?.click();
  };

  const handleFileInputChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleClearVideo = () => {
    setVideoPath('');
    setVideoInfo(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    toast.info('Video cleared');
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024 * 1024) {
      return (bytes / 1024).toFixed(2) + ' KB';
    }
    return (bytes / 1024 / 1024).toFixed(2) + ' MB';
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="input-tab">
      <div className="page-header">
        <h1 className="page-title">Input Video & Output Settings</h1>
        <p className="page-description">
          Upload video files and configure output destination for processed clips
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
                  disabled
                />
                <Radio
                  label="Folder"
                  name="mode"
                  value="folder"
                  checked={selectionMode === 'folder'}
                  onChange={(e) => setSelectionMode('folder')}
                  disabled
                />
              </div>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="video/mp4,video/quicktime,video/x-msvideo,video/x-matroska,.mp4,.mov,.avi,.mkv"
              onChange={handleFileInputChange}
              style={{ display: 'none' }}
            />

            <div 
              className={`file-drop-zone ${dragActive ? 'drag-active' : ''} ${uploading ? 'uploading' : ''}`}
              onClick={!uploading ? handleBrowse : undefined}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              {uploading ? (
                <>
                  <div className="spinner"></div>
                  <p style={{ fontSize: '16px', fontWeight: 500 }}>
                    Uploading video...
                  </p>
                </>
              ) : (
                <>
                  <Upload size={48} style={{ color: 'var(--accent-primary)', marginBottom: 'var(--spacing-md)' }} />
                  <p style={{ fontSize: '16px', fontWeight: 500, marginBottom: 'var(--spacing-sm)' }}>
                    Drop video here or click to browse
                  </p>
                  <p style={{ fontSize: '14px', color: 'var(--text-tertiary)' }}>
                    Supports MP4, MOV, AVI, MKV formats
                  </p>
                </>
              )}
            </div>

            {videoPath && videoInfo && (
              <div className="video-info-card">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--spacing-md)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                    <FileVideo size={20} style={{ color: 'var(--accent-primary)' }} />
                    <h4>Video Information</h4>
                  </div>
                  <button 
                    onClick={handleClearVideo}
                    style={{ 
                      background: 'none', 
                      border: 'none', 
                      color: 'var(--text-tertiary)', 
                      cursor: 'pointer',
                      padding: '4px',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                  >
                    <X size={18} />
                  </button>
                </div>
                
                <div style={{ marginBottom: 'var(--spacing-md)' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', display: 'block', marginBottom: '4px' }}>
                    Filename
                  </span>
                  <span style={{ fontSize: '14px', color: 'var(--text-primary)' }}>
                    {videoInfo.filename}
                  </span>
                </div>

                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-label">Duration</span>
                    <span className="info-value">{formatDuration(videoInfo.duration)}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Resolution</span>
                    <span className="info-value">{videoInfo.width}x{videoInfo.height}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Size</span>
                    <span className="info-value">{formatFileSize(videoInfo.size)}</span>
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
              <SecondaryButton onClick={handleClearVideo} disabled={!videoPath}>
                <X size={16} />
                Clear Video
              </SecondaryButton>
            </div>
          </GlassPanelBody>
        </GlassPanel>
      </div>
    </div>
  );
};

export default InputTab;
