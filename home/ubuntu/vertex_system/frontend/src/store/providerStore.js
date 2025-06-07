import { defineStore } from 'pinia';
import axios from 'axios';

export const useProviderStore = defineStore('providers', {
  state: () => ({
    providers: [],
    currentProvider: null,
    loading: false,
    error: null
  }),
  
  getters: {
    getProviderById: (state) => (id) => {
      return state.providers.find(provider => provider.provider_id === id);
    },
    
    getProvidersByCapability: (state) => (capability) => {
      return state.providers.filter(provider => 
        provider.capabilities && provider.capabilities.includes(capability)
      );
    },
    
    getModelsByCapability: (state) => (capability) => {
      const models = [];
      
      state.providers.forEach(provider => {
        if (provider.models) {
          const matchingModels = provider.models.filter(model => 
            model.capabilities && model.capabilities.includes(capability)
          );
          
          matchingModels.forEach(model => {
            models.push({
              ...model,
              provider_id: provider.provider_id,
              provider_name: provider.name
            });
          });
        }
      });
      
      return models;
    }
  },
  
  actions: {
    async fetchProviders() {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.get('/providers');
        this.providers = response.data;
      } catch (error) {
        this.error = error.response?.data?.error?.message || 'Failed to fetch providers';
        console.error('Error fetching providers:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async fetchProviderById(providerId) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.get(`/providers/${providerId}`);
        this.currentProvider = response.data;
        
        // Update the provider in the providers array if it exists
        const index = this.providers.findIndex(provider => provider.provider_id === providerId);
        if (index !== -1) {
          this.providers[index] = response.data;
        }
        
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.error?.message || `Failed to fetch provider ${providerId}`;
        console.error(`Error fetching provider ${providerId}:`, error);
        return null;
      } finally {
        this.loading = false;
      }
    }
  }
});
