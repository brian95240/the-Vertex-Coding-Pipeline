"""
Dynamic Micro-Batching System for Vertex Full-Stack System.

This module implements the dynamic micro-batching controller, which
optimizes task execution by grouping similar tasks into batches based
on environmental factors and task characteristics.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Type
import time
import asyncio
import importlib
from enum import Enum

# Import Task definition
from .task_orchestrator import Task


class BatchRule(ABC):
    """
    Abstract base class for batch sizing rules.
    
    Batch rules determine how tasks should be grouped into batches based on
    various factors such as task similarity, system load, and priority.
    """
    
    @abstractmethod
    def evaluate(self, tasks: List[Task], system_state: Dict[str, Any]) -> int:
        """
        Evaluate the optimal batch size for a set of tasks.
        
        Args:
            tasks: List of tasks to potentially batch
            system_state: Current system state information
            
        Returns:
            Recommended batch size (number of tasks)
        """
        pass


class BatchPriority(Enum):
    """Enum representing batch priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class BatchConfig:
    """
    Configuration for batch processing.
    
    Defines parameters that control how batches are formed and processed.
    """
    
    def __init__(self,
                max_batch_size: int = 10,
                min_batch_size: int = 1,
                max_wait_time: float = 5.0,
                similarity_threshold: float = 0.7,
                priority: BatchPriority = BatchPriority.NORMAL):
        """
        Initialize batch configuration.
        
        Args:
            max_batch_size: Maximum number of tasks in a batch
            min_batch_size: Minimum number of tasks to form a batch
            max_wait_time: Maximum time to wait for batch formation (seconds)
            similarity_threshold: Minimum similarity score for tasks to be batched
            priority: Priority level for this batch configuration
        """
        self.max_batch_size = max_batch_size
        self.min_batch_size = min_batch_size
        self.max_wait_time = max_wait_time
        self.similarity_threshold = similarity_threshold
        self.priority = priority


class BatchController:
    """
    Controller for dynamic micro-batching.
    
    Manages the formation and execution of task batches based on rules and
    system state.
    """
    
    def __init__(self, task_orchestrator=None, resource_optimization=None):
        """
        Initialize batch controller with empty state.
        
        Args:
            task_orchestrator: TaskOrchestrator instance for executing tasks
            resource_optimization: ResourceOptimizationLayer instance for resource management
        """
        self.task_orchestrator = task_orchestrator
        self.resource_optimization = resource_optimization
        self.pending_tasks = []
        self.active_batches = []
        self.completed_batches = []
        self.rule_registry = {}
        self.rule_metadata = {}
        self.rule_cache = {}
        self.default_config = BatchConfig()
    
    def get_batch_scheduler(self):
        """
        Get the batch scheduler for resource optimization.
        
        Returns:
            PredictiveBatchScheduler instance or None
        """
        # This is a placeholder for the actual implementation
        return None
    
    def add_task(self, task: Task) -> None:
        """
        Add a task to the pending queue.
        
        Args:
            task: Task to add
        """
        self.pending_tasks.append(task)
    
    def register_rule(self, 
                     rule_id: str, 
                     rule_metadata: Dict[str, Any],
                     module_path: str,
                     class_name: str) -> None:
        """
        Register a batch rule for lazy loading.
        
        Args:
            rule_id: Unique identifier for the rule
            rule_metadata: Metadata for the rule
            module_path: Import path to the module containing the rule
            class_name: Name of the rule class
        """
        if rule_id in self.rule_metadata:
            raise ValueError(f"Rule ID {rule_id} already registered")
        
        self.rule_metadata[rule_id] = {
            "metadata": rule_metadata,
            "module_path": module_path,
            "class_name": class_name
        }
    
    def get_rule(self, rule_id: str) -> BatchRule:
        """
        Get a batch rule by ID, loading it if necessary.
        
        Args:
            rule_id: ID of the rule to get
            
        Returns:
            BatchRule instance
            
        Raises:
            ValueError: If rule not found or cannot be loaded
        """
        if rule_id in self.rule_cache:
            # Update access timestamp
            self.rule_cache[rule_id]["last_accessed"] = time.time()
            return self.rule_cache[rule_id]["implementation"]
        
        metadata = self.rule_metadata.get(rule_id)
        if not metadata:
            raise ValueError(f"Rule ID {rule_id} not found in repository")
        
        module_path = metadata.get("module_path")
        class_name = metadata.get("class_name")
        if not module_path or not class_name:
            raise ValueError(f"Invalid metadata for rule ID {rule_id}")
        
        # Load rule implementation dynamically
        try:
            # This assumes module_path is importable (e.g., "vertex_system.strategies.batch_rules.memory_rule")
            module = importlib.import_module(module_path)
            rule_class = getattr(module, class_name)
            rule_implementation = rule_class() # Instantiate the rule
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Failed to load rule {rule_id} from {module_path}.{class_name}: {e}")
        
        # Add to cache
        self.rule_cache[rule_id] = {
            "implementation": rule_implementation,
            "last_accessed": time.time()
        }
        
        return rule_implementation
    
    def form_batch(self, config: Optional[BatchConfig] = None) -> List[Task]:
        """
        Form a batch from pending tasks based on configuration.
        
        Args:
            config: Optional batch configuration (uses default if None)
            
        Returns:
            List of tasks forming the batch
        """
        if not self.pending_tasks:
            return []
        
        if config is None:
            config = self.default_config
        
        # Simple implementation: just take up to max_batch_size tasks
        batch_size = min(config.max_batch_size, len(self.pending_tasks))
        
        if batch_size < config.min_batch_size:
            return []
        
        batch = self.pending_tasks[:batch_size]
        self.pending_tasks = self.pending_tasks[batch_size:]
        
        return batch
    
    def form_optimal_batch(self, 
                          rule_ids: List[str], 
                          system_state: Dict[str, Any]) -> List[Task]:
        """
        Form an optimal batch using multiple rules.
        
        Args:
            rule_ids: List of rule IDs to apply
            system_state: Current system state
            
        Returns:
            List of tasks forming the optimal batch
        """
        if not self.pending_tasks:
            return []
        
        # Apply each rule to get batch size recommendations
        batch_sizes = []
        
        for rule_id in rule_ids:
            try:
                rule = self.get_rule(rule_id)
                batch_size = rule.evaluate(self.pending_tasks, system_state)
                batch_sizes.append(batch_size)
            except Exception as e:
                # Log error and continue with other rules
                print(f"Error applying rule {rule_id}: {e}")
        
        if not batch_sizes:
            # No valid rules, use default
            return self.form_batch()
        
        # Use average of recommended batch sizes
        avg_batch_size = int(sum(batch_sizes) / len(batch_sizes))
        batch_size = min(avg_batch_size, len(self.pending_tasks))
        
        batch = self.pending_tasks[:batch_size]
        self.pending_tasks = self.pending_tasks[batch_size:]
        
        return batch
    
    async def process_batches(self, 
                            processor_func: callable, 
                            config: Optional[BatchConfig] = None,
                            rule_ids: Optional[List[str]] = None,
                            system_state: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Process tasks in batches.
        
        Args:
            processor_func: Function to process each batch
            config: Optional batch configuration
            rule_ids: Optional list of rule IDs for optimal batching
            system_state: Optional system state for rules
            
        Returns:
            List of batch processing results
        """
        results = []
        
        while self.pending_tasks:
            # Form batch
            if rule_ids and system_state:
                batch = self.form_optimal_batch(rule_ids, system_state)
            else:
                batch = self.form_batch(config)
            
            if not batch:
                break
            
            # Process batch
            batch_id = f"batch_{int(time.time())}_{len(self.active_batches)}"
            batch_info = {
                "batch_id": batch_id,
                "tasks": batch,
                "start_time": time.time()
            }
            
            self.active_batches.append(batch_info)
            
            try:
                batch_result = await processor_func(batch)
                
                # Record completion
                batch_info["end_time"] = time.time()
                batch_info["result"] = batch_result
                batch_info["status"] = "completed"
                
                self.completed_batches.append(batch_info)
                self.active_batches.remove(batch_info)
                
                results.append({
                    "batch_id": batch_id,
                    "task_count": len(batch),
                    "processing_time": batch_info["end_time"] - batch_info["start_time"],
                    "result": batch_result
                })
                
            except Exception as e:
                # Record failure
                batch_info["end_time"] = time.time()
                batch_info["error"] = str(e)
                batch_info["status"] = "failed"
                
                self.completed_batches.append(batch_info)
                self.active_batches.remove(batch_info)
                
                results.append({
                    "batch_id": batch_id,
                    "task_count": len(batch),
                    "processing_time": batch_info["end_time"] - batch_info["start_time"],
                    "error": str(e)
                })
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about batch processing.
        
        Returns:
            Dictionary containing batch processing statistics
        """
        completed_count = len(self.completed_batches)
        
        if completed_count == 0:
            return {
                "pending_tasks": len(self.pending_tasks),
                "active_batches": len(self.active_batches),
                "completed_batches": 0,
                "avg_batch_size": 0,
                "avg_processing_time": 0
            }
        
        total_tasks = sum(len(batch["tasks"]) for batch in self.completed_batches)
        avg_batch_size = total_tasks / completed_count
        
        completed_with_times = [
            batch for batch in self.completed_batches
            if "start_time" in batch and "end_time" in batch
        ]
        
        if completed_with_times:
            total_time = sum(
                batch["end_time"] - batch["start_time"]
                for batch in completed_with_times
            )
            avg_time = total_time / len(completed_with_times)
        else:
            avg_time = 0
        
        return {
            "pending_tasks": len(self.pending_tasks),
            "active_batches": len(self.active_batches),
            "completed_batches": completed_count,
            "avg_batch_size": avg_batch_size,
            "avg_processing_time": avg_time
        }
