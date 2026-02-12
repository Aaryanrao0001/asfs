/**
 * API Service - Handles all backend communication
 * Now with REAL endpoints (no mocks!)
 */

const API_BASE = '';  // Proxied through React dev server

class APIService {
  constructor() {
    this.wsConnection = null;
    this.logCallbacks = [];
  }

  async request(endpoint, options = {}) {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ 
          error: `Request failed with status ${response.status}` 
        }));
        throw new Error(error.detail || error.error || 'Request failed');
      }

      return response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // ============================================================================
  // Video Upload
  // ============================================================================

  async uploadVideo(file, onProgress = null) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE}/api/upload-video`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ 
          error: 'Upload failed' 
        }));
        throw new Error(error.detail || error.error || 'Upload failed');
      }

      return response.json();
    } catch (error) {
      console.error('Video upload failed:', error);
      throw error;
    }
  }

  // ============================================================================
  // Pipeline Control
  // ============================================================================

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

  // ============================================================================
  // WebSocket Log Streaming
  // ============================================================================

  connectWebSocket(callback) {
    // Disconnect existing connection
    this.disconnectWebSocket();

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host || 'localhost:5000';
    const wsUrl = `${wsProtocol}//${wsHost}/ws/logs`;

    console.log('Connecting to WebSocket:', wsUrl);

    try {
      this.wsConnection = new WebSocket(wsUrl);

      this.wsConnection.onopen = () => {
        console.log('WebSocket connected');
      };

      this.wsConnection.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type !== 'heartbeat') {
            callback(data);
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      this.wsConnection.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      this.wsConnection.onclose = () => {
        console.log('WebSocket disconnected');
        this.wsConnection = null;
      };

      return () => this.disconnectWebSocket();
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      return () => {};
    }
  }

  disconnectWebSocket() {
    if (this.wsConnection) {
      this.wsConnection.close();
      this.wsConnection = null;
    }
  }

  // ============================================================================
  // Settings Management
  // ============================================================================

  async getSettings() {
    return this.request('/api/settings');
  }

  async saveSettings(category, settings) {
    return this.request('/api/settings', {
      method: 'POST',
      body: JSON.stringify({ category, settings })
    });
  }

  async updateAllSettings(settings) {
    return this.request('/api/settings', {
      method: 'POST',
      body: JSON.stringify({ settings })
    });
  }

  // ============================================================================
  // Ollama / AI Model Management
  // ============================================================================

  async getOllamaStatus() {
    return this.request('/api/ollama/status');
  }

  async startOllama() {
    return this.request('/api/ollama/start', {
      method: 'POST'
    });
  }

  async stopOllama() {
    return this.request('/api/ollama/stop', {
      method: 'POST'
    });
  }

  async listOllamaModels() {
    return this.request('/api/ollama/models');
  }

  async loadOllamaModel(modelName) {
    return this.request('/api/ollama/load-model', {
      method: 'POST',
      body: JSON.stringify({ model_name: modelName })
    });
  }

  // ============================================================================
  // Metadata Management
  // ============================================================================

  async saveMetadata(metadata) {
    return this.request('/api/metadata/save', {
      method: 'POST',
      body: JSON.stringify(metadata)
    });
  }

  async previewMetadata() {
    return this.request('/api/metadata/preview');
  }

  // ============================================================================
  // Upload Configuration
  // ============================================================================

  async configureUpload(config) {
    return this.request('/api/upload/configure', {
      method: 'POST',
      body: JSON.stringify(config)
    });
  }

  // ============================================================================
  // Video Registry
  // ============================================================================

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

  // ============================================================================
  // Health Check
  // ============================================================================

  async healthCheck() {
    return this.request('/api/health');
  }
}

const apiService = new APIService();
export default apiService;
