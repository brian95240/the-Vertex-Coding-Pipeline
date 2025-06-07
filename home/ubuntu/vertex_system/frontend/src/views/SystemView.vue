<template>
  <div class="system-container">
    <h1>System Status</h1>
    
    <div class="actions">
      <button @click="refreshSystemStatus" :disabled="loading" class="btn btn-secondary">
        {{ loading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </div>
    
    <div v-if="error" class="error-message">
      {{ error }}
    </div>
    
    <div class="status-cards">
      <div class="status-card">
        <h2>System Health</h2>
        <div class="status-indicator" :class="{ 'status-healthy': systemStatus.healthy, 'status-unhealthy': !systemStatus.healthy }">
          {{ systemStatus.healthy ? 'Healthy' : 'Unhealthy' }}
        </div>
        <div class="status-details">
          <p><strong>Version:</strong> {{ systemStatus.version }}</p>
          <p><strong>Uptime:</strong> {{ formatUptime(systemStatus.uptime) }}</p>
          <p><strong>Last Updated:</strong> {{ formatTimestamp(systemStatus.timestamp) }}</p>
        </div>
      </div>
      
      <div class="status-card">
        <h2>Resource Usage</h2>
        <div class="resource-meters">
          <div class="resource-meter">
            <div class="meter-label">CPU</div>
            <div class="meter-bar">
              <div class="meter-fill" :style="{ width: `${resourceUsage.cpu}%` }" :class="getResourceClass(resourceUsage.cpu)"></div>
            </div>
            <div class="meter-value">{{ resourceUsage.cpu }}%</div>
          </div>
          <div class="resource-meter">
            <div class="meter-label">Memory</div>
            <div class="meter-bar">
              <div class="meter-fill" :style="{ width: `${resourceUsage.memory}%` }" :class="getResourceClass(resourceUsage.memory)"></div>
            </div>
            <div class="meter-value">{{ resourceUsage.memory }}%</div>
          </div>
          <div class="resource-meter">
            <div class="meter-label">Credits</div>
            <div class="meter-bar">
              <div class="meter-fill" :style="{ width: `${resourceUsage.credits}%` }" :class="getResourceClass(resourceUsage.credits)"></div>
            </div>
            <div class="meter-value">{{ resourceUsage.credits }}%</div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="status-cards">
      <div class="status-card">
        <h2>Active Tasks</h2>
        <div class="task-summary">
          <div class="summary-item">
            <div class="summary-value">{{ taskSummary.pending }}</div>
            <div class="summary-label">Pending</div>
          </div>
          <div class="summary-item">
            <div class="summary-value">{{ taskSummary.running }}</div>
            <div class="summary-label">Running</div>
          </div>
          <div class="summary-item">
            <div class="summary-value">{{ taskSummary.completed }}</div>
            <div class="summary-label">Completed</div>
          </div>
          <div class="summary-item">
            <div class="summary-value">{{ taskSummary.failed }}</div>
            <div class="summary-label">Failed</div>
          </div>
        </div>
      </div>
      
      <div class="status-card">
        <h2>Active Providers</h2>
        <div v-if="activeProviders.length === 0" class="empty-state">
          No active providers.
        </div>
        <div v-else class="provider-list">
          <div v-for="provider in activeProviders" :key="provider.id" class="provider-item">
            <div class="provider-name">{{ provider.name }}</div>
            <div class="provider-status" :class="{ 'status-healthy': provider.status === 'online', 'status-unhealthy': provider.status !== 'online' }">
              {{ provider.status }}
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="status-card">
      <h2>System Logs</h2>
      <div class="log-controls">
        <select v-model="logLevel" @change="filterLogs" class="log-level-select">
          <option value="all">All Levels</option>
          <option value="info">Info & Above</option>
          <option value="warning">Warning & Above</option>
          <option value="error">Errors Only</option>
        </select>
        <input type="text" v-model="logSearch" @input="filterLogs" placeholder="Search logs..." class="log-search">
      </div>
      <div class="log-container">
        <div v-if="filteredLogs.length === 0" class="empty-state">
          No logs matching the current filters.
        </div>
        <table v-else class="log-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Level</th>
              <th>Component</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(log, index) in filteredLogs" :key="index" :class="`log-${log.level.toLowerCase()}`">
              <td>{{ formatTimestamp(log.timestamp) }}</td>
              <td>{{ log.level }}</td>
              <td>{{ log.component }}</td>
              <td>{{ log.message }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';

export default {
  name: 'SystemView',
  setup() {
    const loading = ref(false);
    const error = ref(null);
    
    // System status
    const systemStatus = ref({
      healthy: true,
      version: '1.0.0',
      uptime: 3600, // seconds
      timestamp: Date.now() / 1000
    });
    
    // Resource usage
    const resourceUsage = ref({
      cpu: 45,
      memory: 60,
      credits: 25
    });
    
    // Task summary
    const taskSummary = ref({
      pending: 5,
      running: 3,
      completed: 42,
      failed: 2
    });
    
    // Active providers
    const activeProviders = ref([
      { id: 'openai', name: 'OpenAI', status: 'online' },
      { id: 'anthropic', name: 'Anthropic', status: 'online' },
      { id: 'google', name: 'Google AI', status: 'degraded' }
    ]);
    
    // System logs
    const logs = ref([
      { timestamp: Date.now() / 1000 - 60, level: 'INFO', component: 'TaskOrchestrator', message: 'Task task_123456 completed successfully' },
      { timestamp: Date.now() / 1000 - 120, level: 'WARNING', component: 'ResourceOptimization', message: 'Credit usage approaching daily limit' },
      { timestamp: Date.now() / 1000 - 180, level: 'ERROR', component: 'ModelProvider', message: 'Failed to connect to provider "cohere"' },
      { timestamp: Date.now() / 1000 - 240, level: 'INFO', component: 'BatchController', message: 'Batch batch_789012 created with 5 tasks' },
      { timestamp: Date.now() / 1000 - 300, level: 'INFO', component: 'KnowledgeSystem', message: 'Entity "machine_learning" created' },
      { timestamp: Date.now() / 1000 - 360, level: 'WARNING', component: 'TaskOrchestrator', message: 'Task task_345678 exceeded timeout, retrying' },
      { timestamp: Date.now() / 1000 - 420, level: 'INFO', component: 'SystemMonitor', message: 'System health check passed' },
      { timestamp: Date.now() / 1000 - 480, level: 'ERROR', component: 'BatchController', message: 'Failed to process batch batch_567890' },
      { timestamp: Date.now() / 1000 - 540, level: 'INFO', component: 'ModelProvider', message: 'New provider "mistral" registered' },
      { timestamp: Date.now() / 1000 - 600, level: 'INFO', component: 'ResourceOptimization', message: 'Resource allocation optimized' }
    ]);
    
    // Log filtering
    const logLevel = ref('all');
    const logSearch = ref('');
    const filteredLogs = ref([...logs.value]);
    
    const filterLogs = () => {
      filteredLogs.value = logs.value.filter(log => {
        // Filter by level
        if (logLevel.value === 'info' && log.level === 'INFO') return true;
        if (logLevel.value === 'warning' && (log.level === 'WARNING' || log.level === 'ERROR')) return true;
        if (logLevel.value === 'error' && log.level === 'ERROR') return true;
        if (logLevel.value === 'all') return true;
        return false;
      }).filter(log => {
        // Filter by search term
        if (!logSearch.value) return true;
        const searchTerm = logSearch.value.toLowerCase();
        return (
          log.component.toLowerCase().includes(searchTerm) ||
          log.message.toLowerCase().includes(searchTerm)
        );
      });
    };
    
    // Format timestamps
    const formatTimestamp = (timestamp) => {
      if (!timestamp) return 'N/A';
      return new Date(timestamp * 1000).toLocaleString();
    };
    
    // Format uptime
    const formatUptime = (seconds) => {
      if (!seconds) return 'N/A';
      
      const days = Math.floor(seconds / 86400);
      const hours = Math.floor((seconds % 86400) / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      
      let result = '';
      if (days > 0) result += `${days}d `;
      if (hours > 0 || days > 0) result += `${hours}h `;
      result += `${minutes}m`;
      
      return result;
    };
    
    // Get CSS class for resource meter
    const getResourceClass = (value) => {
      if (value < 50) return 'resource-low';
      if (value < 80) return 'resource-medium';
      return 'resource-high';
    };
    
    // Refresh system status
    const refreshSystemStatus = async () => {
      loading.value = true;
      error.value = null;
      
      try {
        // In a real implementation, this would fetch data from the API
        // For now, we'll just simulate a delay and update some values
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        systemStatus.value.uptime += 1000;
        systemStatus.value.timestamp = Date.now() / 1000;
        
        resourceUsage.value.cpu = Math.floor(Math.random() * 80) + 10;
        resourceUsage.value.memory = Math.floor(Math.random() * 70) + 20;
        
        // Add a new log entry
        const newLog = {
          timestamp: Date.now() / 1000,
          level: 'INFO',
          component: 'SystemMonitor',
          message: 'System status refreshed'
        };
        logs.value.unshift(newLog);
        
        // Re-apply filters
        filterLogs();
      } catch (e) {
        error.value = 'Failed to refresh system status';
        console.error('Error refreshing system status:', e);
      } finally {
        loading.value = false;
      }
    };
    
    onMounted(() => {
      // Initial filter
      filterLogs();
    });
    
    return {
      loading,
      error,
      systemStatus,
      resourceUsage,
      taskSummary,
      activeProviders,
      logs,
      filteredLogs,
      logLevel,
      logSearch,
      formatTimestamp,
      formatUptime,
      getResourceClass,
      filterLogs,
      refreshSystemStatus
    };
  }
};
</script>

<style scoped>
.system-container {
  padding: 20px;
}

.actions {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.btn {
  padding: 8px 15px;
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  font-size: 14px;
  transition: background-color var(--transition-speed);
}

.btn-secondary {
  background-color: var(--secondary-color);
  color: white;
}

.btn-secondary:hover {
  background-color: #5a6268;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  color: var(--danger-color);
  background-color: rgba(220, 53, 69, 0.1);
  border: 1px solid var(--danger-color);
  padding: 10px;
  border-radius: var(--border-radius);
  margin-bottom: 20px;
}

.status-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.status-card {
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 20px;
}

.status-card h2 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 18px;
  color: var(--dark-color);
}

.status-indicator {
  display: inline-block;
  padding: 5px 10px;
  border-radius: 12px;
  font-weight: bold;
  margin-bottom: 15px;
}

.status-healthy {
  background-color: var(--success-color);
  color: white;
}

.status-unhealthy {
  background-color: var(--danger-color);
  color: white;
}

.status-details p {
  margin: 5px 0;
}

.resource-meters {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.resource-meter {
  display: flex;
  align-items: center;
  gap: 10px;
}

.meter-label {
  width: 60px;
  font-weight: bold;
}

.meter-bar {
  flex: 1;
  height: 10px;
  background-color: #e9ecef;
  border-radius: 5px;
  overflow: hidden;
}

.meter-fill {
  height: 100%;
  border-radius: 5px;
}

.resource-low {
  background-color: var(--success-color);
}

.resource-medium {
  background-color: var(--warning-color);
}

.resource-high {
  background-color: var(--danger-color);
}

.meter-value {
  width: 50px;
  text-align: right;
}

.task-summary {
  display: flex;
  justify-content: space-between;
}

.summary-item {
  text-align: center;
  padding: 10px;
}

.summary-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.summary-label {
  font-size: 12px;
  color: var(--secondary-color);
}

.provider-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.provider-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background-color: var(--light-color);
  border-radius: var(--border-radius);
}

.provider-name {
  font-weight: bold;
}

.provider-status {
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
  text-transform: uppercase;
}

.log-controls {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.log-level-select,
.log-search {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: var(--border-radius);
}

.log-search {
  flex: 1;
}

.log-container {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #eee;
  border-radius: var(--border-radius);
}

.log-table {
  width: 100%;
  border-collapse: collapse;
}

.log-table th,
.log-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
  font-size: 13px;
}

.log-table th {
  background-color: var(--light-color);
  font-weight: bold;
  position: sticky;
  top: 0;
}

.log-info {
  background-color: rgba(23, 162, 184, 0.1);
}

.log-warning {
  background-color: rgba(255, 193, 7, 0.1);
}

.log-error {
  background-color: rgba(220, 53, 69, 0.1);
}

.empty-state {
  text-align: center;
  padding: 20px;
  color: var(--secondary-color);
}

@media (max-width: 768px) {
  .status-cards {
    grid-template-columns: 1fr;
  }
  
  .task-summary {
    flex-wrap: wrap;
  }
  
  .summary-item {
    width: 50%;
  }
}
</style>
