<template>
  <div class="providers-container">
    <h1>Model Providers</h1>
    
    <div class="actions">
      <button @click="refreshProviders" :disabled="providerStore.loading" class="btn btn-secondary">
        {{ providerStore.loading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </div>
    
    <div v-if="providerStore.error" class="error-message">
      {{ providerStore.error }}
    </div>
    
    <div class="providers-list">
      <h2>Available Providers</h2>
      <div v-if="providerStore.loading && !providerStore.providers.length" class="loading-indicator">
        Loading providers...
      </div>
      <div v-else-if="providerStore.providers.length" class="provider-cards">
        <div 
          v-for="provider in providerStore.providers" 
          :key="provider.provider_id" 
          class="provider-card"
          @click="viewProviderDetails(provider.provider_id)">
          <div class="provider-header">
            <h3>{{ provider.name }}</h3>
            <span class="provider-id">{{ provider.provider_id }}</span>
          </div>
          <p class="provider-description">{{ provider.description }}</p>
          <div class="provider-capabilities">
            <h4>Capabilities:</h4>
            <div class="capability-tags">
              <span 
                v-for="(capability, index) in provider.capabilities" 
                :key="index" 
                class="capability-tag">
                {{ capability }}
              </span>
            </div>
          </div>
          <div class="provider-models">
            <h4>Models: {{ provider.models ? provider.models.length : 0 }}</h4>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">
        No providers found.
      </div>
    </div>

    <!-- Provider Details Modal -->
    <div v-if="showProviderDetailsModal && providerStore.currentProvider" class="modal-overlay" @click.self="closeProviderDetailsModal">
      <div class="modal-content modal-lg">
        <h2>Provider Details: {{ providerStore.currentProvider.name }}</h2>
        <div v-if="providerStore.loading" class="loading-indicator">Loading details...</div>
        <div v-else>
          <div class="provider-info">
            <p><strong>ID:</strong> {{ providerStore.currentProvider.provider_id }}</p>
            <p><strong>Description:</strong> {{ providerStore.currentProvider.description }}</p>
            
            <h3>Capabilities</h3>
            <div class="capability-tags">
              <span 
                v-for="(capability, index) in providerStore.currentProvider.capabilities" 
                :key="index" 
                class="capability-tag">
                {{ capability }}
              </span>
            </div>
            
            <h3>Available Models</h3>
            <table v-if="providerStore.currentProvider.models && providerStore.currentProvider.models.length" class="models-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Capabilities</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="model in providerStore.currentProvider.models" :key="model.id">
                  <td>{{ model.id }}</td>
                  <td>{{ model.name }}</td>
                  <td>
                    <div class="capability-tags">
                      <span 
                        v-for="(capability, index) in model.capabilities" 
                        :key="index" 
                        class="capability-tag small">
                        {{ capability }}
                      </span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-else class="empty-state">No models available for this provider.</div>
          </div>
        </div>
        <div class="form-actions">
          <button type="button" @click="closeProviderDetailsModal" class="btn btn-secondary">Close</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useProviderStore } from '../store/providerStore';

export default {
  name: 'ProvidersView',
  setup() {
    const providerStore = useProviderStore();
    const showProviderDetailsModal = ref(false);
    
    onMounted(() => {
      providerStore.fetchProviders();
    });

    const refreshProviders = () => {
      providerStore.fetchProviders();
    };

    const viewProviderDetails = async (providerId) => {
      await providerStore.fetchProviderById(providerId);
      if (providerStore.currentProvider) {
        showProviderDetailsModal.value = true;
      }
    };

    const closeProviderDetailsModal = () => {
      showProviderDetailsModal.value = false;
      providerStore.currentProvider = null; // Clear current provider
    };

    return {
      providerStore,
      showProviderDetailsModal,
      refreshProviders,
      viewProviderDetails,
      closeProviderDetailsModal
    };
  }
};
</script>

<style scoped>
.providers-container {
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

.providers-list {
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 20px;
}

.providers-list h2 {
  margin-top: 0;
  margin-bottom: 15px;
}

.loading-indicator,
.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--secondary-color);
}

.provider-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.provider-card {
  background-color: var(--light-color);
  border-radius: var(--border-radius);
  padding: 20px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  transition: transform var(--transition-speed), box-shadow var(--transition-speed);
  cursor: pointer;
}

.provider-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.provider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.provider-header h3 {
  margin: 0;
  font-size: 18px;
  color: var(--primary-color);
}

.provider-id {
  font-size: 12px;
  color: var(--secondary-color);
}

.provider-description {
  margin-bottom: 15px;
  color: var(--dark-color);
  font-size: 14px;
  line-height: 1.4;
}

.provider-capabilities,
.provider-models {
  margin-bottom: 10px;
}

.provider-capabilities h4,
.provider-models h4 {
  margin: 0 0 5px 0;
  font-size: 14px;
  color: var(--secondary-color);
}

.capability-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.capability-tag {
  background-color: rgba(74, 108, 247, 0.1);
  color: var(--primary-color);
  padding: 5px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}

.capability-tag.small {
  padding: 3px 8px;
  font-size: 11px;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 30px;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-lg {
  max-width: 800px;
}

.modal-content h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: var(--primary-color);
}

.modal-content h3 {
  margin-top: 20px;
  margin-bottom: 10px;
  border-bottom: 1px solid #eee;
  padding-bottom: 5px;
}

.provider-info p {
  margin-bottom: 10px;
}

.models-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

.models-table th,
.models-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
}

.models-table th {
  background-color: var(--light-color);
  font-weight: bold;
}

.form-actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
