<template>
  <div class="knowledge-container">
    <h1>Knowledge & Context System</h1>
    
    <div class="actions">
      <button @click="showCreateEntityModal = true" class="btn btn-primary">Create Entity</button>
      <button @click="showCreateRelationModal = true" class="btn btn-secondary">Create Relation</button>
      <button @click="showQueryModal = true" class="btn btn-info">Query Knowledge</button>
    </div>
    
    <div v-if="knowledgeStore.error" class="error-message">
      {{ knowledgeStore.error }}
    </div>
    
    <div class="knowledge-graph-container">
      <h2>Knowledge Graph Visualization</h2>
      <div v-if="knowledgeStore.loading" class="loading-indicator">
        Loading knowledge graph...
      </div>
      <div v-else class="graph-container">
        <!-- Placeholder for graph visualization -->
        <div class="graph-placeholder">
          <p>Knowledge graph visualization will be displayed here</p>
          <p>This will use a graph visualization library like Cytoscape.js</p>
        </div>
      </div>
    </div>
    
    <div class="query-results" v-if="knowledgeStore.queryResults">
      <h2>Query Results</h2>
      <div class="results-container">
        <h3>Entities</h3>
        <table v-if="knowledgeStore.queryResults.entities && knowledgeStore.queryResults.entities.length" class="results-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Type</th>
              <th>Name</th>
              <th>Properties</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entity in knowledgeStore.queryResults.entities" :key="entity.entity_id">
              <td>{{ entity.entity_id }}</td>
              <td>{{ entity.entity_type }}</td>
              <td>{{ entity.name }}</td>
              <td>
                <pre>{{ JSON.stringify(entity.properties, null, 2) }}</pre>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state">No entities found.</div>
        
        <h3>Relations</h3>
        <table v-if="knowledgeStore.queryResults.relations && knowledgeStore.queryResults.relations.length" class="results-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Type</th>
              <th>Source</th>
              <th>Target</th>
              <th>Properties</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="relation in knowledgeStore.queryResults.relations" :key="relation.relation_id">
              <td>{{ relation.relation_id }}</td>
              <td>{{ relation.relation_type }}</td>
              <td>{{ relation.source_id }}</td>
              <td>{{ relation.target_id }}</td>
              <td>
                <pre>{{ JSON.stringify(relation.properties, null, 2) }}</pre>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state">No relations found.</div>
      </div>
    </div>

    <!-- Create Entity Modal -->
    <div v-if="showCreateEntityModal" class="modal-overlay" @click.self="closeCreateEntityModal">
      <div class="modal-content">
        <h2>Create New Entity</h2>
        <form @submit.prevent="submitCreateEntity">
          <div class="form-group">
            <label for="entity-type">Entity Type:</label>
            <select id="entity-type" v-model="newEntity.entity_type" required>
              <option value="concept">Concept</option>
              <option value="task">Task</option>
              <option value="agent">Agent</option>
              <option value="resource">Resource</option>
              <option value="event">Event</option>
            </select>
          </div>
          <div class="form-group">
            <label for="entity-name">Name:</label>
            <input type="text" id="entity-name" v-model="newEntity.name" required>
          </div>
          <div class="form-group">
            <label for="entity-properties">Properties (JSON):</label>
            <textarea id="entity-properties" v-model="newEntity.properties_json" rows="4"></textarea>
            <small>Enter valid JSON data or leave empty for no properties.</small>
          </div>
          <div class="form-actions">
            <button type="button" @click="closeCreateEntityModal" class="btn btn-secondary">Cancel</button>
            <button type="submit" :disabled="knowledgeStore.loading" class="btn btn-primary">
              {{ knowledgeStore.loading ? 'Creating...' : 'Create Entity' }}
            </button>
          </div>
          <div v-if="createEntityError" class="error-message">
            {{ createEntityError }}
          </div>
        </form>
      </div>
    </div>

    <!-- Create Relation Modal -->
    <div v-if="showCreateRelationModal" class="modal-overlay" @click.self="closeCreateRelationModal">
      <div class="modal-content">
        <h2>Create New Relation</h2>
        <form @submit.prevent="submitCreateRelation">
          <div class="form-group">
            <label for="relation-type">Relation Type:</label>
            <select id="relation-type" v-model="newRelation.relation_type" required>
              <option value="is_a">Is A</option>
              <option value="part_of">Part Of</option>
              <option value="related_to">Related To</option>
              <option value="depends_on">Depends On</option>
              <option value="created_by">Created By</option>
              <option value="used_by">Used By</option>
            </select>
          </div>
          <div class="form-group">
            <label for="source-id">Source Entity ID:</label>
            <input type="text" id="source-id" v-model="newRelation.source_id" required>
          </div>
          <div class="form-group">
            <label for="target-id">Target Entity ID:</label>
            <input type="text" id="target-id" v-model="newRelation.target_id" required>
          </div>
          <div class="form-group">
            <label for="relation-properties">Properties (JSON):</label>
            <textarea id="relation-properties" v-model="newRelation.properties_json" rows="4"></textarea>
            <small>Enter valid JSON data or leave empty for no properties.</small>
          </div>
          <div class="form-actions">
            <button type="button" @click="closeCreateRelationModal" class="btn btn-secondary">Cancel</button>
            <button type="submit" :disabled="knowledgeStore.loading" class="btn btn-primary">
              {{ knowledgeStore.loading ? 'Creating...' : 'Create Relation' }}
            </button>
          </div>
          <div v-if="createRelationError" class="error-message">
            {{ createRelationError }}
          </div>
        </form>
      </div>
    </div>

    <!-- Query Modal -->
    <div v-if="showQueryModal" class="modal-overlay" @click.self="closeQueryModal">
      <div class="modal-content">
        <h2>Query Knowledge Graph</h2>
        <form @submit.prevent="submitQuery">
          <div class="form-group">
            <label for="query-string">Query:</label>
            <input type="text" id="query-string" v-model="queryParams.query" required>
          </div>
          <div class="form-group">
            <label>Entity Types:</label>
            <div class="checkbox-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="entityTypeFilters.concept"> Concept
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="entityTypeFilters.task"> Task
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="entityTypeFilters.agent"> Agent
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="entityTypeFilters.resource"> Resource
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="entityTypeFilters.event"> Event
              </label>
            </div>
          </div>
          <div class="form-group">
            <label>Relation Types:</label>
            <div class="checkbox-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="relationTypeFilters.is_a"> Is A
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="relationTypeFilters.part_of"> Part Of
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="relationTypeFilters.related_to"> Related To
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="relationTypeFilters.depends_on"> Depends On
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="relationTypeFilters.created_by"> Created By
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="relationTypeFilters.used_by"> Used By
              </label>
            </div>
          </div>
          <div class="form-group">
            <label for="max-results">Max Results:</label>
            <input type="number" id="max-results" v-model.number="queryParams.max_results" min="1" max="1000">
          </div>
          <div class="form-actions">
            <button type="button" @click="closeQueryModal" class="btn btn-secondary">Cancel</button>
            <button type="submit" :disabled="knowledgeStore.loading" class="btn btn-primary">
              {{ knowledgeStore.loading ? 'Querying...' : 'Run Query' }}
            </button>
          </div>
          <div v-if="queryError" class="error-message">
            {{ queryError }}
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useKnowledgeStore } from '../store/knowledgeStore';

export default {
  name: 'KnowledgeView',
  setup() {
    const knowledgeStore = useKnowledgeStore();
    const showCreateEntityModal = ref(false);
    const showCreateRelationModal = ref(false);
    const showQueryModal = ref(false);
    const createEntityError = ref(null);
    const createRelationError = ref(null);
    const queryError = ref(null);
    
    const newEntity = ref({
      entity_type: 'concept',
      name: '',
      properties_json: '{}'
    });

    const newRelation = ref({
      relation_type: 'is_a',
      source_id: '',
      target_id: '',
      properties_json: '{}'
    });

    const entityTypeFilters = ref({
      concept: true,
      task: true,
      agent: true,
      resource: true,
      event: true
    });

    const relationTypeFilters = ref({
      is_a: true,
      part_of: true,
      related_to: true,
      depends_on: true,
      created_by: true,
      used_by: true
    });

    const queryParams = ref({
      query: '',
      max_results: 100
    });

    // Computed properties for selected entity and relation types
    const selectedEntityTypes = computed(() => {
      return Object.entries(entityTypeFilters.value)
        .filter(([_, selected]) => selected)
        .map(([type]) => type);
    });

    const selectedRelationTypes = computed(() => {
      return Object.entries(relationTypeFilters.value)
        .filter(([_, selected]) => selected)
        .map(([type]) => type);
    });

    // Close modals
    const closeCreateEntityModal = () => {
      showCreateEntityModal.value = false;
      createEntityError.value = null;
      newEntity.value = {
        entity_type: 'concept',
        name: '',
        properties_json: '{}'
      };
    };

    const closeCreateRelationModal = () => {
      showCreateRelationModal.value = false;
      createRelationError.value = null;
      newRelation.value = {
        relation_type: 'is_a',
        source_id: '',
        target_id: '',
        properties_json: '{}'
      };
    };

    const closeQueryModal = () => {
      showQueryModal.value = false;
      queryError.value = null;
    };

    // Submit functions
    const submitCreateEntity = async () => {
      createEntityError.value = null;
      let properties = {};
      
      if (newEntity.value.properties_json.trim()) {
        try {
          properties = JSON.parse(newEntity.value.properties_json);
        } catch (e) {
          createEntityError.value = 'Invalid JSON format for Properties.';
          return;
        }
      }

      const entityData = {
        entity_type: newEntity.value.entity_type,
        name: newEntity.value.name,
        properties: properties
      };

      const result = await knowledgeStore.createEntity(entityData);
      if (result) {
        closeCreateEntityModal();
      } else {
        createEntityError.value = knowledgeStore.error || 'Failed to create entity.';
      }
    };

    const submitCreateRelation = async () => {
      createRelationError.value = null;
      let properties = {};
      
      if (newRelation.value.properties_json.trim()) {
        try {
          properties = JSON.parse(newRelation.value.properties_json);
        } catch (e) {
          createRelationError.value = 'Invalid JSON format for Properties.';
          return;
        }
      }

      const relationData = {
        relation_type: newRelation.value.relation_type,
        source_id: newRelation.value.source_id,
        target_id: newRelation.value.target_id,
        properties: properties
      };

      const result = await knowledgeStore.createRelation(relationData);
      if (result) {
        closeCreateRelationModal();
      } else {
        createRelationError.value = knowledgeStore.error || 'Failed to create relation.';
      }
    };

    const submitQuery = async () => {
      queryError.value = null;
      
      const queryData = {
        query: queryParams.value.query,
        max_results: queryParams.value.max_results
      };

      // Add entity types filter if any are selected
      if (selectedEntityTypes.value.length > 0 && selectedEntityTypes.value.length < 5) {
        queryData.entity_types = selectedEntityTypes.value;
      }

      // Add relation types filter if any are selected
      if (selectedRelationTypes.value.length > 0 && selectedRelationTypes.value.length < 6) {
        queryData.relation_types = selectedRelationTypes.value;
      }

      const result = await knowledgeStore.queryKnowledge(queryData);
      if (result) {
        closeQueryModal();
      } else {
        queryError.value = knowledgeStore.error || 'Failed to query knowledge.';
      }
    };

    return {
      knowledgeStore,
      showCreateEntityModal,
      showCreateRelationModal,
      showQueryModal,
      newEntity,
      newRelation,
      queryParams,
      entityTypeFilters,
      relationTypeFilters,
      createEntityError,
      createRelationError,
      queryError,
      closeCreateEntityModal,
      closeCreateRelationModal,
      closeQueryModal,
      submitCreateEntity,
      submitCreateRelation,
      submitQuery
    };
  }
};
</script>

<style scoped>
.knowledge-container {
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

.knowledge-graph-container {
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 20px;
  margin-bottom: 20px;
}

.knowledge-graph-container h2 {
  margin-top: 0;
  margin-bottom: 15px;
}

.graph-container {
  width: 100%;
  height: 400px;
}

.graph-placeholder {
  width: 100%;
  height: 100%;
  background-color: var(--light-color);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--secondary-color);
  border-radius: var(--border-radius);
}

.loading-indicator,
.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--secondary-color);
}

.query-results {
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 20px;
}

.query-results h2 {
  margin-top: 0;
  margin-bottom: 15px;
}

.query-results h3 {
  margin-top: 20px;
  margin-bottom: 10px;
  border-bottom: 1px solid #eee;
  padding-bottom: 5px;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

.results-table th,
.results-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
}

.results-table th {
  background-color: var(--light-color);
  font-weight: bold;
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

.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 5px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  margin-right: 5px;
}

.form-actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

pre {
  background-color: var(--light-color);
  padding: 10px;
  border-radius: var(--border-radius);
  overflow-x: auto;
  font-size: 12px;
  max-height: 100px;
  overflow-y: auto;
}
</style>
