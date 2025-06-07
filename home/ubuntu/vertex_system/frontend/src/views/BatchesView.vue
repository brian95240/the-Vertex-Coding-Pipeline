<template>
  <div class="batches-container">
    <h1>Batches</h1>
    
    <div class="actions">
      <button @click="showCreateBatchModal = true" class="btn btn-primary">Create Batch</button>
      <button @click="refreshBatches" :disabled="batchStore.loading" class="btn btn-secondary">
        {{ batchStore.loading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </div>
    
    <div v-if="batchStore.error" class="error-message">
      {{ batchStore.error }}
    </div>
    
    <div class="batch-list">
      <h2>Batch List</h2>
      <div v-if="batchStore.loading && !batchStore.batches.length" class="loading-indicator">
        Loading batches...
      </div>
      <table v-else-if="batchStore.batches.length" class="batch-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Status</th>
            <th>Tasks</th>
            <th>Created At</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="batch in batchStore.batches" :key="batch.batch_id">
            <td>{{ batch.batch_id.substring(0, 8) }}...</td>
            <td>{{ batch.name || 'N/A' }}</td>
            <td>
              <span :class="['status-badge', `status-${batch.status.toLowerCase()}`]">
                {{ batch.status }}
              </span>
            </td>
            <td>{{ batch.completed_count }} / {{ batch.task_count }}</td>
            <td>{{ formatTimestamp(batch.created_at) }}</td>
            <td>
              <button @click="viewBatchDetails(batch.batch_id)" class="btn btn-sm btn-info">Details</button>
              <button 
                @click="cancelBatch(batch.batch_id)" 
                :disabled="batchStore.loading || !canCancel(batch.status)"
                class="btn btn-sm btn-danger">
                Cancel
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">
        No batches found.
      </div>
    </div>

    <!-- Create Batch Modal -->
    <div v-if="showCreateBatchModal" class="modal-overlay" @click.self="closeCreateBatchModal">
      <div class="modal-content modal-lg">
        <h2>Create New Batch</h2>
        <form @submit.prevent="submitCreateBatch">
          <div class="form-group">
            <label for="batch-name">Batch Name:</label>
            <input type="text" id="batch-name" v-model="newBatch.name" required>
          </div>
          <div class="form-group">
            <label for="batch-description">Batch Description:</label>
            <input type="text" id="batch-description" v-model="newBatch.description" required>
          </div>
          
          <h3>Tasks</h3>
          <div v-for="(task, index) in newBatch.tasks" :key="index" class="task-form-group">
            <h4>Task {{ index + 1 }}</h4>
            <div class="form-group">
              <label :for="`task-desc-${index}`">Description:</label>
              <input type="text" :id="`task-desc-${index}`" v-model="task.description" required>
            </div>
            <div class="form-group">
              <label :for="`task-input-${index}`">Input Data (JSON):</label>
              <textarea :id="`task-input-${index}`" v-model="task.input_data_json" rows="3" required></textarea>
            </div>
            <button type="button" @click="removeTask(index)" class="btn btn-sm btn-danger">Remove Task</button>
          </div>
          <button type="button" @click="addTask" class="btn btn-sm btn-secondary">Add Task</button>

          <h3>Batch Configuration</h3>
          <div class="form-group">
            <label for="batch-max-concurrent">Max Concurrent Tasks:</label>
            <input type="number" id="batch-max-concurrent" v-model.number="newBatch.batch_config.max_concurrent_tasks" min="1">
          </div>
          <div class="form-group">
            <label for="batch-stop-on-failure">Stop on First Failure:</label>
            <input type="checkbox" id="batch-stop-on-failure" v-model="newBatch.batch_config.stop_on_first_failure">
          </div>

          <div class="form-actions">
            <button type="button" @click="closeCreateBatchModal" class="btn btn-secondary">Cancel</button>
            <button type="submit" :disabled="batchStore.loading || newBatch.tasks.length === 0" class="btn btn-primary">
              {{ batchStore.loading ? 'Creating...' : 'Create Batch' }}
            </button>
          </div>
          <div v-if="createBatchError" class="error-message">
            {{ createBatchError }}
          </div>
        </form>
      </div>
    </div>

    <!-- Batch Details Modal -->
    <div v-if="showBatchDetailsModal && batchStore.currentBatch" class="modal-overlay" @click.self="closeBatchDetailsModal">
      <div class="modal-content modal-lg">
        <h2>Batch Details ({{ batchStore.currentBatch.batch_id }})</h2>
        <div v-if="batchStore.loading" class="loading-indicator">Loading details...</div>
        <div v-else>
          <pre>{{ JSON.stringify(batchStore.currentBatch, null, 2) }}</pre>
          <h3>Tasks</h3>
          <div v-if="batchStore.currentBatch.tasks && batchStore.currentBatch.tasks.length">
            <table class="task-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Status</th>
                  <th>Result/Error</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="task in batchStore.currentBatch.tasks" :key="task.task_id">
                  <td>{{ task.task_id.substring(0, 8) }}...</td>
                  <td>
                    <span :class="['status-badge', `status-${task.status.toLowerCase()}`]">
                      {{ task.status }}
                    </span>
                  </td>
                  <td>
                    <pre v-if="task.result">{{ JSON.stringify(task.result, null, 2) }}</pre>
                    <span v-else-if="task.error" class="error-text">{{ task.error }}</span>
                    <span v-else>-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty-state">No tasks found for this batch.</div>
        </div>
        <div class="form-actions">
          <button type="button" @click="closeBatchDetailsModal" class="btn btn-secondary">Close</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useBatchStore } from '../store/batchStore';

export default {
  name: 'BatchesView',
  setup() {
    const batchStore = useBatchStore();
    const showCreateBatchModal = ref(false);
    const showBatchDetailsModal = ref(false);
    const createBatchError = ref(null);
    
    const newBatch = ref({
      name: '',
      description: '',
      tasks: [],
      batch_config: {
        max_concurrent_tasks: 5,
        stop_on_first_failure: false
      }
    });

    onMounted(() => {
      batchStore.fetchBatches();
    });

    const refreshBatches = () => {
      batchStore.fetchBatches();
    };

    const formatTimestamp = (timestamp) => {
      if (!timestamp) return 'N/A';
      return new Date(timestamp * 1000).toLocaleString();
    };

    const canCancel = (status) => {
      return ['PENDING', 'RUNNING'].includes(status);
    };

    const cancelBatch = async (batchId) => {
      if (confirm(`Are you sure you want to cancel batch ${batchId}?`)) {
        await batchStore.cancelBatch(batchId);
      }
    };

    const viewBatchDetails = async (batchId) => {
      await batchStore.fetchBatchById(batchId);
      if (batchStore.currentBatch) {
        await batchStore.fetchBatchTasks(batchId); // Fetch tasks for the batch
        showBatchDetailsModal.value = true;
      }
    };

    const closeBatchDetailsModal = () => {
      showBatchDetailsModal.value = false;
      batchStore.currentBatch = null; // Clear current batch
    };

    const closeCreateBatchModal = () => {
      showCreateBatchModal.value = false;
      createBatchError.value = null;
      // Reset form
      newBatch.value = {
        name: '',
        description: '',
        tasks: [],
        batch_config: {
          max_concurrent_tasks: 5,
          stop_on_first_failure: false
        }
      };
    };

    const addTask = () => {
      newBatch.value.tasks.push({
        description: '',
        input_data_json: '{}',
        priority: 'MEDIUM', // Default priority for batch tasks
        timeout_seconds: 300,
        max_retries: 3
      });
    };

    const removeTask = (index) => {
      newBatch.value.tasks.splice(index, 1);
    };

    const submitCreateBatch = async () => {
      createBatchError.value = null;
      const tasksData = [];

      for (const task of newBatch.value.tasks) {
        let inputData;
        try {
          inputData = JSON.parse(task.input_data_json);
        } catch (e) {
          createBatchError.value = `Invalid JSON format for Input Data in one of the tasks.`;
          return;
        }
        tasksData.push({
          description: task.description,
          input_data: inputData,
          priority: task.priority, // Use task-specific priority if needed
          timeout_seconds: task.timeout_seconds,
          max_retries: task.max_retries
        });
      }

      const batchData = {
        name: newBatch.value.name,
        description: newBatch.value.description,
        tasks: tasksData,
        batch_config: newBatch.value.batch_config
      };

      const createdBatch = await batchStore.createBatch(batchData);
      if (createdBatch) {
        closeCreateBatchModal();
      } else {
        createBatchError.value = batchStore.error || 'Failed to create batch.';
      }
    };

    // Add a default task when the modal opens
    addTask();

    return {
      batchStore,
      showCreateBatchModal,
      showBatchDetailsModal,
      newBatch,
      createBatchError,
      refreshBatches,
      formatTimestamp,
      canCancel,
      cancelBatch,
      viewBatchDetails,
      closeBatchDetailsModal,
      closeCreateBatchModal,
      addTask,
      removeTask,
      submitCreateBatch
    };
  }
};
</script>

<style scoped>
/* Reuse styles from TasksView.vue where applicable */
.batches-container {
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

.btn-info {
  background-color: var(--info-color);
  color: white;
}

.btn-info:hover {
  background-color: #138496;
}

.btn-danger {
  background-color: var(--danger-color);
  color: white;
}

.btn-danger:hover {
  background-color: #c82333;
}

.btn-sm {
  padding: 5px 10px;
  font-size: 12px;
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

.batch-list {
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 20px;
}

.batch-list h2 {
  margin-top: 0;
  margin-bottom: 15px;
}

.loading-indicator,
.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--secondary-color);
}

.batch-table,
.task-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
}

.batch-table th,
.batch-table td,
.task-table th,
.task-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
}

.batch-table th,
.task-table th {
  background-color: var(--light-color);
  font-weight: bold;
}

.batch-table tbody tr:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.batch-table td button {
  margin-right: 5px;
}

.status-badge {
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
  color: white;
  text-transform: uppercase;
}

.status-pending {
  background-color: var(--warning-color);
  color: #333;
}

.status-running {
  background-color: var(--info-color);
}

.status-completed {
  background-color: var(--success-color);
}

.status-failed {
  background-color: var(--danger-color);
}

.status-canceled {
  background-color: var(--secondary-color);
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
}

.modal-content h3 {
  margin-top: 20px;
  margin-bottom: 10px;
  border-bottom: 1px solid #eee;
  padding-bottom: 5px;
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
.form-group input[type="number"],
.form-group input[type="checkbox"],
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: var(--border-radius);
}

.form-group input[type="checkbox"] {
  width: auto;
}

.form-group textarea {
  resize: vertical;
}

.form-group small {
  color: var(--secondary-color);
  font-size: 12px;
}

.task-form-group {
  border: 1px solid #eee;
  padding: 15px;
  margin-bottom: 15px;
  border-radius: var(--border-radius);
}

.task-form-group h4 {
  margin-top: 0;
  margin-bottom: 10px;
}

.form-actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

pre {
  background-color: var(--light-color);
  padding: 15px;
  border-radius: var(--border-radius);
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 13px;
}

.error-text {
  color: var(--danger-color);
}
</style>
