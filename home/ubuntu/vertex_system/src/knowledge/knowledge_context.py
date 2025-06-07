"""
Knowledge & Context System for Vertex Full-Stack System.

This module implements the knowledge graph memory integration, context-aware
memory management, and information retrieval components.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Set, Tuple
import time
import uuid
import json
from enum import Enum


class EntityType(Enum):
    """Enum representing different types of entities in the knowledge graph."""
    CONCEPT = "concept"
    TASK = "task"
    MODEL = "model"
    PROVIDER = "provider"
    STRATEGY = "strategy"
    TOOL = "tool"
    SERVER = "server"
    USER = "user"
    SESSION = "session"
    DOCUMENT = "document"


class RelationType(Enum):
    """Enum representing different types of relationships in the knowledge graph."""
    IS_A = "is_a"
    PART_OF = "part_of"
    DEPENDS_ON = "depends_on"
    CREATED_BY = "created_by"
    USED_BY = "used_by"
    RELATED_TO = "related_to"
    PRECEDES = "precedes"
    SUCCEEDS = "succeeds"
    SIMILAR_TO = "similar_to"
    CONTAINS = "contains"


class Entity:
    """
    Represents an entity in the knowledge graph.
    
    Entities are the nodes in the knowledge graph, representing concepts,
    tasks, models, or other objects.
    """
    
    def __init__(self,
                entity_id: Optional[str] = None,
                entity_type: EntityType = EntityType.CONCEPT,
                name: str = "",
                properties: Optional[Dict[str, Any]] = None,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize an entity.
        
        Args:
            entity_id: Optional unique identifier (generated if not provided)
            entity_type: Type of entity
            name: Human-readable name
            properties: Dictionary of entity properties
            metadata: Additional metadata
        """
        self.entity_id = entity_id or str(uuid.uuid4())
        self.entity_type = entity_type
        self.name = name
        self.properties = properties or {}
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.updated_at = self.created_at
    
    def update(self, 
              name: Optional[str] = None,
              properties: Optional[Dict[str, Any]] = None,
              metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update entity properties.
        
        Args:
            name: New name (if None, keep current)
            properties: New properties (if None, keep current)
            metadata: New metadata (if None, keep current)
        """
        if name is not None:
            self.name = name
            
        if properties is not None:
            self.properties = properties
            
        if metadata is not None:
            self.metadata = metadata
            
        self.updated_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert entity to dictionary representation.
        
        Returns:
            Dictionary containing all entity data
        """
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "name": self.name,
            "properties": self.properties,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """
        Create an entity from dictionary representation.
        
        Args:
            data: Dictionary containing entity data
            
        Returns:
            Entity instance
        """
        entity = cls(
            entity_id=data.get("entity_id"),
            entity_type=EntityType(data.get("entity_type", "concept")),
            name=data.get("name", ""),
            properties=data.get("properties", {}),
            metadata=data.get("metadata", {})
        )
        
        entity.created_at = data.get("created_at", time.time())
        entity.updated_at = data.get("updated_at", entity.created_at)
        
        return entity


class Relation:
    """
    Represents a relationship between entities in the knowledge graph.
    
    Relations are the edges in the knowledge graph, connecting entities
    with typed relationships.
    """
    
    def __init__(self,
                relation_id: Optional[str] = None,
                relation_type: RelationType = RelationType.RELATED_TO,
                source_id: str = "",
                target_id: str = "",
                properties: Optional[Dict[str, Any]] = None,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a relation.
        
        Args:
            relation_id: Optional unique identifier (generated if not provided)
            relation_type: Type of relation
            source_id: ID of the source entity
            target_id: ID of the target entity
            properties: Dictionary of relation properties
            metadata: Additional metadata
        """
        self.relation_id = relation_id or str(uuid.uuid4())
        self.relation_type = relation_type
        self.source_id = source_id
        self.target_id = target_id
        self.properties = properties or {}
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.updated_at = self.created_at
    
    def update(self, 
              relation_type: Optional[RelationType] = None,
              properties: Optional[Dict[str, Any]] = None,
              metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update relation properties.
        
        Args:
            relation_type: New relation type (if None, keep current)
            properties: New properties (if None, keep current)
            metadata: New metadata (if None, keep current)
        """
        if relation_type is not None:
            self.relation_type = relation_type
            
        if properties is not None:
            self.properties = properties
            
        if metadata is not None:
            self.metadata = metadata
            
        self.updated_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert relation to dictionary representation.
        
        Returns:
            Dictionary containing all relation data
        """
        return {
            "relation_id": self.relation_id,
            "relation_type": self.relation_type.value,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "properties": self.properties,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Relation':
        """
        Create a relation from dictionary representation.
        
        Args:
            data: Dictionary containing relation data
            
        Returns:
            Relation instance
        """
        relation = cls(
            relation_id=data.get("relation_id"),
            relation_type=RelationType(data.get("relation_type", "related_to")),
            source_id=data.get("source_id", ""),
            target_id=data.get("target_id", ""),
            properties=data.get("properties", {}),
            metadata=data.get("metadata", {})
        )
        
        relation.created_at = data.get("created_at", time.time())
        relation.updated_at = data.get("updated_at", relation.created_at)
        
        return relation


class Observation:
    """
    Represents an observation about entities or relations.
    
    Observations are facts or statements about entities or relations,
    with associated confidence and source information.
    """
    
    def __init__(self,
                observation_id: Optional[str] = None,
                entity_id: Optional[str] = None,
                relation_id: Optional[str] = None,
                content: str = "",
                confidence: float = 1.0,
                source: str = "",
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize an observation.
        
        Args:
            observation_id: Optional unique identifier (generated if not provided)
            entity_id: Optional ID of the entity this observation is about
            relation_id: Optional ID of the relation this observation is about
            content: Observation content
            confidence: Confidence score (0.0 to 1.0)
            source: Source of the observation
            metadata: Additional metadata
        """
        self.observation_id = observation_id or str(uuid.uuid4())
        self.entity_id = entity_id
        self.relation_id = relation_id
        self.content = content
        self.confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        self.source = source
        self.metadata = metadata or {}
        self.created_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert observation to dictionary representation.
        
        Returns:
            Dictionary containing all observation data
        """
        return {
            "observation_id": self.observation_id,
            "entity_id": self.entity_id,
            "relation_id": self.relation_id,
            "content": self.content,
            "confidence": self.confidence,
            "source": self.source,
            "metadata": self.metadata,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Observation':
        """
        Create an observation from dictionary representation.
        
        Args:
            data: Dictionary containing observation data
            
        Returns:
            Observation instance
        """
        observation = cls(
            observation_id=data.get("observation_id"),
            entity_id=data.get("entity_id"),
            relation_id=data.get("relation_id"),
            content=data.get("content", ""),
            confidence=data.get("confidence", 1.0),
            source=data.get("source", ""),
            metadata=data.get("metadata", {})
        )
        
        observation.created_at = data.get("created_at", time.time())
        
        return observation


class KnowledgeGraph:
    """
    Knowledge graph for storing entities, relations, and observations.
    
    This class provides methods for creating, querying, and managing
    a knowledge graph.
    """
    
    def __init__(self):
        """Initialize an empty knowledge graph."""
        self.entities = {}  # entity_id -> Entity
        self.relations = {}  # relation_id -> Relation
        self.observations = {}  # observation_id -> Observation
        
        # Indexes for efficient querying
        self.entity_type_index = {}  # entity_type -> Set[entity_id]
        self.relation_type_index = {}  # relation_type -> Set[relation_id]
        self.source_index = {}  # source_id -> Set[relation_id]
        self.target_index = {}  # target_id -> Set[relation_id]
        self.entity_observation_index = {}  # entity_id -> Set[observation_id]
        self.relation_observation_index = {}  # relation_id -> Set[observation_id]
    
    def add_entity(self, entity: Entity) -> str:
        """
        Add an entity to the knowledge graph.
        
        Args:
            entity: Entity to add
            
        Returns:
            Entity ID
            
        Raises:
            ValueError: If entity with same ID already exists
        """
        if entity.entity_id in self.entities:
            raise ValueError(f"Entity with ID '{entity.entity_id}' already exists")
        
        self.entities[entity.entity_id] = entity
        
        # Update indexes
        entity_type = entity.entity_type
        if entity_type not in self.entity_type_index:
            self.entity_type_index[entity_type] = set()
        self.entity_type_index[entity_type].add(entity.entity_id)
        
        return entity.entity_id
    
    def add_relation(self, relation: Relation) -> str:
        """
        Add a relation to the knowledge graph.
        
        Args:
            relation: Relation to add
            
        Returns:
            Relation ID
            
        Raises:
            ValueError: If relation with same ID already exists
            KeyError: If source or target entity does not exist
        """
        if relation.relation_id in self.relations:
            raise ValueError(f"Relation with ID '{relation.relation_id}' already exists")
        
        if relation.source_id not in self.entities:
            raise KeyError(f"Source entity '{relation.source_id}' does not exist")
        
        if relation.target_id not in self.entities:
            raise KeyError(f"Target entity '{relation.target_id}' does not exist")
        
        self.relations[relation.relation_id] = relation
        
        # Update indexes
        relation_type = relation.relation_type
        if relation_type not in self.relation_type_index:
            self.relation_type_index[relation_type] = set()
        self.relation_type_index[relation_type].add(relation.relation_id)
        
        source_id = relation.source_id
        if source_id not in self.source_index:
            self.source_index[source_id] = set()
        self.source_index[source_id].add(relation.relation_id)
        
        target_id = relation.target_id
        if target_id not in self.target_index:
            self.target_index[target_id] = set()
        self.target_index[target_id].add(relation.relation_id)
        
        return relation.relation_id
    
    def add_observation(self, observation: Observation) -> str:
        """
        Add an observation to the knowledge graph.
        
        Args:
            observation: Observation to add
            
        Returns:
            Observation ID
            
        Raises:
            ValueError: If observation with same ID already exists
            KeyError: If referenced entity or relation does not exist
        """
        if observation.observation_id in self.observations:
            raise ValueError(f"Observation with ID '{observation.observation_id}' already exists")
        
        if observation.entity_id is not None and observation.entity_id not in self.entities:
            raise KeyError(f"Entity '{observation.entity_id}' does not exist")
        
        if observation.relation_id is not None and observation.relation_id not in self.relations:
            raise KeyError(f"Relation '{observation.relation_id}' does not exist")
        
        self.observations[observation.observation_id] = observation
        
        # Update indexes
        if observation.entity_id is not None:
            entity_id = observation.entity_id
            if entity_id not in self.entity_observation_index:
                self.entity_observation_index[entity_id] = set()
            self.entity_observation_index[entity_id].add(observation.observation_id)
        
        if observation.relation_id is not None:
            relation_id = observation.relation_id
            if relation_id not in self.relation_observation_index:
                self.relation_observation_index[relation_id] = set()
            self.relation_observation_index[relation_id].add(observation.observation_id)
        
        return observation.observation_id
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """
        Get an entity by ID.
        
        Args:
            entity_id: ID of the entity
            
        Returns:
            Entity instance or None if not found
        """
        return self.entities.get(entity_id)
    
    def get_relation(self, relation_id: str) -> Optional[Relation]:
        """
        Get a relation by ID.
        
        Args:
            relation_id: ID of the relation
            
        Returns:
            Relation instance or None if not found
        """
        return self.relations.get(relation_id)
    
    def get_observation(self, observation_id: str) -> Optional[Observation]:
        """
        Get an observation by ID.
        
        Args:
            observation_id: ID of the observation
            
        Returns:
            Observation instance or None if not found
        """
        return self.observations.get(observation_id)
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """
        Get all entities of a specific type.
        
        Args:
            entity_type: Type of entities to retrieve
            
        Returns:
            List of Entity instances
        """
        entity_ids = self.entity_type_index.get(entity_type, set())
        return [self.entities[entity_id] for entity_id in entity_ids]
    
    def get_relations_by_type(self, relation_type: RelationType) -> List[Relation]:
        """
        Get all relations of a specific type.
        
        Args:
            relation_type: Type of relations to retrieve
            
        Returns:
            List of Relation instances
        """
        relation_ids = self.relation_type_index.get(relation_type, set())
        return [self.relations[relation_id] for relation_id in relation_ids]
    
    def get_relations_from_entity(self, entity_id: str) -> List[Relation]:
        """
        Get all relations where an entity is the source.
        
        Args:
            entity_id: ID of the source entity
            
        Returns:
            List of Relation instances
        """
        relation_ids = self.source_index.get(entity_id, set())
        return [self.relations[relation_id] for relation_id in relation_ids]
    
    def get_relations_to_entity(self, entity_id: str) -> List[Relation]:
        """
        Get all relations where an entity is the target.
        
        Args:
            entity_id: ID of the target entity
            
        Returns:
            List of Relation instances
        """
        relation_ids = self.target_index.get(entity_id, set())
        return [self.relations[relation_id] for relation_id in relation_ids]
    
    def get_observations_for_entity(self, entity_id: str) -> List[Observation]:
        """
        Get all observations about an entity.
        
        Args:
            entity_id: ID of the entity
            
        Returns:
            List of Observation instances
        """
        observation_ids = self.entity_observation_index.get(entity_id, set())
        return [self.observations[observation_id] for observation_id in observation_ids]
    
    def get_observations_for_relation(self, relation_id: str) -> List[Observation]:
        """
        Get all observations about a relation.
        
        Args:
            relation_id: ID of the relation
            
        Returns:
            List of Observation instances
        """
        observation_ids = self.relation_observation_index.get(relation_id, set())
        return [self.observations[observation_id] for observation_id in observation_ids]
    
    def update_entity(self, 
                     entity_id: str,
                     name: Optional[str] = None,
                     properties: Optional[Dict[str, Any]] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update an entity.
        
        Args:
            entity_id: ID of the entity to update
            name: New name (if None, keep current)
            properties: New properties (if None, keep current)
            metadata: New metadata (if None, keep current)
            
        Returns:
            True if entity was updated, False if not found
        """
        entity = self.get_entity(entity_id)
        if not entity:
            return False
            
        entity.update(name, properties, metadata)
        return True
    
    def update_relation(self, 
                       relation_id: str,
                       relation_type: Optional[RelationType] = None,
                       properties: Optional[Dict[str, Any]] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update a relation.
        
        Args:
            relation_id: ID of the relation to update
            relation_type: New relation type (if None, keep current)
            properties: New properties (if None, keep current)
            metadata: New metadata (if None, keep current)
            
        Returns:
            True if relation was updated, False if not found
        """
        relation = self.get_relation(relation_id)
        if not relation:
            return False
            
        relation.update(relation_type, properties, metadata)
        return True
    
    def delete_entity(self, entity_id: str) -> bool:
        """
        Delete an entity and all its relations and observations.
        
        Args:
            entity_id: ID of the entity to delete
            
        Returns:
            True if entity was deleted, False if not found
        """
        entity = self.get_entity(entity_id)
        if not entity:
            return False
            
        # Delete relations where this entity is source or target
        source_relations = self.get_relations_from_entity(entity_id)
        target_relations = self.get_relations_to_entity(entity_id)
        
        for relation in source_relations + target_relations:
            self.delete_relation(relation.relation_id)
            
        # Delete observations about this entity
        observations = self.get_observations_for_entity(entity_id)
        for observation in observations:
            self.delete_observation(observation.observation_id)
            
        # Remove from indexes
        self.entity_type_index[entity.entity_type].remove(entity_id)
        if entity_id in self.source_index:
            del self.source_index[entity_id]
        if entity_id in self.target_index:
            del self.target_index[entity_id]
        if entity_id in self.entity_observation_index:
            del self.entity_observation_index[entity_id]
            
        # Remove entity
        del self.entities[entity_id]
        
        return True
    
    def delete_relation(self, relation_id: str) -> bool:
        """
        Delete a relation and all its observations.
        
        Args:
            relation_id: ID of the relation to delete
            
        Returns:
            True if relation was deleted, False if not found
        """
        relation = self.get_relation(relation_id)
        if not relation:
            return False
            
        # Delete observations about this relation
        observations = self.get_observations_for_relation(relation_id)
        for observation in observations:
            self.delete_observation(observation.observation_id)
            
        # Remove from indexes
        self.relation_type_index[relation.relation_type].remove(relation_id)
        self.source_index[relation.source_id].remove(relation_id)
        self.target_index[relation.target_id].remove(relation_id)
        if relation_id in self.relation_observation_index:
            del self.relation_observation_index[relation_id]
            
        # Remove relation
        del self.relations[relation_id]
        
        return True
    
    def delete_observation(self, observation_id: str) -> bool:
        """
        Delete an observation.
        
        Args:
            observation_id: ID of the observation to delete
            
        Returns:
            True if observation was deleted, False if not found
        """
        observation = self.get_observation(observation_id)
        if not observation:
            return False
            
        # Remove from indexes
        if observation.entity_id is not None:
            self.entity_observation_index[observation.entity_id].remove(observation_id)
        if observation.relation_id is not None:
            self.relation_observation_index[observation.relation_id].remove(observation_id)
            
        # Remove observation
        del self.observations[observation_id]
        
        return True
    
    def query(self, 
             entity_types: Optional[List[EntityType]] = None,
             relation_types: Optional[List[RelationType]] = None,
             properties: Optional[Dict[str, Any]] = None,
             max_results: int = 100) -> Dict[str, List[Union[Entity, Relation]]]:
        """
        Query the knowledge graph for entities and relations.
        
        Args:
            entity_types: Optional list of entity types to filter by
            relation_types: Optional list of relation types to filter by
            properties: Optional dictionary of properties to match
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with 'entities' and 'relations' lists
        """
        entities = []
        relations = []
        
        # Filter entities by type
        if entity_types:
            entity_ids = set()
            for entity_type in entity_types:
                entity_ids.update(self.entity_type_index.get(entity_type, set()))
        else:
            entity_ids = set(self.entities.keys())
            
        # Filter relations by type
        if relation_types:
            relation_ids = set()
            for relation_type in relation_types:
                relation_ids.update(self.relation_type_index.get(relation_type, set()))
        else:
            relation_ids = set(self.relations.keys())
            
        # Filter by properties
        if properties:
            filtered_entity_ids = set()
            for entity_id in entity_ids:
                entity = self.entities[entity_id]
                if all(entity.properties.get(k) == v for k, v in properties.items()):
                    filtered_entity_ids.add(entity_id)
            entity_ids = filtered_entity_ids
            
            filtered_relation_ids = set()
            for relation_id in relation_ids:
                relation = self.relations[relation_id]
                if all(relation.properties.get(k) == v for k, v in properties.items()):
                    filtered_relation_ids.add(relation_id)
            relation_ids = filtered_relation_ids
            
        # Collect results
        for entity_id in list(entity_ids)[:max_results]:
            entities.append(self.entities[entity_id])
            
        for relation_id in list(relation_ids)[:max_results]:
            relations.append(self.relations[relation_id])
            
        return {
            "entities": entities,
            "relations": relations
        }
    
    def traverse(self, 
                start_entity_id: str,
                relation_types: Optional[List[RelationType]] = None,
                max_depth: int = 3,
                max_results: int = 100) -> Dict[str, List[Union[Entity, Relation]]]:
        """
        Traverse the knowledge graph starting from an entity.
        
        Args:
            start_entity_id: ID of the starting entity
            relation_types: Optional list of relation types to follow
            max_depth: Maximum traversal depth
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with 'entities' and 'relations' lists
            
        Raises:
            KeyError: If start entity does not exist
        """
        if start_entity_id not in self.entities:
            raise KeyError(f"Start entity '{start_entity_id}' does not exist")
            
        visited_entities = set([start_entity_id])
        visited_relations = set()
        result_entities = [self.entities[start_entity_id]]
        result_relations = []
        
        # Breadth-first traversal
        queue = [(start_entity_id, 0)]  # (entity_id, depth)
        
        while queue and len(result_entities) < max_results:
            current_id, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue
                
            # Get outgoing relations
            outgoing_relations = self.get_relations_from_entity(current_id)
            
            # Filter by relation type if specified
            if relation_types:
                outgoing_relations = [
                    r for r in outgoing_relations
                    if r.relation_type in relation_types
                ]
                
            for relation in outgoing_relations:
                if relation.relation_id in visited_relations:
                    continue
                    
                visited_relations.add(relation.relation_id)
                result_relations.append(relation)
                
                target_id = relation.target_id
                if target_id not in visited_entities:
                    visited_entities.add(target_id)
                    result_entities.append(self.entities[target_id])
                    queue.append((target_id, depth + 1))
                    
        return {
            "entities": result_entities[:max_results],
            "relations": result_relations[:max_results]
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the knowledge graph to a dictionary representation.
        
        Returns:
            Dictionary containing all graph data
        """
        return {
            "entities": {
                entity_id: entity.to_dict()
                for entity_id, entity in self.entities.items()
            },
            "relations": {
                relation_id: relation.to_dict()
                for relation_id, relation in self.relations.items()
            },
            "observations": {
                observation_id: observation.to_dict()
                for observation_id, observation in self.observations.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeGraph':
        """
        Create a knowledge graph from dictionary representation.
        
        Args:
            data: Dictionary containing graph data
            
        Returns:
            KnowledgeGraph instance
        """
        graph = cls()
        
        # Load entities first
        for entity_id, entity_data in data.get("entities", {}).items():
            entity = Entity.from_dict(entity_data)
            graph.entities[entity_id] = entity
            
            # Update indexes
            entity_type = entity.entity_type
            if entity_type not in graph.entity_type_index:
                graph.entity_type_index[entity_type] = set()
            graph.entity_type_index[entity_type].add(entity_id)
            
        # Load relations
        for relation_id, relation_data in data.get("relations", {}).items():
            relation = Relation.from_dict(relation_data)
            graph.relations[relation_id] = relation
            
            # Update indexes
            relation_type = relation.relation_type
            if relation_type not in graph.relation_type_index:
                graph.relation_type_index[relation_type] = set()
            graph.relation_type_index[relation_type].add(relation_id)
            
            source_id = relation.source_id
            if source_id not in graph.source_index:
                graph.source_index[source_id] = set()
            graph.source_index[source_id].add(relation_id)
            
            target_id = relation.target_id
            if target_id not in graph.target_index:
                graph.target_index[target_id] = set()
            graph.target_index[target_id].add(relation_id)
            
        # Load observations
        for observation_id, observation_data in data.get("observations", {}).items():
            observation = Observation.from_dict(observation_data)
            graph.observations[observation_id] = observation
            
            # Update indexes
            if observation.entity_id is not None:
                entity_id = observation.entity_id
                if entity_id not in graph.entity_observation_index:
                    graph.entity_observation_index[entity_id] = set()
                graph.entity_observation_index[entity_id].add(observation_id)
            
            if observation.relation_id is not None:
                relation_id = observation.relation_id
                if relation_id not in graph.relation_observation_index:
                    graph.relation_observation_index[relation_id] = set()
                graph.relation_observation_index[relation_id].add(observation_id)
            
        return graph


class MemoryManager:
    """
    Manages memory persistence and retrieval.
    
    This class handles saving and loading knowledge graphs, as well as
    memory optimization through pruning and compression.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize memory manager.
        
        Args:
            storage_path: Optional path for persistent storage
        """
        self.storage_path = storage_path
        self.current_graph = KnowledgeGraph()
        self.session_graphs = {}  # session_id -> KnowledgeGraph
    
    def save_graph(self, graph_id: str, graph: KnowledgeGraph) -> bool:
        """
        Save a knowledge graph.
        
        Args:
            graph_id: ID for the saved graph
            graph: KnowledgeGraph instance to save
            
        Returns:
            True if save was successful, False otherwise
        """
        if not self.storage_path:
            return False
            
        try:
            graph_data = graph.to_dict()
            file_path = f"{self.storage_path}/{graph_id}.json"
            
            with open(file_path, 'w') as f:
                json.dump(graph_data, f)
                
            return True
        except Exception:
            return False
    
    def load_graph(self, graph_id: str) -> Optional[KnowledgeGraph]:
        """
        Load a knowledge graph.
        
        Args:
            graph_id: ID of the graph to load
            
        Returns:
            KnowledgeGraph instance or None if load failed
        """
        if not self.storage_path:
            return None
            
        try:
            file_path = f"{self.storage_path}/{graph_id}.json"
            
            with open(file_path, 'r') as f:
                graph_data = json.load(f)
                
            return KnowledgeGraph.from_dict(graph_data)
        except Exception:
            return None
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        Create a new session with its own knowledge graph.
        
        Args:
            session_id: Optional session ID (generated if not provided)
            
        Returns:
            Session ID
        """
        session_id = session_id or str(uuid.uuid4())
        self.session_graphs[session_id] = KnowledgeGraph()
        return session_id
    
    def get_session_graph(self, session_id: str) -> Optional[KnowledgeGraph]:
        """
        Get the knowledge graph for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            KnowledgeGraph instance or None if session not found
        """
        return self.session_graphs.get(session_id)
    
    def merge_session(self, session_id: str) -> bool:
        """
        Merge a session's knowledge graph into the current graph.
        
        Args:
            session_id: ID of the session to merge
            
        Returns:
            True if merge was successful, False otherwise
        """
        session_graph = self.get_session_graph(session_id)
        if not session_graph:
            return False
            
        # Merge entities
        for entity_id, entity in session_graph.entities.items():
            if entity_id not in self.current_graph.entities:
                try:
                    self.current_graph.add_entity(entity)
                except ValueError:
                    # Entity already exists, skip
                    pass
                    
        # Merge relations
        for relation_id, relation in session_graph.relations.items():
            if relation_id not in self.current_graph.relations:
                try:
                    self.current_graph.add_relation(relation)
                except (ValueError, KeyError):
                    # Relation already exists or references missing entities, skip
                    pass
                    
        # Merge observations
        for observation_id, observation in session_graph.observations.items():
            if observation_id not in self.current_graph.observations:
                try:
                    self.current_graph.add_observation(observation)
                except (ValueError, KeyError):
                    # Observation already exists or references missing entities/relations, skip
                    pass
                    
        return True
    
    def prune_graph(self, 
                   min_confidence: float = 0.5,
                   max_age: Optional[float] = None) -> int:
        """
        Prune the current knowledge graph.
        
        Args:
            min_confidence: Minimum confidence for observations to keep
            max_age: Maximum age in seconds for entities/relations to keep
            
        Returns:
            Number of items pruned
        """
        pruned_count = 0
        current_time = time.time()
        
        # Prune observations by confidence
        low_confidence_observations = [
            observation_id for observation_id, observation in self.current_graph.observations.items()
            if observation.confidence < min_confidence
        ]
        
        for observation_id in low_confidence_observations:
            if self.current_graph.delete_observation(observation_id):
                pruned_count += 1
                
        # Prune by age if specified
        if max_age is not None:
            cutoff_time = current_time - max_age
            
            # Prune old entities
            old_entities = [
                entity_id for entity_id, entity in self.current_graph.entities.items()
                if entity.updated_at < cutoff_time
            ]
            
            for entity_id in old_entities:
                if self.current_graph.delete_entity(entity_id):
                    pruned_count += 1
                    
            # Prune old relations
            old_relations = [
                relation_id for relation_id, relation in self.current_graph.relations.items()
                if relation.updated_at < cutoff_time
            ]
            
            for relation_id in old_relations:
                if self.current_graph.delete_relation(relation_id):
                    pruned_count += 1
                    
        return pruned_count
    
    def compress_memory(self) -> Dict[str, Any]:
        """
        Compress the current knowledge graph by merging similar entities.
        
        Returns:
            Dictionary with compression statistics
        """
        # Find similar entities based on name and properties
        entity_groups = {}  # name -> List[entity_id]
        
        for entity_id, entity in self.current_graph.entities.items():
            name = entity.name.lower()
            if name not in entity_groups:
                entity_groups[name] = []
            entity_groups[name].append(entity_id)
            
        # Merge entities with same name
        merged_count = 0
        for name, entity_ids in entity_groups.items():
            if len(entity_ids) <= 1:
                continue
                
            # Keep the most recently updated entity
            entity_ids.sort(
                key=lambda eid: self.current_graph.entities[eid].updated_at,
                reverse=True
            )
            
            keep_id = entity_ids[0]
            merge_ids = entity_ids[1:]
            
            for merge_id in merge_ids:
                # Redirect relations
                source_relations = self.current_graph.get_relations_from_entity(merge_id)
                target_relations = self.current_graph.get_relations_to_entity(merge_id)
                
                for relation in source_relations:
                    # Create new relation with keep_id as source
                    new_relation = Relation(
                        relation_type=relation.relation_type,
                        source_id=keep_id,
                        target_id=relation.target_id,
                        properties=relation.properties,
                        metadata=relation.metadata
                    )
                    
                    try:
                        self.current_graph.add_relation(new_relation)
                    except (ValueError, KeyError):
                        # Relation already exists or references missing entities, skip
                        pass
                        
                for relation in target_relations:
                    # Create new relation with keep_id as target
                    new_relation = Relation(
                        relation_type=relation.relation_type,
                        source_id=relation.source_id,
                        target_id=keep_id,
                        properties=relation.properties,
                        metadata=relation.metadata
                    )
                    
                    try:
                        self.current_graph.add_relation(new_relation)
                    except (ValueError, KeyError):
                        # Relation already exists or references missing entities, skip
                        pass
                        
                # Redirect observations
                observations = self.current_graph.get_observations_for_entity(merge_id)
                
                for observation in observations:
                    # Create new observation for keep_id
                    new_observation = Observation(
                        entity_id=keep_id,
                        content=observation.content,
                        confidence=observation.confidence,
                        source=observation.source,
                        metadata=observation.metadata
                    )
                    
                    try:
                        self.current_graph.add_observation(new_observation)
                    except (ValueError, KeyError):
                        # Observation already exists or references missing entities, skip
                        pass
                        
                # Delete the merged entity
                self.current_graph.delete_entity(merge_id)
                merged_count += 1
                
        return {
            "merged_entities": merged_count,
            "remaining_entities": len(self.current_graph.entities),
            "remaining_relations": len(self.current_graph.relations),
            "remaining_observations": len(self.current_graph.observations)
        }


class ContextManager:
    """
    Manages context for tasks and sessions.
    
    This class handles context preservation, retrieval, and relevance
    determination.
    """
    
    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize context manager.
        
        Args:
            memory_manager: MemoryManager instance
        """
        self.memory_manager = memory_manager
        self.active_contexts = {}  # context_id -> Dict[str, Any]
    
    def create_context(self, 
                      context_id: Optional[str] = None,
                      session_id: Optional[str] = None,
                      initial_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new context.
        
        Args:
            context_id: Optional context ID (generated if not provided)
            session_id: Optional session ID to associate with this context
            initial_data: Optional initial context data
            
        Returns:
            Context ID
        """
        context_id = context_id or str(uuid.uuid4())
        
        self.active_contexts[context_id] = {
            "session_id": session_id,
            "created_at": time.time(),
            "updated_at": time.time(),
            "data": initial_data or {},
            "history": []
        }
        
        return context_id
    
    def update_context(self, 
                      context_id: str,
                      data: Dict[str, Any],
                      merge: bool = True) -> bool:
        """
        Update a context with new data.
        
        Args:
            context_id: ID of the context to update
            data: New context data
            merge: If True, merge with existing data; if False, replace
            
        Returns:
            True if update was successful, False if context not found
        """
        if context_id not in self.active_contexts:
            return False
            
        context = self.active_contexts[context_id]
        
        # Save current state in history
        context["history"].append({
            "timestamp": time.time(),
            "data": context["data"].copy()
        })
        
        # Update data
        if merge:
            context["data"].update(data)
        else:
            context["data"] = data
            
        context["updated_at"] = time.time()
        
        return True
    
    def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a context by ID.
        
        Args:
            context_id: ID of the context
            
        Returns:
            Context data or None if not found
        """
        if context_id not in self.active_contexts:
            return None
            
        return self.active_contexts[context_id]["data"].copy()
    
    def get_context_history(self, 
                          context_id: str,
                          max_entries: int = 10) -> List[Dict[str, Any]]:
        """
        Get the history of a context.
        
        Args:
            context_id: ID of the context
            max_entries: Maximum number of history entries to return
            
        Returns:
            List of historical context states or empty list if context not found
        """
        if context_id not in self.active_contexts:
            return []
            
        history = self.active_contexts[context_id]["history"]
        
        # Return most recent entries first
        return sorted(
            history[-max_entries:],
            key=lambda entry: entry["timestamp"],
            reverse=True
        )
    
    def enrich_context(self, 
                      context_id: str,
                      query: str,
                      max_results: int = 10) -> bool:
        """
        Enrich a context with relevant information from the knowledge graph.
        
        Args:
            context_id: ID of the context to enrich
            query: Query string to find relevant information
            max_results: Maximum number of results to add
            
        Returns:
            True if enrichment was successful, False if context not found
        """
        if context_id not in self.active_contexts:
            return False
            
        context = self.active_contexts[context_id]
        session_id = context.get("session_id")
        
        # Get the appropriate knowledge graph
        if session_id and session_id in self.memory_manager.session_graphs:
            graph = self.memory_manager.session_graphs[session_id]
        else:
            graph = self.memory_manager.current_graph
            
        # Simple keyword matching for now
        # In a real implementation, this would use more sophisticated retrieval
        keywords = query.lower().split()
        
        matching_entities = []
        for entity_id, entity in graph.entities.items():
            entity_text = f"{entity.name} {json.dumps(entity.properties)}".lower()
            if any(keyword in entity_text for keyword in keywords):
                matching_entities.append(entity)
                
        matching_observations = []
        for observation_id, observation in graph.observations.items():
            if any(keyword in observation.content.lower() for keyword in keywords):
                matching_observations.append(observation)
                
        # Add to context
        if "relevant_entities" not in context["data"]:
            context["data"]["relevant_entities"] = []
            
        if "relevant_observations" not in context["data"]:
            context["data"]["relevant_observations"] = []
            
        # Add new entities and observations
        for entity in matching_entities[:max_results]:
            context["data"]["relevant_entities"].append(entity.to_dict())
            
        for observation in matching_observations[:max_results]:
            context["data"]["relevant_observations"].append(observation.to_dict())
            
        context["updated_at"] = time.time()
        
        return True
    
    def persist_context(self, context_id: str) -> bool:
        """
        Persist a context to the knowledge graph.
        
        Args:
            context_id: ID of the context to persist
            
        Returns:
            True if persistence was successful, False if context not found
        """
        if context_id not in self.active_contexts:
            return False
            
        context = self.active_contexts[context_id]
        session_id = context.get("session_id")
        
        # Get the appropriate knowledge graph
        if session_id and session_id in self.memory_manager.session_graphs:
            graph = self.memory_manager.session_graphs[session_id]
        else:
            graph = self.memory_manager.current_graph
            
        # Create a context entity
        context_entity = Entity(
            entity_type=EntityType.SESSION,
            name=f"Context {context_id}",
            properties={
                "context_id": context_id,
                "session_id": session_id,
                "created_at": context["created_at"],
                "updated_at": context["updated_at"]
            },
            metadata={
                "type": "context"
            }
        )
        
        try:
            context_entity_id = graph.add_entity(context_entity)
            
            # Create observations for context data
            for key, value in context["data"].items():
                if key not in ["relevant_entities", "relevant_observations"]:
                    observation = Observation(
                        entity_id=context_entity_id,
                        content=f"{key}: {json.dumps(value)}",
                        confidence=1.0,
                        source="context_manager"
                    )
                    
                    graph.add_observation(observation)
                    
            return True
        except Exception:
            return False
    
    def delete_context(self, context_id: str) -> bool:
        """
        Delete a context.
        
        Args:
            context_id: ID of the context to delete
            
        Returns:
            True if deletion was successful, False if context not found
        """
        if context_id not in self.active_contexts:
            return False
            
        del self.active_contexts[context_id]
        return True


class KnowledgeContextSystem:
    """
    Main entry point for the Knowledge & Context System.
    
    Coordinates knowledge graph operations, memory management, and
    context handling.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the knowledge and context system.
        
        Args:
            storage_path: Optional path for persistent storage
        """
        self.memory_manager = MemoryManager(storage_path)
        self.context_manager = ContextManager(self.memory_manager)
    
    def create_entity(self, 
                     entity_type: EntityType,
                     name: str,
                     properties: Optional[Dict[str, Any]] = None,
                     session_id: Optional[str] = None) -> str:
        """
        Create an entity in the knowledge graph.
        
        Args:
            entity_type: Type of entity
            name: Entity name
            properties: Optional entity properties
            session_id: Optional session ID (uses current graph if None)
            
        Returns:
            Entity ID
            
        Raises:
            ValueError: If entity creation fails
        """
        entity = Entity(
            entity_type=entity_type,
            name=name,
            properties=properties or {}
        )
        
        graph = self._get_graph(session_id)
        return graph.add_entity(entity)
    
    def create_relation(self, 
                       relation_type: RelationType,
                       source_id: str,
                       target_id: str,
                       properties: Optional[Dict[str, Any]] = None,
                       session_id: Optional[str] = None) -> str:
        """
        Create a relation in the knowledge graph.
        
        Args:
            relation_type: Type of relation
            source_id: ID of source entity
            target_id: ID of target entity
            properties: Optional relation properties
            session_id: Optional session ID (uses current graph if None)
            
        Returns:
            Relation ID
            
        Raises:
            ValueError: If relation creation fails
            KeyError: If source or target entity does not exist
        """
        relation = Relation(
            relation_type=relation_type,
            source_id=source_id,
            target_id=target_id,
            properties=properties or {}
        )
        
        graph = self._get_graph(session_id)
        return graph.add_relation(relation)
    
    def add_observation(self, 
                       content: str,
                       entity_id: Optional[str] = None,
                       relation_id: Optional[str] = None,
                       confidence: float = 1.0,
                       source: str = "system",
                       session_id: Optional[str] = None) -> str:
        """
        Add an observation to the knowledge graph.
        
        Args:
            content: Observation content
            entity_id: Optional ID of the entity this observation is about
            relation_id: Optional ID of the relation this observation is about
            confidence: Confidence score (0.0 to 1.0)
            source: Source of the observation
            session_id: Optional session ID (uses current graph if None)
            
        Returns:
            Observation ID
            
        Raises:
            ValueError: If observation creation fails
            KeyError: If referenced entity or relation does not exist
        """
        observation = Observation(
            entity_id=entity_id,
            relation_id=relation_id,
            content=content,
            confidence=confidence,
            source=source
        )
        
        graph = self._get_graph(session_id)
        return graph.add_observation(observation)
    
    def query_knowledge(self, 
                       query: str,
                       entity_types: Optional[List[EntityType]] = None,
                       relation_types: Optional[List[RelationType]] = None,
                       max_results: int = 100,
                       session_id: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Query the knowledge graph.
        
        Args:
            query: Query string
            entity_types: Optional list of entity types to filter by
            relation_types: Optional list of relation types to filter by
            max_results: Maximum number of results to return
            session_id: Optional session ID (uses current graph if None)
            
        Returns:
            Dictionary with 'entities' and 'relations' lists of dictionaries
        """
        graph = self._get_graph(session_id)
        
        # Simple keyword matching for now
        # In a real implementation, this would use more sophisticated retrieval
        keywords = query.lower().split()
        
        # First, find entities and relations matching the query
        matching_entities = []
        for entity_id, entity in graph.entities.items():
            if entity_types and entity.entity_type not in entity_types:
                continue
                
            entity_text = f"{entity.name} {json.dumps(entity.properties)}".lower()
            if any(keyword in entity_text for keyword in keywords):
                matching_entities.append(entity)
                
        matching_relations = []
        for relation_id, relation in graph.relations.items():
            if relation_types and relation.relation_type not in relation_types:
                continue
                
            relation_text = f"{relation.relation_type.value} {json.dumps(relation.properties)}".lower()
            if any(keyword in relation_text for keyword in keywords):
                matching_relations.append(relation)
                
        # Then, find observations matching the query and include their entities/relations
        for observation_id, observation in graph.observations.items():
            if any(keyword in observation.content.lower() for keyword in keywords):
                if observation.entity_id:
                    entity = graph.get_entity(observation.entity_id)
                    if entity and (not entity_types or entity.entity_type in entity_types):
                        matching_entities.append(entity)
                        
                if observation.relation_id:
                    relation = graph.get_relation(observation.relation_id)
                    if relation and (not relation_types or relation.relation_type in relation_types):
                        matching_relations.append(relation)
                        
        # Remove duplicates
        unique_entities = {}
        for entity in matching_entities:
            unique_entities[entity.entity_id] = entity
            
        unique_relations = {}
        for relation in matching_relations:
            unique_relations[relation.relation_id] = relation
            
        # Convert to dictionaries
        entity_dicts = [entity.to_dict() for entity in unique_entities.values()]
        relation_dicts = [relation.to_dict() for relation in unique_relations.values()]
        
        # Limit results
        return {
            "entities": entity_dicts[:max_results],
            "relations": relation_dicts[:max_results]
        }
    
    def create_context(self, 
                      initial_data: Optional[Dict[str, Any]] = None,
                      session_id: Optional[str] = None) -> str:
        """
        Create a new context.
        
        Args:
            initial_data: Optional initial context data
            session_id: Optional session ID to associate with this context
            
        Returns:
            Context ID
        """
        return self.context_manager.create_context(
            session_id=session_id,
            initial_data=initial_data
        )
    
    def update_context(self, 
                      context_id: str,
                      data: Dict[str, Any],
                      merge: bool = True) -> bool:
        """
        Update a context with new data.
        
        Args:
            context_id: ID of the context to update
            data: New context data
            merge: If True, merge with existing data; if False, replace
            
        Returns:
            True if update was successful, False if context not found
        """
        return self.context_manager.update_context(context_id, data, merge)
    
    def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a context by ID.
        
        Args:
            context_id: ID of the context
            
        Returns:
            Context data or None if not found
        """
        return self.context_manager.get_context(context_id)
    
    def enrich_context(self, 
                      context_id: str,
                      query: str,
                      max_results: int = 10) -> bool:
        """
        Enrich a context with relevant information from the knowledge graph.
        
        Args:
            context_id: ID of the context to enrich
            query: Query string to find relevant information
            max_results: Maximum number of results to add
            
        Returns:
            True if enrichment was successful, False if context not found
        """
        return self.context_manager.enrich_context(context_id, query, max_results)
    
    def create_session(self) -> str:
        """
        Create a new session with its own knowledge graph.
        
        Returns:
            Session ID
        """
        return self.memory_manager.create_session()
    
    def merge_session(self, session_id: str) -> bool:
        """
        Merge a session's knowledge graph into the current graph.
        
        Args:
            session_id: ID of the session to merge
            
        Returns:
            True if merge was successful, False otherwise
        """
        return self.memory_manager.merge_session(session_id)
    
    def optimize_memory(self, 
                       min_confidence: float = 0.5,
                       max_age: Optional[float] = None) -> Dict[str, Any]:
        """
        Optimize memory through pruning and compression.
        
        Args:
            min_confidence: Minimum confidence for observations to keep
            max_age: Maximum age in seconds for entities/relations to keep
            
        Returns:
            Dictionary with optimization statistics
        """
        pruned_count = self.memory_manager.prune_graph(min_confidence, max_age)
        compression_stats = self.memory_manager.compress_memory()
        
        return {
            "pruned_count": pruned_count,
            "compression_stats": compression_stats
        }
    
    def save_memory(self, graph_id: str = "default") -> bool:
        """
        Save the current knowledge graph to persistent storage.
        
        Args:
            graph_id: ID for the saved graph
            
        Returns:
            True if save was successful, False otherwise
        """
        return self.memory_manager.save_graph(graph_id, self.memory_manager.current_graph)
    
    def load_memory(self, graph_id: str = "default") -> bool:
        """
        Load a knowledge graph from persistent storage.
        
        Args:
            graph_id: ID of the graph to load
            
        Returns:
            True if load was successful, False otherwise
        """
        graph = self.memory_manager.load_graph(graph_id)
        if graph:
            self.memory_manager.current_graph = graph
            return True
        return False
    
    def _get_graph(self, session_id: Optional[str] = None) -> KnowledgeGraph:
        """
        Get the appropriate knowledge graph.
        
        Args:
            session_id: Optional session ID
            
        Returns:
            KnowledgeGraph instance
            
        Raises:
            KeyError: If session not found
        """
        if session_id:
            graph = self.memory_manager.get_session_graph(session_id)
            if not graph:
                raise KeyError(f"Session '{session_id}' not found")
            return graph
        else:
            return self.memory_manager.current_graph
