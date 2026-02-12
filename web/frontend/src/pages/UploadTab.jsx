import React, { useState, useEffect, useRef } from 'react';
import { GlassPanel, GlassPanelBody } from '../components/GlassPanel';
import { TextInput, Checkbox, Toggle } from '../components/FormInputs';
import { SecondaryButton } from '../components/Buttons';
import { Upload, CheckCircle } from 'lucide-react';
import { useToast } from '../components/Toast';
import api from '../services/api';

const UploadTab = () => {
  const [settings, setSettings] = useState({
    platforms: {
      tiktok: false,
      instagram: false,
      youtube: false
    },
    brave_path: '',
    user_data_dir: '',
    profile_dir: '',
    upload_delay: 30,
    headless: false,
    wait_confirmation: true,
    auto_retry: true
  });
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
  }, [settings]);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      if (data.upload) {
        setSettings(data.upload);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
      toast.error('Failed to load settings');
    }
  };

  const saveSettings = async () => {
    try {
      await api.configureUpload({
        platforms: settings.platforms,
        brave_path: settings.brave_path,
        user_data_dir: settings.user_data_dir,
        profile_dir: settings.profile_dir
      });
      
      // Also save other settings
      await api.saveSettings('upload', settings);
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const testBrowser = () => {
    // TODO: Implement browser connection test
    toast.info('Browser connection test not yet implemented');
  };

  const selectedCount = Object.values(settings.platforms).filter(Boolean).length;

  return (
    <div className="upload-tab">
      <div className="page-header">
        <h1 className="page-title">Upload Configuration</h1>
        <p className="page-description">
          Configure platform selection and browser automation settings
        </p>
      </div>

      <div style={{ maxWidth: '800px' }}>
        <GlassPanel style={{ marginBottom: 'var(--spacing-xl)' }}>
          <GlassPanelBody>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-lg)' }}>
              <h3 style={{ margin: 0 }}>Platform Selection</h3>
              <span style={{ 
                fontSize: '14px', 
                color: 'var(--text-tertiary)',
                background: selectedCount > 0 ? 'rgba(0, 255, 136, 0.1)' : 'transparent',
                padding: '4px 12px',
                borderRadius: '12px',
                border: selectedCount > 0 ? '1px solid rgba(0, 255, 136, 0.3)' : 'none'
              }}>
                {selectedCount} selected
              </span>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
              <Checkbox
                label="TikTok"
                checked={settings.platforms.tiktok}
                onChange={(e) => setSettings({
                  ...settings,
                  platforms: { ...settings.platforms, tiktok: e.target.checked }
                })}
              />
              <Checkbox
                label="Instagram Reels"
                checked={settings.platforms.instagram}
                onChange={(e) => setSettings({
                  ...settings,
                  platforms: { ...settings.platforms, instagram: e.target.checked }
                })}
              />
              <Checkbox
                label="YouTube Shorts"
                checked={settings.platforms.youtube}
                onChange={(e) => setSettings({
                  ...settings,
                  platforms: { ...settings.platforms, youtube: e.target.checked }
                })}
              />
            </div>

            {selectedCount === 0 && (
              <div style={{ 
                marginTop: 'var(--spacing-md)',
                padding: 'var(--spacing-sm)',
                fontSize: '13px',
                color: '#ffc107',
                background: 'rgba(255, 193, 7, 0.1)',
                border: '1px solid rgba(255, 193, 7, 0.3)',
                borderRadius: 'var(--radius-md)'
              }}>
                ⚠️ No platforms selected. Pipeline will skip upload step.
              </div>
            )}
          </GlassPanelBody>
        </GlassPanel>

        <GlassPanel style={{ marginBottom: 'var(--spacing-xl)' }}>
          <GlassPanelBody>
            <h3 style={{ marginBottom: 'var(--spacing-lg)' }}>Brave Browser Settings</h3>
            
            <TextInput
              label="Brave Browser Path"
              value={settings.brave_path}
              onChange={(e) => setSettings({ ...settings, brave_path: e.target.value })}
              placeholder="/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
              helper="Path to Brave browser executable"
            />

            <TextInput
              label="User Data Directory"
              value={settings.user_data_dir}
              onChange={(e) => setSettings({ ...settings, user_data_dir: e.target.value })}
              placeholder="~/Library/Application Support/BraveSoftware/Brave-Browser"
              helper="Brave user data directory"
            />

            <TextInput
              label="Profile Directory"
              value={settings.profile_dir}
              onChange={(e) => setSettings({ ...settings, profile_dir: e.target.value })}
              placeholder="Default"
              helper="Browser profile to use"
            />

            <div style={{ marginTop: 'var(--spacing-lg)' }}>
              <SecondaryButton onClick={testBrowser}>
                <CheckCircle size={16} />
                Test Browser Connection
              </SecondaryButton>
            </div>
          </GlassPanelBody>
        </GlassPanel>

        <GlassPanel style={{ marginBottom: 'var(--spacing-xl)' }}>
          <GlassPanelBody>
            <h3 style={{ marginBottom: 'var(--spacing-lg)' }}>Upload Options</h3>
            
            <TextInput
              label="Upload Delay (seconds)"
              type="number"
              value={settings.upload_delay}
              onChange={(e) => setSettings({ ...settings, upload_delay: parseInt(e.target.value) || 30 })}
              helper="Delay between uploads to different platforms"
            />

            <div style={{ marginTop: 'var(--spacing-lg)', display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
              <Toggle
                label="Headless Mode"
                checked={settings.headless}
                onChange={(e) => setSettings({ ...settings, headless: e.target.checked })}
              />
              <p style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginTop: '-8px', marginLeft: '60px' }}>
                Run browser in background without visible window
              </p>

              <Toggle
                label="Wait for Upload Confirmation"
                checked={settings.wait_confirmation}
                onChange={(e) => setSettings({ ...settings, wait_confirmation: e.target.checked })}
              />
              <p style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginTop: '-8px', marginLeft: '60px' }}>
                Wait for platform to confirm upload before proceeding
              </p>

              <Toggle
                label="Auto-retry on Failure"
                checked={settings.auto_retry}
                onChange={(e) => setSettings({ ...settings, auto_retry: e.target.checked })}
              />
              <p style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginTop: '-8px', marginLeft: '60px' }}>
                Automatically retry failed uploads
              </p>
            </div>
          </GlassPanelBody>
        </GlassPanel>

        <div style={{ 
          padding: 'var(--spacing-sm)',
          fontSize: '13px',
          color: 'var(--text-tertiary)',
          fontStyle: 'italic'
        }}>
          Settings are automatically saved
        </div>
      </div>
    </div>
  );
};

export default UploadTab;
