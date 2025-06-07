import { defineStore } from 'pinia';
import axios from 'axios';

export const useBatchStore = defineStore('batches', {
  state: () => ({
    batches: [],
    currentBatch: null,
    loading: false,
    error: null
  }),
  
  getters: {
    getBatchById: (state) => (id) => {
      return state.batches.find(batch => batch.batch_id === id);
    },
    
    runningBatches: (state) => {
      return state.batches.filter(batch => batch.status === 'RUNNING');
    },
    
    completedBatches: (state) => {
      return state.batches.filter(batch => batch.status === 'COMPLETED');
    }
  },
  
  actions: {
    async fetchBatches() {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.get('/batches');
        this.batches = response.data;
      } catch (error) {
        this.error = error.response?.data?.error?.message || 'Failed to fetch batches';
        console.error('Error fetching batches:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async fetchBatchById(batchId) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.get(`/batches/${batchId}`);
        this.currentBatch = response.data;
        
        // Update the batch in the batches array if it exists
        const index = this.batches.findIndex(batch => batch.batch_id === batchId);
        if (index !== -1) {
          this.batches[index] = response.data;
        }
        
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.error?.message || `Failed to fetch batch ${batchId}`;
        console.error(`Error fetching batch ${batchId}:`, error);
        return null;
      } finally {
        this.loading = false;
      }
    },
    
    async fetchBatchTasks(batchId) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.get(`/batches/${batchId}/tasks`);
        
        // Update the current batch tasks if it's the same batch
        if (this.currentBatch && this.currentBatch.batch_id === batchId) {
          this.currentBatch.tasks = response.data;
        }
        
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.error?.message || `Failed to fetch tasks for batch ${batchId}`;
        console.error(`Error fetching tasks for batch ${batchId}:`, error);
        return null;
      } finally {
        this.loading = false;
      }
    },
    
    async createBatch(batchData) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.post('/batches', batchData);
        
        // Add the new batch to the batches array
        this.batches.push(response.data);
        
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.error?.message || 'Failed to create batch';
        console.error('Error creating batch:', error);
        return null;
      } finally {
        this.loading = false;
      }
    },
    
    async cancelBatch(batchId) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.delete(`/batches/${batchId}`);
        
        // Update the batch status in the batches array
        const index = this.batches.findIndex(batch => batch.batch_id === batchId);
        if (index !== -1) {
          this.batches[index].status = 'CANCELED';
        }
        
        // Update current batch if it's the same batch
        if (this.currentBatch && this.currentBatch.batch_id === batchId) {
          this.currentBatch.status = 'CANCELED';
        }
        
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.error?.message || `Failed to cancel batch ${batchId}`;
        console.error(`Error canceling batch ${batchId}:`, error);
        return null;
      } finally {
        this.loading = false;
      }
    }
  }
});
