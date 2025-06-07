import axios from 'axios';

// Create axios instance with base URL
const api = axios.create({
  baseURL: process.env.VUE_APP_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Request interceptor for API calls
api.interceptors.request.use(
  (config) => {
    // You can add auth tokens here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for API calls
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle errors globally
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// API service functions
export const apiService = {
  // Health check
  getHealth: () => api.get('/health'),
  
  // Tasks
  getTasks: (params) => api.get('/tasks', { params }),
  getTaskById: (taskId) => api.get(`/tasks/${taskId}`),
  createTask: (taskData) => api.post('/tasks', taskData),
  cancelTask: (taskId) => api.post(`/tasks/${taskId}/cancel`),
  
  // Batches
  getBatches: (params) => api.get('/batches', { params }),
  getBatchById: (batchId) => api.get(`/batches/${batchId}`),
  getBatchTasks: (batchId) => api.get(`/batches/${batchId}/tasks`),
  createBatch: (batchData) => api.post('/batches', batchData),
  cancelBatch: (batchId) => api.post(`/batches/${batchId}/cancel`),
  
  // Providers
  getProviders: () => api.get('/providers'),
  getProviderById: (providerId) => api.get(`/providers/${providerId}`),
  getProviderModels: (providerId) => api.get(`/providers/${providerId}/models`),
  
  // Knowledge
  queryKnowledge: (queryData) => api.post('/knowledge/query', queryData),
  createEntity: (entityData) => api.post('/knowledge/entities', entityData),
  createRelation: (relationData) => api.post('/knowledge/relations', relationData),
  
  // System
  getSystemStatus: () => api.get('/system/status'),
  getSystemLogs: (params) => api.get('/system/logs', { params }),
  
  // Settings
  getSystemSettings: () => api.get('/settings/system'),
  updateSystemSettings: (settingsData) => api.put('/settings/system', settingsData),
  getProviderSettings: () => api.get('/settings/providers'),
  updateProviderSettings: (settingsData) => api.put('/settings/providers', settingsData),
  getFeatureFlags: () => api.get('/settings/features'),
  updateFeatureFlags: (flagsData) => api.put('/settings/features', flagsData)
};

export default api;
