/**
 * API Service - Handles all backend communication
 */

const API_BASE = '';  // Proxied through React dev server

class APIService {
  async request(endpoint, options = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Request failed' }));
      throw new Error(error.error || 'Request failed');
    }

    return response.json();
  }

  // Pipeline endpoints
  async startPipeline(videoPath, outputDir, useCache = true) {
    return this.request('/api/pipeline/start', {
      method: 'POST',
      body: JSON.stringify({ 
        video_path: videoPath, 
        output_dir: outputDir,
        use_cache: useCache
      })
    });
  }

  async stopPipeline() {
    return this.request('/api/pipeline/stop', {
      method: 'POST'
    });
  }

  async getPipelineStatus() {
    return this.request('/api/pipeline/status');
  }

  streamLogs(callback) {
    const eventSource = new EventSource('/api/pipeline/logs');
    
    eventSource.onmessage = (event) => {
      if (event.data && event.data !== ': heartbeat') {
        try {
          const log = JSON.parse(event.data);
          callback(log);
        } catch (e) {
          console.error('Failed to parse log:', e);
        }
      }
    };

    eventSource.onerror = (error) => {
      console.error('Log stream error:', error);
      eventSource.close();
    };

    return () => eventSource.close();
  }

  // Video endpoints
  async getVideoInfo(videoPath) {
    return this.request('/api/video/info', {
      method: 'POST',
      body: JSON.stringify({ video_path: videoPath })
    });
  }

  // Settings endpoints
  async getSettings() {
    return this.request('/api/settings');
  }

  async saveSettings(category, settings) {
    return this.request('/api/settings', {
      method: 'POST',
      body: JSON.stringify({ category, settings })
    });
  }

  async updateAISettings(settings) {
    return this.request('/api/ai/settings', {
      method: 'POST',
      body: JSON.stringify(settings)
    });
  }

  // Video registry endpoints
  async listVideos() {
    return this.request('/api/videos');
  }

  async addVideo(filePath, title, duration) {
    return this.request('/api/videos/add', {
      method: 'POST',
      body: JSON.stringify({ 
        file_path: filePath, 
        title, 
        duration 
      })
    });
  }

  // Upload endpoints
  async startUpload(videoId, platforms) {
    return this.request('/api/upload/start', {
      method: 'POST',
      body: JSON.stringify({ 
        video_id: videoId, 
        platforms 
      })
    });
  }

  async getUploadStatus(videoId) {
    return this.request(`/api/upload/status?video_id=${videoId}`);
  }

  // Health check
  async healthCheck() {
    return this.request('/api/health');
  }
}

const apiService = new APIService();
export default apiService;
