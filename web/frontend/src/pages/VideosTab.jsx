import React, { useState, useEffect } from 'react';
import { GlassPanel, GlassPanelBody } from '../components/GlassPanel';
import { StatusBadge } from '../components/UIComponents';
import { GlowButton, SecondaryButton } from '../components/Buttons';
import { Video, Upload, RefreshCw, Plus } from 'lucide-react';
import api from '../services/api';
import './VideosTab.css';

const VideosTab = () => {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadVideos();
  }, []);

  const loadVideos = async () => {
    setLoading(true);
    try {
      const data = await api.listVideos();
      setVideos(data.videos || []);
    } catch (error) {
      console.error('Failed to load videos:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPlatformStatus = (platforms, platform) => {
    const status = platforms[platform];
    if (status === 'completed') return 'success';
    if (status === 'failed') return 'error';
    if (status === 'pending') return 'info';
    return 'info';
  };

  return (
    <div className="videos-tab">
      <div className="page-header">
        <h1 className="page-title">Video Registry</h1>
        <p className="page-description">
          Manage videos and track upload status across platforms
        </p>
      </div>

      <div className="videos-toolbar">
        <GlowButton>
          <Plus size={16} />
          Add Videos
        </GlowButton>
        <SecondaryButton onClick={loadVideos}>
          <RefreshCw size={16} />
          Refresh
        </SecondaryButton>
      </div>

      <GlassPanel>
        <GlassPanelBody>
          {loading ? (
            <div style={{ textAlign: 'center', padding: 'var(--spacing-2xl)', color: 'var(--text-secondary)' }}>
              Loading videos...
            </div>
          ) : videos.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 'var(--spacing-2xl)', color: 'var(--text-tertiary)' }}>
              <Video size={48} style={{ marginBottom: 'var(--spacing-md)', opacity: 0.5 }} />
              <p>No videos in registry yet</p>
            </div>
          ) : (
            <div className="videos-table">
              <div className="table-header">
                <div className="table-cell">Title</div>
                <div className="table-cell">Duration</div>
                <div className="table-cell">TikTok</div>
                <div className="table-cell">Instagram</div>
                <div className="table-cell">YouTube</div>
                <div className="table-cell">Actions</div>
              </div>
              {videos.map((video) => (
                <div key={video.id} className="table-row">
                  <div className="table-cell">
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span>{video.title || 'Untitled'}</span>
                      <span style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>
                        {video.file_path}
                      </span>
                    </div>
                  </div>
                  <div className="table-cell">
                    {video.duration ? `${video.duration.toFixed(1)}s` : 'N/A'}
                  </div>
                  <div className="table-cell">
                    <StatusBadge status={getPlatformStatus(video.platforms, 'tiktok')}>
                      {video.platforms.tiktok || 'pending'}
                    </StatusBadge>
                  </div>
                  <div className="table-cell">
                    <StatusBadge status={getPlatformStatus(video.platforms, 'instagram')}>
                      {video.platforms.instagram || 'pending'}
                    </StatusBadge>
                  </div>
                  <div className="table-cell">
                    <StatusBadge status={getPlatformStatus(video.platforms, 'youtube')}>
                      {video.platforms.youtube || 'pending'}
                    </StatusBadge>
                  </div>
                  <div className="table-cell">
                    <SecondaryButton size="sm">
                      <Upload size={14} />
                      Upload
                    </SecondaryButton>
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassPanelBody>
      </GlassPanel>
    </div>
  );
};

export default VideosTab;
