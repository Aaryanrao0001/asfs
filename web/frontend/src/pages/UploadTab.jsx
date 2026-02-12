import React, { useState, useEffect } from 'react';
import { GlassPanel, GlassPanelBody } from '../components/GlassPanel';
import { TextInput, Checkbox, Toggle } from '../components/FormInputs';
import { GlowButton, SecondaryButton } from '../components/Buttons';
import { Upload, CheckCircle } from 'lucide-react';
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

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      if (data.upload) {
        setSettings(data.upload);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const handleSave = async () => {
    try {
      await api.saveSettings('upload', settings);
      alert('Upload settings saved successfully!');
    } catch (error) {
      alert('Failed to save settings: ' + error.message);
    }
  };

  const testBrowser = () => {
    alert('Browser connection test would run here');
  };

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
            <h3 style={{ marginBottom: 'var(--spacing-lg)' }}>Platform Selection</h3>
            
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
              onChange={(e) => setSettings({ ...settings, upload_delay: parseInt(e.target.value) })}
              helper="Delay between uploads to different platforms"
            />

            <div style={{ marginTop: 'var(--spacing-lg)', display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
              <Toggle
                label="Headless Mode"
                checked={settings.headless}
                onChange={(e) => setSettings({ ...settings, headless: e.target.checked })}
              />
              <Toggle
                label="Wait for Upload Confirmation"
                checked={settings.wait_confirmation}
                onChange={(e) => setSettings({ ...settings, wait_confirmation: e.target.checked })}
              />
              <Toggle
                label="Auto-retry on Failure"
                checked={settings.auto_retry}
                onChange={(e) => setSettings({ ...settings, auto_retry: e.target.checked })}
              />
            </div>
          </GlassPanelBody>
        </GlassPanel>

        <GlowButton onClick={handleSave}>
          <Upload size={16} />
          Save Upload Settings
        </GlowButton>
      </div>
    </div>
  );
};

export default UploadTab;
