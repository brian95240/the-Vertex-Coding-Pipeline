<template>
  <div class="settings-container">
    <h1>Settings</h1>
    
    <div v-if="saveError" class="error-message">
      {{ saveError }}
    </div>
    
    <div v-if="saveSuccess" class="success-message">
      {{ saveSuccess }}
    </div>
    
    <div class="settings-card">
      <h2>System Settings</h2>
      
      <form @submit.prevent="saveSystemSettings">
        <div class="form-group">
          <label for="credit-limit">Credit Limit:</label>
          <input type="number" id="credit-limit" v-model.number="systemSettings.creditLimit" min="0" step="1">
          <small>Maximum number of credits that can be used per day</small>
        </div>
        
        <div class="form-group">
          <label for="default-timeout">Default Task Timeout (seconds):</label>
          <input type="number" id="default-timeout" v-model.number="systemSettings.defaultTimeout" min="1" max="3600">
          <small>Default timeout for tasks in seconds</small>
        </div>
        
        <div class="form-group">
          <label for="default-retries">Default Max Retries:</label>
          <input type="number" id="default-retries" v-model.number="systemSettings.defaultRetries" min="0" max="10">
          <small>Default maximum number of retries for failed tasks</small>
        </div>
        
        <div class="form-group">
          <label for="log-level">Log Level:</label>
          <select id="log-level" v-model="systemSettings.logLevel">
            <option value="debug">Debug</option>
            <option value="info">Info</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
          </select>
          <small>Minimum log level to record</small>
        </div>
        
        <div class="form-actions">
          <button type="submit" :disabled="saving" class="btn btn-primary">
            {{ saving ? 'Saving...' : 'Save System Settings' }}
          </button>
        </div>
      </form>
    </div>
    
    <div class="settings-card">
      <h2>Provider Settings</h2>
      
      <div v-if="!providers.length" class="empty-state">
        No providers configured.
      </div>
      
      <div v-else class="provider-settings">
        <div v-for="provider in providers" :key="provider.id" class="provider-setting-item">
          <div class="provider-header">
            <h3>{{ provider.name }}</h3>
            <div class="provider-toggle">
              <label class="switch">
                <input type="checkbox" v-model="provider.enabled">
                <span class="slider"></span>
              </label>
              <span class="toggle-label">{{ provider.enabled ? 'Enabled' : 'Disabled' }}</span>
            </div>
          </div>
          
          <div class="provider-details" v-if="provider.enabled">
            <div class="form-group">
              <label :for="`api-key-${provider.id}`">API Key:</label>
              <div class="api-key-input">
                <input :type="provider.showKey ? 'text' : 'password'" :id="`api-key-${provider.id}`" v-model="provider.apiKey">
                <button type="button" @click="provider.showKey = !provider.showKey" class="btn btn-sm btn-secondary">
                  {{ provider.showKey ? 'Hide' : 'Show' }}
                </button>
              </div>
            </div>
            
            <div class="form-group">
              <label :for="`priority-${provider.id}`">Priority:</label>
              <select :id="`priority-${provider.id}`" v-model="provider.priority">
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
              <small>Provider selection priority</small>
            </div>
            
            <div class="form-group">
              <label :for="`max-concurrent-${provider.id}`">Max Concurrent Requests:</label>
              <input type="number" :id="`max-concurrent-${provider.id}`" v-model.number="provider.maxConcurrent" min="1">
              <small>Maximum number of concurrent requests to this provider</small>
            </div>
          </div>
        </div>
        
        <div class="form-actions">
          <button @click="saveProviderSettings" :disabled="saving" class="btn btn-primary">
            {{ saving ? 'Saving...' : 'Save Provider Settings' }}
          </button>
        </div>
      </div>
    </div>
    
    <div class="settings-card">
      <h2>Feature Flags</h2>
      
      <div class="feature-flags">
        <div v-for="(enabled, feature) in featureFlags" :key="feature" class="feature-flag-item">
          <div class="feature-flag-header">
            <h3>{{ formatFeatureName(feature) }}</h3>
            <div class="feature-toggle">
              <label class="switch">
                <input type="checkbox" v-model="featureFlags[feature]">
                <span class="slider"></span>
              </label>
              <span class="toggle-label">{{ featureFlags[feature] ? 'Enabled' : 'Disabled' }}</span>
            </div>
          </div>
          <p class="feature-description">{{ getFeatureDescription(feature) }}</p>
        </div>
        
        <div class="form-actions">
          <button @click="saveFeatureFlags" :disabled="saving" class="btn btn-primary">
            {{ saving ? 'Saving...' : 'Save Feature Flags' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';

export default {
  name: 'SettingsView',
  setup() {
    const saving = ref(false);
    const saveError = ref(null);
    const saveSuccess = ref(null);
    
    // System settings
    const systemSettings = ref({
      creditLimit: 1000,
      defaultTimeout: 300,
      defaultRetries: 3,
      logLevel: 'info'
    });
    
    // Provider settings
    const providers = ref([
      {
        id: 'openai',
        name: 'OpenAI',
        enabled: true,
        apiKey: '••••••••••••••••••••••',
        showKey: false,
        priority: 'high',
        maxConcurrent: 10
      },
      {
        id: 'anthropic',
        name: 'Anthropic',
        enabled: true,
        apiKey: '••••••••••••••••••••••',
        showKey: false,
        priority: 'medium',
        maxConcurrent: 5
      },
      {
        id: 'google',
        name: 'Google AI',
        enabled: false,
        apiKey: '',
        showKey: false,
        priority: 'medium',
        maxConcurrent: 5
      },
      {
        id: 'mistral',
        name: 'Mistral AI',
        enabled: false,
        apiKey: '',
        showKey: false,
        priority: 'low',
        maxConcurrent: 3
      }
    ]);
    
    // Feature flags
    const featureFlags = ref({
      advanced_batching: true,
      knowledge_graph: true,
      sleep_optimization: true,
      mcp_integration: false,
      recursive_strategies: true
    });
    
    // Format feature name for display
    const formatFeatureName = (feature) => {
      return feature
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    };
    
    // Get feature description
    const getFeatureDescription = (feature) => {
      const descriptions = {
        advanced_batching: 'Enable advanced batch processing capabilities for efficient task execution.',
        knowledge_graph: 'Enable knowledge graph for storing and querying contextual information.',
        sleep_optimization: 'Enable optimization of resource usage during idle periods.',
        mcp_integration: 'Enable integration with MCP server for enhanced capabilities.',
        recursive_strategies: 'Enable recursive problem-solving strategies for complex tasks.'
      };
      
      return descriptions[feature] || 'No description available.';
    };
    
    // Save system settings
    const saveSystemSettings = async () => {
      saving.value = true;
      saveError.value = null;
      saveSuccess.value = null;
      
      try {
        // In a real implementation, this would call an API endpoint
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        saveSuccess.value = 'System settings saved successfully.';
        
        // Auto-hide success message after 3 seconds
        setTimeout(() => {
          saveSuccess.value = null;
        }, 3000);
      } catch (error) {
        saveError.value = 'Failed to save system settings.';
        console.error('Error saving system settings:', error);
      } finally {
        saving.value = false;
      }
    };
    
    // Save provider settings
    const saveProviderSettings = async () => {
      saving.value = true;
      saveError.value = null;
      saveSuccess.value = null;
      
      try {
        // In a real implementation, this would call an API endpoint
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        saveSuccess.value = 'Provider settings saved successfully.';
        
        // Auto-hide success message after 3 seconds
        setTimeout(() => {
          saveSuccess.value = null;
        }, 3000);
      } catch (error) {
        saveError.value = 'Failed to save provider settings.';
        console.error('Error saving provider settings:', error);
      } finally {
        saving.value = false;
      }
    };
    
    // Save feature flags
    const saveFeatureFlags = async () => {
      saving.value = true;
      saveError.value = null;
      saveSuccess.value = null;
      
      try {
        // In a real implementation, this would call an API endpoint
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        saveSuccess.value = 'Feature flags saved successfully.';
        
        // Auto-hide success message after 3 seconds
        setTimeout(() => {
          saveSuccess.value = null;
        }, 3000);
      } catch (error) {
        saveError.value = 'Failed to save feature flags.';
        console.error('Error saving feature flags:', error);
      } finally {
        saving.value = false;
      }
    };
    
    // Load settings on mount
    onMounted(() => {
      // In a real implementation, this would fetch settings from the API
    });
    
    return {
      saving,
      saveError,
      saveSuccess,
      systemSettings,
      providers,
      featureFlags,
      formatFeatureName,
      getFeatureDescription,
      saveSystemSettings,
      saveProviderSettings,
      saveFeatureFlags
    };
  }
};
</script>

<style scoped>
.settings-container {
  padding: 20px;
}

.settings-card {
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 20px;
  margin-bottom: 20px;
}

.settings-card h2 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 18px;
  color: var(--dark-color);
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

.error-message {
  color: var(--danger-color);
  background-color: rgba(220, 53, 69, 0.1);
  border: 1px solid var(--danger-color);
  padding: 10px;
  border-radius: var(--border-radius);
  margin-bottom: 20px;
}

.success-message {
  color: var(--success-color);
  background-color: rgba(40, 167, 69, 0.1);
  border: 1px solid var(--success-color);
  padding: 10px;
  border-radius: var(--border-radius);
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group input[type="text"],
.form-group input[type="password"],
.form-group input[type="number"],
.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: var(--border-radius);
}

.form-group small {
  display: block;
  margin-top: 5px;
  color: var(--secondary-color);
  font-size: 12px;
}

.form-actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.btn {
  padding: 8px 15px;
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  font-size: 14px;
  transition: background-color var(--transition-speed);
}

.btn-primary {
  background-color: var(--primary-color);
  color: white;
}

.btn-primary:hover {
  background-color: #3a5cdc;
}

.btn-secondary {
  background-color: var(--secondary-color);
  color: white;
}

.btn-secondary:hover {
  background-color: #5a6268;
}

.btn-sm {
  padding: 5px 10px;
  font-size: 12px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.empty-state {
  text-align: center;
  padding: 20px;
  color: var(--secondary-color);
}

.provider-settings,
.feature-flags {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.provider-setting-item,
.feature-flag-item {
  border: 1px solid #eee;
  border-radius: var(--border-radius);
  padding: 15px;
}

.provider-header,
.feature-flag-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.provider-header h3,
.feature-flag-header h3 {
  margin: 0;
  font-size: 16px;
}

.provider-toggle,
.feature-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toggle-label {
  font-size: 14px;
  color: var(--secondary-color);
}

/* Toggle Switch */
.switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--primary-color);
}

input:focus + .slider {
  box-shadow: 0 0 1px var(--primary-color);
}

input:checked + .slider:before {
  transform: translateX(16px);
}

.api-key-input {
  display: flex;
  gap: 10px;
}

.api-key-input input {
  flex: 1;
}

.feature-description {
  margin: 0;
  color: var(--secondary-color);
  font-size: 14px;
}
</style>
