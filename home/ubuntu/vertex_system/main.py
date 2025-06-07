"""
Main FastAPI application for Vertex Full-Stack System.

This module implements the FastAPI application that serves as the entry point
for the Vertex Full-Stack System, providing REST API endpoints for all system
functionality.
"""

from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator, constr
from typing import Dict, Any, List, Optional, Union
import time
import uuid
import asyncio
from enum import Enum
import logging
from contextlib import asynccontextmanager

# Import Vertex system components
from src.interfaces.model_provider import ModelProvider, ProviderRegistry, ModelCapability
from src.orchestration.task_orchestrator import TaskOrchestrator, Task, TaskStatus, TaskPriority
from src.orchestration.batch_controller import BatchController, BatchConfig
from src.strategies.tiered_solver import TieredProblemSolver, ProblemType
from src.optimization.resource_optimization import ResourceOptimizationLayer, CreditManager
from src.mcp.mcp_integration import MCPIntegrationLayer, MCPCapability
from src.knowledge.knowledge_context import KnowledgeContextSystem, EntityType, RelationType
from src.optimization.sleep_optimizer import SleepTimeOptimizer, TaskPriority as SleepTaskPriority

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("vertex_api")

# Initialize system components
provider_registry = ProviderRegistry()
credit_manager = CreditManager(initial_balance=100.0, budget_limit=1000.0)
knowledge_system = KnowledgeContextSystem(storage_path="/data/knowledge")

# Application lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize system components
    logger.info("Initializing Vertex Full-Stack System components...")
    
    # Initialize remaining components that depend on the above
    resource_optimization = ResourceOptimizationLayer(
        credit_manager=credit_manager,
        cost_selector=None,  # Will be initialized later
        batch_scheduler=None  # Will be initialized later
    )
    
    task_orchestrator = TaskOrchestrator(
        provider_registry=provider_registry,
        resource_optimization=resource_optimization
    )
    
    batch_controller = BatchController(
        task_orchestrator=task_orchestrator,
        resource_optimization=resource_optimization
    )
    
    # Complete circular dependencies
    resource_optimization.cost_selector = task_orchestrator.get_cost_selector()
    resource_optimization.batch_scheduler = batch_controller.get_batch_scheduler()
    
    # Store components in app state
    app.state.provider_registry = provider_registry
    app.state.credit_manager = credit_manager
    app.state.resource_optimization = resource_optimization
    app.state.task_orchestrator = task_orchestrator
    app.state.batch_controller = batch_controller
    app.state.knowledge_system = knowledge_system
    
    # Load any persistent data
    try:
        knowledge_system.load_memory()
        logger.info("Knowledge system data loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to load knowledge system data: {e}")
    
    logger.info("Vertex Full-Stack System initialized successfully")
    
    yield
    
    # Shutdown: Clean up resources
    logger.info("Shutting down Vertex Full-Stack System...")
    
    # Save any persistent data
    try:
        knowledge_system.save_memory()
        logger.info("Knowledge system data saved successfully")
    except Exception as e:
        logger.error(f"Failed to save knowledge system data: {e}")
    
    logger.info("Vertex Full-Stack System shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Vertex Full-Stack System API",
    description="API for the Vertex Full-Stack System, a model-agnostic AI orchestration platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add telemetry middleware
@app.middleware("http")
async def add_telemetry(request: Request, call_next):
    # Record request start time
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate request duration
    duration = time.time() - start_time
    
    # Add telemetry headers
    response.headers["X-Request-Duration"] = str(duration)
    response.headers["X-Request-ID"] = str(uuid.uuid4())
    
    return response

# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
            }
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Log the error
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "detail": str(exc) if app.debug else None
            }
        },
    )

# Dependency for getting system components
def get_provider_registry(request: Request) -> ProviderRegistry:
    return request.app.state.provider_registry

def get_credit_manager(request: Request) -> CreditManager:
    return request.app.state.credit_manager

def get_resource_optimization(request: Request) -> ResourceOptimizationLayer:
    return request.app.state.resource_optimization

def get_task_orchestrator(request: Request) -> TaskOrchestrator:
    return request.app.state.task_orchestrator

def get_batch_controller(request: Request) -> BatchController:
    return request.app.state.batch_controller

def get_knowledge_system(request: Request) -> KnowledgeContextSystem:
    return request.app.state.knowledge_system

# Feature flag checking
def check_feature_flag(flag_name: str) -> bool:
    # Simple feature flag implementation
    # In a real system, this would check a feature flag service
    enabled_flags = {
        "advanced_batching": True,
        "knowledge_graph": True,
        "sleep_optimization": True,
        "mcp_integration": False  # Example of a disabled feature
    }
    
    return enabled_flags.get(flag_name, False)

# Pydantic models for API requests and responses
class ModelProviderInfo(BaseModel):
    """Information about a model provider."""
    provider_id: str = Field(..., description="Unique identifier for the provider")
    name: str = Field(..., description="Human-readable name of the provider")
    description: str = Field(..., description="Description of the provider")
    capabilities: List[str] = Field(default_factory=list, description="List of provider capabilities")
    models: List[Dict[str, Any]] = Field(default_factory=list, description="List of available models")
    
    class Config:
        schema_extra = {
            "example": {
                "provider_id": "openai",
                "name": "OpenAI",
                "description": "OpenAI API provider",
                "capabilities": ["text_generation", "embeddings"],
                "models": [
                    {
                        "id": "gpt-4",
                        "name": "GPT-4",
                        "capabilities": ["text_generation"]
                    }
                ]
            }
        }

class TaskRequest(BaseModel):
    """Request to create a new task."""
    description: constr(min_length=1, max_length=1000) = Field(
        ..., description="Description of the task")
    input_data: Dict[str, Any] = Field(
        ..., description="Input data for the task")
    model_requirements: Dict[str, Any] = Field(
        default_factory=dict, description="Requirements for model selection")
    priority: str = Field(
        default="MEDIUM", description="Task priority (LOW, MEDIUM, HIGH, CRITICAL)")
    timeout_seconds: int = Field(
        default=300, description="Timeout in seconds", ge=1, le=3600)
    max_retries: int = Field(
        default=3, description="Maximum number of retries", ge=0, le=10)
    
    @validator("priority")
    def validate_priority(cls, v):
        valid_priorities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of {valid_priorities}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "description": "Generate a summary of the provided text",
                "input_data": {
                    "text": "Lorem ipsum dolor sit amet..."
                },
                "model_requirements": {
                    "capabilities": ["text_generation"],
                    "min_tokens": 1000
                },
                "priority": "MEDIUM",
                "timeout_seconds": 300,
                "max_retries": 3
            }
        }

class TaskResponse(BaseModel):
    """Response containing task information."""
    task_id: str = Field(..., description="Unique identifier for the task")
    status: str = Field(..., description="Current status of the task")
    created_at: float = Field(..., description="Timestamp when the task was created")
    updated_at: float = Field(..., description="Timestamp when the task was last updated")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result (if completed)")
    error: Optional[str] = Field(None, description="Error message (if failed)")
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "task_123456",
                "status": "COMPLETED",
                "created_at": 1619712000.0,
                "updated_at": 1619712060.0,
                "result": {
                    "summary": "This is a summary of the provided text..."
                },
                "error": None
            }
        }

class BatchRequest(BaseModel):
    """Request to create a new batch of tasks."""
    name: constr(min_length=1, max_length=100) = Field(
        ..., description="Name of the batch")
    description: constr(min_length=1, max_length=1000) = Field(
        ..., description="Description of the batch")
    tasks: List[TaskRequest] = Field(
        ..., description="List of tasks in the batch", min_items=1, max_items=100)
    batch_config: Dict[str, Any] = Field(
        default_factory=dict, description="Batch configuration")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Text Summarization Batch",
                "description": "Batch of text summarization tasks",
                "tasks": [
                    {
                        "description": "Generate a summary of text 1",
                        "input_data": {"text": "Lorem ipsum dolor sit amet..."}
                    },
                    {
                        "description": "Generate a summary of text 2",
                        "input_data": {"text": "Consectetur adipiscing elit..."}
                    }
                ],
                "batch_config": {
                    "max_concurrent_tasks": 5,
                    "stop_on_first_failure": False
                }
            }
        }

class BatchResponse(BaseModel):
    """Response containing batch information."""
    batch_id: str = Field(..., description="Unique identifier for the batch")
    status: str = Field(..., description="Current status of the batch")
    created_at: float = Field(..., description="Timestamp when the batch was created")
    updated_at: float = Field(..., description="Timestamp when the batch was last updated")
    task_count: int = Field(..., description="Total number of tasks in the batch")
    completed_count: int = Field(..., description="Number of completed tasks")
    failed_count: int = Field(..., description="Number of failed tasks")
    
    class Config:
        schema_extra = {
            "example": {
                "batch_id": "batch_123456",
                "status": "RUNNING",
                "created_at": 1619712000.0,
                "updated_at": 1619712060.0,
                "task_count": 10,
                "completed_count": 5,
                "failed_count": 0
            }
        }

class KnowledgeEntityRequest(BaseModel):
    """Request to create a new knowledge entity."""
    entity_type: str = Field(..., description="Type of entity")
    name: constr(min_length=1, max_length=100) = Field(..., description="Name of the entity")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Entity properties")
    
    @validator("entity_type")
    def validate_entity_type(cls, v):
        try:
            EntityType(v)
            return v
        except ValueError:
            valid_types = [e.value for e in EntityType]
            raise ValueError(f"Entity type must be one of {valid_types}")
    
    class Config:
        schema_extra = {
            "example": {
                "entity_type": "concept",
                "name": "Machine Learning",
                "properties": {
                    "definition": "A field of AI that uses statistical techniques to give computers the ability to learn",
                    "related_fields": ["artificial intelligence", "data science"]
                }
            }
        }

class KnowledgeRelationRequest(BaseModel):
    """Request to create a new knowledge relation."""
    relation_type: str = Field(..., description="Type of relation")
    source_id: str = Field(..., description="ID of the source entity")
    target_id: str = Field(..., description="ID of the target entity")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relation properties")
    
    @validator("relation_type")
    def validate_relation_type(cls, v):
        try:
            RelationType(v)
            return v
        except ValueError:
            valid_types = [r.value for r in RelationType]
            raise ValueError(f"Relation type must be one of {valid_types}")
    
    class Config:
        schema_extra = {
            "example": {
                "relation_type": "is_a",
                "source_id": "entity_123",
                "target_id": "entity_456",
                "properties": {
                    "confidence": 0.95,
                    "source": "user_defined"
                }
            }
        }

class KnowledgeQueryRequest(BaseModel):
    """Request to query the knowledge graph."""
    query: constr(min_length=1, max_length=1000) = Field(..., description="Query string")
    entity_types: Optional[List[str]] = Field(None, description="Types of entities to include")
    relation_types: Optional[List[str]] = Field(None, description="Types of relations to include")
    max_results: int = Field(default=100, description="Maximum number of results", ge=1, le=1000)
    
    @validator("entity_types")
    def validate_entity_types(cls, v):
        if v is None:
            return v
        
        valid_types = [e.value for e in EntityType]
        for entity_type in v:
            if entity_type not in valid_types:
                raise ValueError(f"Entity type must be one of {valid_types}")
        return v
    
    @validator("relation_types")
    def validate_relation_types(cls, v):
        if v is None:
            return v
        
        valid_types = [r.value for r in RelationType]
        for relation_type in v:
            if relation_type not in valid_types:
                raise ValueError(f"Relation type must be one of {valid_types}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "query": "machine learning",
                "entity_types": ["concept", "task"],
                "relation_types": ["is_a", "part_of"],
                "max_results": 50
            }
        }

# API endpoints
@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "Vertex Full-Stack System API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }

# Model Provider endpoints
@app.get("/providers", response_model=List[ModelProviderInfo])
async def list_providers(
    registry: ProviderRegistry = Depends(get_provider_registry)
):
    """List all registered model providers."""
    providers = []
    
    for provider_id in registry.list_providers():
        try:
            provider = registry.get_provider(provider_id)
            
            # Get provider information
            info = {
                "provider_id": provider_id,
                "name": provider.get_name(),
                "description": provider.get_description(),
                "capabilities": provider.get_capabilities(),
                "models": provider.list_available_models()
            }
            
            providers.append(info)
        except Exception as e:
            logger.error(f"Error getting provider {provider_id}: {e}")
    
    return providers

@app.get("/providers/{provider_id}", response_model=ModelProviderInfo)
async def get_provider(
    provider_id: str,
    registry: ProviderRegistry = Depends(get_provider_registry)
):
    """Get information about a specific model provider."""
    try:
        provider = registry.get_provider(provider_id)
        
        # Get provider information
        info = {
            "provider_id": provider_id,
            "name": provider.get_name(),
            "description": provider.get_description(),
            "capabilities": provider.get_capabilities(),
            "models": provider.list_available_models()
        }
        
        return info
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")
    except Exception as e:
        logger.error(f"Error getting provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Task endpoints
@app.post("/tasks", response_model=TaskResponse)
async def create_task(
    task_request: TaskRequest,
    background_tasks: BackgroundTasks,
    orchestrator: TaskOrchestrator = Depends(get_task_orchestrator)
):
    """Create a new task."""
    try:
        # Convert priority string to enum
        priority = TaskPriority[task_request.priority]
        
        # Create task
        task = Task(
            description=task_request.description,
            input_data=task_request.input_data,
            priority=priority,
            timeout_seconds=task_request.timeout_seconds,
            max_retries=task_request.max_retries,
            metadata={
                "model_requirements": task_request.model_requirements
            }
        )
        
        # Submit task
        task_id = orchestrator.submit_task(task)
        
        # Start task execution in background
        background_tasks.add_task(orchestrator.execute_task, task_id)
        
        # Get task status
        task_status = orchestrator.get_task_status(task_id)
        
        return {
            "task_id": task_id,
            "status": task_status.status.value,
            "created_at": task_status.created_at,
            "updated_at": task_status.updated_at,
            "result": task_status.result,
            "error": task_status.error
        }
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    orchestrator: TaskOrchestrator = Depends(get_task_orchestrator)
):
    """Get information about a specific task."""
    try:
        task_status = orchestrator.get_task_status(task_id)
        
        if not task_status:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            
        return {
            "task_id": task_id,
            "status": task_status.status.value,
            "created_at": task_status.created_at,
            "updated_at": task_status.updated_at,
            "result": task_status.result,
            "error": task_status.error
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    orchestrator: TaskOrchestrator = Depends(get_task_orchestrator)
):
    """Cancel a task."""
    try:
        success = orchestrator.cancel_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found or cannot be canceled")
            
        return {
            "task_id": task_id,
            "status": "canceled"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error canceling task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Batch endpoints
@app.post("/batches", response_model=BatchResponse)
async def create_batch(
    batch_request: BatchRequest,
    background_tasks: BackgroundTasks,
    batch_controller: BatchController = Depends(get_batch_controller)
):
    """Create a new batch of tasks."""
    try:
        # Check if advanced batching is enabled
        if not check_feature_flag("advanced_batching"):
            raise HTTPException(status_code=403, detail="Advanced batching feature is not enabled")
            
        # Convert task requests to tasks
        tasks = []
        for task_request in batch_request.tasks:
            # Convert priority string to enum
            priority = TaskPriority[task_request.priority]
            
            # Create task
            task = Task(
                description=task_request.description,
                input_data=task_request.input_data,
                priority=priority,
                timeout_seconds=task_request.timeout_seconds,
                max_retries=task_request.max_retries,
                metadata={
                    "model_requirements": task_request.model_requirements
                }
            )
            
            tasks.append(task)
            
        # Create batch config
        batch_config = BatchConfig(
            name=batch_request.name,
            description=batch_request.description,
            **batch_request.batch_config
        )
        
        # Submit batch
        batch_id = batch_controller.create_batch(tasks, batch_config)
        
        # Start batch execution in background
        background_tasks.add_task(batch_controller.execute_batch, batch_id)
        
        # Get batch status
        batch_status = batch_controller.get_batch_status(batch_id)
        
        return {
            "batch_id": batch_id,
            "status": batch_status["status"],
            "created_at": batch_status["created_at"],
            "updated_at": batch_status["updated_at"],
            "task_count": batch_status["task_count"],
            "completed_count": batch_status["completed_count"],
            "failed_count": batch_status["failed_count"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/batches/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: str,
    batch_controller: BatchController = Depends(get_batch_controller)
):
    """Get information about a specific batch."""
    try:
        batch_status = batch_controller.get_batch_status(batch_id)
        
        if not batch_status:
            raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
            
        return {
            "batch_id": batch_id,
            "status": batch_status["status"],
            "created_at": batch_status["created_at"],
            "updated_at": batch_status["updated_at"],
            "task_count": batch_status["task_count"],
            "completed_count": batch_status["completed_count"],
            "failed_count": batch_status["failed_count"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch {batch_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/batches/{batch_id}/tasks", response_model=List[TaskResponse])
async def get_batch_tasks(
    batch_id: str,
    batch_controller: BatchController = Depends(get_batch_controller)
):
    """Get all tasks in a batch."""
    try:
        tasks = batch_controller.get_batch_tasks(batch_id)
        
        if tasks is None:
            raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
            
        return [
            {
                "task_id": task.task_id,
                "status": task.status.value,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "result": task.result,
                "error": task.error
            }
            for task in tasks
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tasks for batch {batch_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/batches/{batch_id}")
async def cancel_batch(
    batch_id: str,
    batch_controller: BatchController = Depends(get_batch_controller)
):
    """Cancel a batch."""
    try:
        success = batch_controller.cancel_batch(batch_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found or cannot be canceled")
            
        return {
            "batch_id": batch_id,
            "status": "canceled"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error canceling batch {batch_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Knowledge System endpoints
@app.post("/knowledge/entities", response_model=Dict[str, str])
async def create_entity(
    entity_request: KnowledgeEntityRequest,
    knowledge_system: KnowledgeContextSystem = Depends(get_knowledge_system)
):
    """Create a new knowledge entity."""
    try:
        # Check if knowledge graph feature is enabled
        if not check_feature_flag("knowledge_graph"):
            raise HTTPException(status_code=403, detail="Knowledge graph feature is not enabled")
            
        # Convert entity type string to enum
        entity_type = EntityType(entity_request.entity_type)
        
        # Create entity
        entity_id = knowledge_system.create_entity(
            entity_type=entity_type,
            name=entity_request.name,
            properties=entity_request.properties
        )
        
        return {
            "entity_id": entity_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/knowledge/relations", response_model=Dict[str, str])
async def create_relation(
    relation_request: KnowledgeRelationRequest,
    knowledge_system: KnowledgeContextSystem = Depends(get_knowledge_system)
):
    """Create a new knowledge relation."""
    try:
        # Check if knowledge graph feature is enabled
        if not check_feature_flag("knowledge_graph"):
            raise HTTPException(status_code=403, detail="Knowledge graph feature is not enabled")
            
        # Convert relation type string to enum
        relation_type = RelationType(relation_request.relation_type)
        
        # Create relation
        relation_id = knowledge_system.create_relation(
            relation_type=relation_type,
            source_id=relation_request.source_id,
            target_id=relation_request.target_id,
            properties=relation_request.properties
        )
        
        return {
            "relation_id": relation_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating relation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/knowledge/query", response_model=Dict[str, List[Dict[str, Any]]])
async def query_knowledge(
    query_request: KnowledgeQueryRequest,
    knowledge_system: KnowledgeContextSystem = Depends(get_knowledge_system)
):
    """Query the knowledge graph."""
    try:
        # Check if knowledge graph feature is enabled
        if not check_feature_flag("knowledge_graph"):
            raise HTTPException(status_code=403, detail="Knowledge graph feature is not enabled")
            
        # Convert type strings to enums
        entity_types = None
        if query_request.entity_types:
            entity_types = [EntityType(et) for et in query_request.entity_types]
            
        relation_types = None
        if query_request.relation_types:
            relation_types = [RelationType(rt) for rt in query_request.relation_types]
            
        # Query knowledge
        results = knowledge_system.query_knowledge(
            query=query_request.query,
            entity_types=entity_types,
            relation_types=relation_types,
            max_results=query_request.max_results
        )
        
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error querying knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Resource Optimization endpoints
@app.get("/resources/usage")
async def get_resource_usage(
    component_id: Optional[str] = None,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    resource_optimization: ResourceOptimizationLayer = Depends(get_resource_optimization)
):
    """Get resource usage information."""
    try:
        usage_report = resource_optimization.get_usage_report(
            component_id=component_id,
            start_time=start_time,
            end_time=end_time
        )
        
        return usage_report
    except Exception as e:
        logger.error(f"Error getting resource usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/resources/optimize")
async def optimize_resources(
    resource_optimization: ResourceOptimizationLayer = Depends(get_resource_optimization)
):
    """Optimize resource allocation."""
    try:
        optimization_results = resource_optimization.optimize_resource_allocation()
        
        return optimization_results
    except Exception as e:
        logger.error(f"Error optimizing resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
