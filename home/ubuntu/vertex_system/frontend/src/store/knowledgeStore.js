import { defineStore } from 'pinia';
import axios from 'axios';

export const useKnowledgeStore = defineStore('knowledge', {
  state: () => ({
    entities: [],
    relations: [],
    queryResults: null,
    loading: false,
    error: null
  }),
  
  getters: {
    getEntityById: (state) => (id) => {
      return state.entities.find(entity => entity.entity_id === id);
    },
    
    getEntitiesByType: (state) => (type) => {
      return state.entities.filter(entity => entity.entity_type === type);
    },
    
    getRelationsBySourceId: (state) => (sourceId) => {
      return state.relations.filter(relation => relation.source_id === sourceId);
    },
    
    getRelationsByTargetId: (state) => (targetId) => {
      return state.relations.filter(relation => relation.target_id === targetId);
    }
  },
  
  actions: {
    async queryKnowledge(queryParams) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.post('/knowledge/query', queryParams);
        this.queryResults = response.data;
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.error?.message || 'Failed to query knowledge';
        console.error('Error querying knowledge:', error);
        return null;
      } finally {
        this.loading = false;
      }
    },
    
    async createEntity(entityData) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.post('/knowledge/entities', entityData);
        
        // Add entity ID to the entity data
        const newEntity = {
          ...entityData,
          entity_id: response.data.entity_id
        };
        
        // Add the new entity to the entities array
        this.entities.push(newEntity);
        
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.error?.message || 'Failed to create entity';
        console.error('Error creating entity:', error);
        return null;
      } finally {
        this.loading = false;
      }
    },
    
    async createRelation(relationData) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.post('/knowledge/relations', relationData);
        
        // Add relation ID to the relation data
        const newRelation = {
          ...relationData,
          relation_id: response.data.relation_id
        };
        
        // Add the new relation to the relations array
        this.relations.push(newRelation);
        
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.error?.message || 'Failed to create relation';
        console.error('Error creating relation:', error);
        return null;
      } finally {
        this.loading = false;
      }
    },
    
    // Helper method to build a graph structure for visualization
    buildGraphData() {
      const nodes = this.entities.map(entity => ({
        id: entity.entity_id,
        label: entity.name,
        type: entity.entity_type,
        properties: entity.properties
      }));
      
      const edges = this.relations.map(relation => ({
        id: relation.relation_id,
        source: relation.source_id,
        target: relation.target_id,
        label: relation.relation_type,
        properties: relation.properties
      }));
      
      return { nodes, edges };
    }
  }
});
