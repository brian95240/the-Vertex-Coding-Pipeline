import { defineStore } from 'pinia';
import axios from 'axios';

export const useTaskStore = defineStore('tasks', {
  state: () => ({
    tasks: [],
    currentTask: null,
    loading: false,
    error: null
  }),
  
  getters: {
    getTaskById: (state) => (id) => {
      return state.tasks.find(task => task.task_id === id);
    },
    
    pendingTasks: (state) => {
      return state.tasks.filter(task => task.status === 'PENDING');
    },
    
    runningTasks: (state) => {
      return state.tasks.filter(task => task.status === 'RUNNING');
    },
    
    completedTasks: (state) => {
      return state.tasks.filter(task => task.status === 'COMPLETED');
    },
    
    failedTasks: (state) => {
      return state.tasks.filter(task => task.status === 'FAILED');
    }
  },
  
  actions: {
    async fetchTasks() {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.get('/tasks');
        this.tasks = response.data;
      } catch (error) {
        this.error = error.response?.data?.error?.message || 'Failed to fetch tasks';
        console.error('Error fetching tasks:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async fetchTaskById(taskId) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.get(`/tasks/${taskId}`);
        this.currentTask = response.data;
        
        // Update the task in the tasks array if it exists
        const index = this.tasks.findIndex(task => task.task_id === taskId);
        if (index !== -1) {
          this.tasks[index] = response.data;
        }
        
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.error?.message || `Failed to fetch task ${taskId}`;
        console.error(`Error fetching task ${taskId}:`, error);
        return null;
      } finally {
        this.loading = false;
      }
    },
    
    async createTask(taskData) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.post('/tasks', taskData);
        
        // Add the new task to the tasks array
        this.tasks.push(response.data);
        
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.error?.message || 'Failed to create task';
        console.error('Error creating task:', error);
        return null;
      } finally {
        this.loading = false;
      }
    },
    
    async cancelTask(taskId) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.delete(`/tasks/${taskId}`);
        
        // Update the task status in the tasks array
        const index = this.tasks.findIndex(task => task.task_id === taskId);
        if (index !== -1) {
          this.tasks[index].status = 'CANCELED';
        }
        
        // Update current task if it's the same task
        if (this.currentTask && this.currentTask.task_id === taskId) {
          this.currentTask.status = 'CANCELED';
        }
        
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.error?.message || `Failed to cancel task ${taskId}`;
        console.error(`Error canceling task ${taskId}:`, error);
        return null;
      } finally {
        this.loading = false;
      }
    },
    
    // Poll for task status updates
    async pollTaskStatus(taskId, interval = 5000, maxAttempts = 60) {
      let attempts = 0;
      
      const poll = async () => {
        attempts++;
        
        try {
          const task = await this.fetchTaskById(taskId);
          
          // If task is completed or failed, stop polling
          if (['COMPLETED', 'FAILED', 'CANCELED'].includes(task.status) || attempts >= maxAttempts) {
            return task;
          }
          
          // Continue polling
          return new Promise(resolve => {
            setTimeout(async () => {
              resolve(await poll());
            }, interval);
          });
        } catch (error) {
          console.error(`Error polling task ${taskId}:`, error);
          
          // If there's an error, try again after interval
          if (attempts < maxAttempts) {
            return new Promise(resolve => {
              setTimeout(async () => {
                resolve(await poll());
              }, interval);
            });
          }
          
          throw error;
        }
      };
      
      return poll();
    }
  }
});
