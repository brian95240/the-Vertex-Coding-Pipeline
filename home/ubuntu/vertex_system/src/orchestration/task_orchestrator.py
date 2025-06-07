"""
Task Orchestrator for Vertex Full-Stack System.

This module defines the core orchestration engine that manages workflows,
task execution, and state management across the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable
from enum import Enum
import uuid
import time
import asyncio
from datetime import datetime

# Import interfaces
from ..interfaces.model_provider import ModelProvider, ProviderRegistry, ModelRole, ModelRoleManager


class TaskStatus(Enum):
    """Enum representing the status of a task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Enum representing the priority of a task."""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class Task:
    """
    Represents a task to be executed by the orchestration engine.
    
    A task encapsulates a unit of work, along with metadata about its
    execution requirements, dependencies, and state.
    """
    
    def __init__(self, 
                task_id: Optional[str] = None,
                name: str = "",
                description: str = "",
                input_data: Optional[Dict[str, Any]] = None,
                priority: TaskPriority = TaskPriority.MEDIUM,
                dependencies: Optional[List[str]] = None,
                required_capabilities: Optional[List[str]] = None,
                max_retries: int = 3,
                timeout_seconds: Optional[int] = None):
        """
        Initialize a task.
        
        Args:
            task_id: Optional unique identifier (generated if not provided)
            name: Human-readable name for the task
            description: Detailed description of the task
            input_data: Input data for the task
            priority: Priority level for scheduling
            dependencies: List of task IDs that must complete before this task
            required_capabilities: Capabilities required to execute this task
            max_retries: Maximum number of retry attempts on failure
            timeout_seconds: Maximum execution time in seconds
        """
        self.task_id = task_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.input_data = input_data or {}
        self.priority = priority
        self.dependencies = dependencies or []
        self.required_capabilities = required_capabilities or []
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        
        # Runtime state
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None
        self.retry_count = 0
        self.assigned_provider = None
        self.assigned_model = None
        self.execution_trace = []
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert task to dictionary representation.
        
        Returns:
            Dictionary containing all task data
        """
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "input_data": self.input_data,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
            "required_capabilities": self.required_capabilities,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "assigned_provider": self.assigned_provider,
            "assigned_model": self.assigned_model,
            "execution_trace": self.execution_trace
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """
        Create a task from dictionary representation.
        
        Args:
            data: Dictionary containing task data
            
        Returns:
            Task instance
        """
        task = cls(
            task_id=data.get("task_id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            input_data=data.get("input_data", {}),
            priority=TaskPriority(data.get("priority", 1)),
            dependencies=data.get("dependencies", []),
            required_capabilities=data.get("required_capabilities", []),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds")
        )
        
        # Set runtime state
        task.status = TaskStatus(data.get("status", "pending"))
        task.created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        task.started_at = datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None
        task.completed_at = datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        task.result = data.get("result")
        task.error = data.get("error")
        task.retry_count = data.get("retry_count", 0)
        task.assigned_provider = data.get("assigned_provider")
        task.assigned_model = data.get("assigned_model")
        task.execution_trace = data.get("execution_trace", [])
        
        return task


class TaskExecutor(ABC):
    """
    Abstract base class for task executors.
    
    Task executors are responsible for executing tasks using appropriate
    models or services.
    """
    
    @abstractmethod
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a task.
        
        Args:
            task: The task to execute
            
        Returns:
            Dictionary containing execution result
            
        Raises:
            Exception: If task execution fails
        """
        pass


class ModelTaskExecutor(TaskExecutor):
    """
    Task executor that uses AI models for execution.
    
    This executor leverages the model provider interface to execute tasks
    using appropriate AI models.
    """
    
    def __init__(self, 
                provider_registry: ProviderRegistry,
                role_manager: ModelRoleManager):
        """
        Initialize the model task executor.
        
        Args:
            provider_registry: Registry of available model providers
            role_manager: Manager for model role assignments
        """
        self.provider_registry = provider_registry
        self.role_manager = role_manager
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a task using an appropriate AI model.
        
        Args:
            task: The task to execute
            
        Returns:
            Dictionary containing execution result
            
        Raises:
            Exception: If task execution fails
        """
        # Determine appropriate model role for this task
        role = self._determine_role_for_task(task)
        
        # Get best model for the role
        model_info = self.role_manager.get_best_model_for_role(role)
        provider_id = model_info["provider_id"]
        model_id = model_info["model_id"]
        
        # Get provider
        provider = self.provider_registry.get_provider(provider_id)
        
        # Update task with assignment
        task.assigned_provider = provider_id
        task.assigned_model = model_id
        
        # Prepare prompt from task
        prompt = self._prepare_prompt_for_task(task)
        
        # Execute prompt
        try:
            start_time = time.time()
            response = provider.execute_prompt(model_id, prompt)
            end_time = time.time()
            
            # Record execution trace
            task.execution_trace.append({
                "timestamp": datetime.now().isoformat(),
                "provider": provider_id,
                "model": model_id,
                "execution_time": end_time - start_time,
                "success": True
            })
            
            # Parse and return result
            return self._parse_response(response)
        
        except Exception as e:
            # Record execution trace
            task.execution_trace.append({
                "timestamp": datetime.now().isoformat(),
                "provider": provider_id,
                "model": model_id,
                "error": str(e),
                "success": False
            })
            
            # Re-raise exception
            raise
    
    def _determine_role_for_task(self, task: Task) -> ModelRole:
        """
        Determine the appropriate model role for a task.
        
        Args:
            task: The task to analyze
            
        Returns:
            ModelRole enum value
        """
        # Simple mapping based on task description for now
        # In a real implementation, this would use more sophisticated analysis
        if "analyze" in task.description.lower():
            return ModelRole.ANALYZER
        elif "generate" in task.description.lower():
            return ModelRole.GENERATOR
        elif "validate" in task.description.lower():
            return ModelRole.VALIDATOR
        elif "optimize" in task.description.lower():
            return ModelRole.OPTIMIZER
        else:
            return ModelRole.EXECUTOR
    
    def _prepare_prompt_for_task(self, task: Task) -> str:
        """
        Prepare a prompt for the task.
        
        Args:
            task: The task to prepare a prompt for
            
        Returns:
            Prompt string
        """
        # Simple prompt template for now
        # In a real implementation, this would use the PromptTemplate class
        prompt = f"""
        Task: {task.name}
        
        Description: {task.description}
        
        Input Data:
        {task.input_data}
        
        Please execute this task and provide the result.
        """
        
        return prompt
    
    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the response from a model.
        
        Args:
            response: Raw response from the model
            
        Returns:
            Parsed result
        """
        # Simple parsing for now
        # In a real implementation, this would use more sophisticated parsing
        return {
            "result": response.get("text", ""),
            "metadata": {
                "model_metadata": response.get("metadata", {})
            }
        }


class TaskOrchestrator:
    """
    Orchestrates task execution across the system.
    
    This class manages task workflows, dependencies, scheduling, and execution.
    """
    
    def __init__(self, 
                provider_registry: ProviderRegistry = None, 
                resource_optimization = None):
        """
        Initialize the task orchestrator.
        
        Args:
            provider_registry: ProviderRegistry instance for model access
            resource_optimization: ResourceOptimizationLayer instance for resource management
        """
        self.provider_registry = provider_registry
        self.resource_optimization = resource_optimization
        
        # Create a default executor if needed
        if provider_registry:
            role_manager = ModelRoleManager(provider_registry)
            self.executor = ModelTaskExecutor(provider_registry, role_manager)
        else:
            self.executor = None
            
        self.tasks = {}  # task_id -> Task
        self.workflows = {}  # workflow_id -> List[task_id]
    
    def get_cost_selector(self):
        """
        Get the cost selector for resource optimization.
        
        Returns:
            CostAwareSelector instance or None
        """
        # This is a placeholder for the actual implementation
        return None
    
    def add_task(self, task: Task) -> str:
        """
        Add a task to the orchestrator.
        
        Args:
            task: The task to add
            
        Returns:
            Task ID
        """
        self.tasks[task.task_id] = task
        return task.task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            Task instance or None if not found
        """
        return self.tasks.get(task_id)
    
    def create_workflow(self, tasks: List[Task]) -> str:
        """
        Create a workflow from a list of tasks.
        
        Args:
            tasks: List of tasks in the workflow
            
        Returns:
            Workflow ID
        """
        workflow_id = str(uuid.uuid4())
        
        # Add tasks to orchestrator
        task_ids = []
        for task in tasks:
            self.add_task(task)
            task_ids.append(task.task_id)
        
        # Store workflow
        self.workflows[workflow_id] = task_ids
        
        return workflow_id
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """
        Execute a single task.
        
        Args:
            task_id: ID of the task to execute
            
        Returns:
            Task execution result
            
        Raises:
            ValueError: If task not found
            Exception: If task execution fails
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        # Check dependencies
        for dep_id in task.dependencies:
            dep_task = self.get_task(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                raise ValueError(f"Dependency not satisfied: {dep_id}")
        
        # Update task status
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        try:
            # Execute task
            result = await self.executor.execute_task(task)
            
            # Update task status
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            
            return result
        
        except Exception as e:
            # Handle retry logic
            task.retry_count += 1
            task.error = str(e)
            
            if task.retry_count < task.max_retries:
                # Retry task
                return await self.execute_task(task_id)
            else:
                # Mark as failed
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                raise
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Execute a workflow.
        
        Args:
            workflow_id: ID of the workflow to execute
            
        Returns:
            Dictionary mapping task IDs to results
            
        Raises:
            ValueError: If workflow not found
        """
        task_ids = self.workflows.get(workflow_id)
        if not task_ids:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Build dependency graph
        graph = {}
        for task_id in task_ids:
            task = self.get_task(task_id)
            graph[task_id] = {
                "task": task,
                "dependencies": task.dependencies,
                "dependents": []
            }
        
        # Populate dependents
        for task_id, node in graph.items():
            for dep_id in node["dependencies"]:
                if dep_id in graph:
                    graph[dep_id]["dependents"].append(task_id)
        
        # Find tasks with no dependencies
        ready_tasks = [
            task_id for task_id, node in graph.items()
            if not node["dependencies"] or all(
                dep_id not in graph for dep_id in node["dependencies"]
            )
        ]
        
        # Execute tasks in dependency order
        results = {}
        while ready_tasks:
            # Execute ready tasks in parallel
            current_tasks = ready_tasks.copy()
            ready_tasks = []
            
            # Create execution tasks
            execution_tasks = [
                self.execute_task(task_id) for task_id in current_tasks
            ]
            
            # Wait for all tasks to complete
            task_results = await asyncio.gather(
                *execution_tasks, return_exceptions=True
            )
            
            # Process results
            for task_id, result in zip(current_tasks, task_results):
                if isinstance(result, Exception):
                    # Task failed
                    results[task_id] = {"error": str(result)}
                    
                    # Mark dependents as failed
                    for dependent_id in graph[task_id]["dependents"]:
                        dependent_task = self.get_task(dependent_id)
                        dependent_task.status = TaskStatus.FAILED
                        dependent_task.error = f"Dependency failed: {task_id}"
                else:
                    # Task succeeded
                    results[task_id] = result
                    
                    # Check if dependents are ready
                    for dependent_id in graph[task_id]["dependents"]:
                        dependent_node = graph[dependent_id]
                        dependent_task = dependent_node["task"]
                        
                        # Check if all dependencies are satisfied
                        if all(
                            dep_id in results
                            for dep_id in dependent_task.dependencies
                            if dep_id in graph
                        ):
                            ready_tasks.append(dependent_id)
        
        return results
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if task was cancelled, False otherwise
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            task.status = TaskStatus.CANCELLED
            return True
        
        return False
    
    def cancel_workflow(self, workflow_id: str) -> List[str]:
        """
        Cancel a workflow.
        
        Args:
            workflow_id: ID of the workflow to cancel
            
        Returns:
            List of task IDs that were cancelled
            
        Raises:
            ValueError: If workflow not found
        """
        task_ids = self.workflows.get(workflow_id)
        if not task_ids:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        cancelled_tasks = []
        for task_id in task_ids:
            if self.cancel_task(task_id):
                cancelled_tasks.append(task_id)
        
        return cancelled_tasks
