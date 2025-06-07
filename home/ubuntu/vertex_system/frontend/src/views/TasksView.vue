<template>
  <div class="tasks-container">
    <h1>Tasks</h1>
    
    <div class="actions">
      <button @click="showCreateTaskModal = true" class="btn btn-primary">Create Task</button>
      <button @click="refreshTasks" :disabled="taskStore.loading" class="btn btn-secondary">
        {{ taskStore.loading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </div>
    
    <div v-if="taskStore.error" class="error-message">
      {{ taskStore.error }}
    </div>
    
    <div class="task-list">
      <h2>Task List</h2>
      <div v-if="taskStore.loading && !taskStore.tasks.length" class="loading-indicator">
        Loading tasks...
      </div>
      <table v-else-if="taskStore.tasks.length" class="task-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Description</th>
            <th>Status</th>
            <th>Priority</th>
            <th>Created At</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in taskStore.tasks" :key="task.task_id">
            <td>{{ task.task_id.substring(0, 8) }}...</td>
            <td>{{ task.description || task.metadata?.description || 'N/A' }}</td>
            <td>
              <span :class="['status-badge', `status-${task.status.toLowerCase()}`]">
                {{ task.status }}
              </span>
            </td>
            <td>{{ task.priority || 'N/A' }}</td>
            <td>{{ formatTimestamp(task.created_at) }}</td>
            <td>
              <button @click="viewTaskDetails(task.task_id)" class="btn btn-sm btn-info">Details</button>
              <button 
                @click="cancelTask(task.task_id)" 
                :disabled="taskStore.loading || !canCancel(task.status)"
                class="btn btn-sm btn-danger">
                Cancel
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">
        No tasks found.
      </div>
    </div>

    <!-- Create Task Modal -->
    <div v-if="showCreateTaskModal" class="modal-overlay" @click.self="closeCreateTaskModal">
      <div class="modal-content">
        <h2>Create New Task</h2>
        <form @submit.prevent="submitCreateTask">
          <div class="form-group">
            <label for="task-description">Description:</label>
            <input type="text" id="task-description" v-model="newTask.description" required>
          </div>
          <div class="form-group">
            <label for="task-input-data">Input Data (JSON):</label>
            <textarea id="task-input-data" v-model="newTask.input_data_json" rows="4" required></textarea>
            <small>Enter valid JSON data.</small>
          </div>
          <div class="form-group">
            <label for="task-priority">Priority:</label>
            <select id="task-priority" v-model="newTask.priority">
              <option value="LOW">LOW</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="HIGH">HIGH</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>
          <div class="form-group">
            <label for="task-timeout">Timeout (seconds):</label>
            <input type="number" id="task-timeout" v-model.number="newTask.timeout_seconds" min="1" max="3600">
          </div>
          <div class="form-group">
            <label for="task-retries">Max Retries:</label>
            <input type="number" id="task-retries" v-model.number="newTask.max_retries" min="0" max="10">
          </div>
          <div class="form-actions">
            <button type="button" @click="closeCreateTaskModal" class="btn btn-secondary">Cancel</button>
            <button type="submit" :disabled="taskStore.loading" class="btn btn-primary">
              {{ taskStore.loading ? 'Creating...' : 'Create Task' }}
            </button>
          </div>
          <div v-if="createTaskError" class="error-message">
            {{ createTaskError }}
          </div>
        </form>
      </div>
    </div>

    <!-- Task Details Modal -->
    <div v-if="showTaskDetailsModal && taskStore.currentTask" class="modal-overlay" @click.self="closeTaskDetailsModal">
      <div class="modal-content modal-lg">
        <h2>Task Details ({{ taskStore.currentTask.task_id }})</h2>
        <div v-if="taskStore.loading" class="loading-indicator">Loading details...</div>
        <div v-else>
          <pre>{{ JSON.stringify(taskStore.currentTask, null, 2) }}</pre>
        </div>
        <div class="form-actions">
          <button type="button" @click="closeTaskDetailsModal" class="btn btn-secondary">Close</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { useTaskStore } from '../store/taskStore';

export default {
  name: 'TasksView',
  setup() {
    const taskStore = useTaskStore();
    const showCreateTaskModal = ref(false);
    const showTaskDetailsModal = ref(false);
    const createTaskError = ref(null);
    
    const newTask = ref({
      description: '',
      input_data_json: '{}',
      priority: 'MEDIUM',
      timeout_seconds: 300,
      max_retries: 3
    });

    onMounted(() => {
      taskStore.fetchTasks();
    });

    const refreshTasks = () => {
      taskStore.fetchTasks();
    };

    const formatTimestamp = (timestamp) => {
      if (!timestamp) return 'N/A';
      return new Date(timestamp * 1000).toLocaleString();
    };

    const canCancel = (status) => {
      return ['PENDING', 'RUNNING'].includes(status);
    };

    const cancelTask = async (taskId) => {
      if (confirm(`Are you sure you want to cancel task ${taskId}?`)) {
        await taskStore.cancelTask(taskId);
        // Optionally refresh the list or rely on reactivity
      }
    };

    const viewTaskDetails = async (taskId) => {
      await taskStore.fetchTaskById(taskId);
      if (taskStore.currentTask) {
        showTaskDetailsModal.value = true;
      }
    };

    const closeTaskDetailsModal = () => {
      showTaskDetailsModal.value = false;
      taskStore.currentTask = null; // Clear current task
    };

    const closeCreateTaskModal = () => {
      showCreateTaskModal.value = false;
      createTaskError.value = null;
      // Reset form
      newTask.value = {
        description: '',
        input_data_json: '{}',
        priority: 'MEDIUM',
        timeout_seconds: 300,
        max_retries: 3
      };
    };

    const submitCreateTask = async () => {
      createTaskError.value = null;
      let inputData;
      try {
        inputData = JSON.parse(newTask.value.input_data_json);
      } catch (e) {
        createTaskError.value = 'Invalid JSON format for Input Data.';
        return;
      }

      const taskData = {
        description: newTask.value.description,
        input_data: inputData,
        priority: newTask.value.priority,
        timeout_seconds: newTask.value.timeout_seconds,
        max_retries: newTask.value.max_retries
      };

      const createdTask = await taskStore.createTask(taskData);
      if (createdTask) {
        closeCreateTaskModal();
        // Optionally poll for status updates
        // taskStore.pollTaskStatus(createdTask.task_id);
      } else {
        createTaskError.value = taskStore.error || 'Failed to create task.';
      }
    };

    return {
      taskStore,
      showCreateTaskModal,
      showTaskDetailsModal,
      newTask,
      createTaskError,
      refreshTasks,
      formatTimestamp,
      canCancel,
      cancelTask,
      viewTaskDetails,
      closeTaskDetailsModal,
      closeCreateTaskModal,
      submitCreateTask
    };
  }
};
</script>

<style scoped>
.tasks-container {
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

.task-list {
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 20px;
}

.task-list h2 {
  margin-top: 0;
  margin-bottom: 15px;
}

.loading-indicator,
.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--secondary-color);
}

.task-table {
  width: 100%;
  border-collapse: collapse;
}

.task-table th,
.task-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
}

.task-table th {
  background-color: var(--light-color);
  font-weight: bold;
}

.task-table tbody tr:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.task-table td button {
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
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: var(--border-radius);
}

.form-group textarea {
  resize: vertical;
}

.form-group small {
  color: var(--secondary-color);
  font-size: 12px;
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
}
</style>
