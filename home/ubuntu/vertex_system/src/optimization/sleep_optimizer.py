"""
Sleep-Time Optimization for Vertex Full-Stack System.

This module implements the sleep-time optimization components that manage
background processing, deferred execution, and resource utilization during
idle periods.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
import time
import asyncio
import uuid
import threading
import heapq
from enum import Enum
from datetime import datetime, timedelta


class TaskPriority(Enum):
    """Enum representing different priority levels for sleep-time tasks."""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class SleepTimeTask:
    """
    Represents a task to be executed during sleep time.
    
    Sleep-time tasks are executed when the system is idle or has
    excess capacity.
    """
    
    def __init__(self,
                task_id: Optional[str] = None,
                name: str = "",
                description: str = "",
                priority: TaskPriority = TaskPriority.MEDIUM,
                estimated_duration: float = 60.0,
                estimated_resources: Optional[Dict[str, float]] = None,
                dependencies: Optional[List[str]] = None,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a sleep-time task.
        
        Args:
            task_id: Optional unique identifier (generated if not provided)
            name: Human-readable name
            description: Detailed description
            priority: Priority level
            estimated_duration: Estimated duration in seconds
            estimated_resources: Dictionary of estimated resource requirements
            dependencies: List of task IDs that must complete before this task
            metadata: Additional metadata
        """
        self.task_id = task_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.priority = priority
        self.estimated_duration = estimated_duration
        self.estimated_resources = estimated_resources or {}
        self.dependencies = dependencies or []
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.scheduled_at = None
        self.started_at = None
        self.completed_at = None
        self.status = "pending"  # pending, scheduled, running, completed, failed
        self.result = None
        self.error = None
    
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
            "priority": self.priority.value,
            "estimated_duration": self.estimated_duration,
            "estimated_resources": self.estimated_resources,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "scheduled_at": self.scheduled_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "result": self.result,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SleepTimeTask':
        """
        Create a task from dictionary representation.
        
        Args:
            data: Dictionary containing task data
            
        Returns:
            SleepTimeTask instance
        """
        task = cls(
            task_id=data.get("task_id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            priority=TaskPriority(data.get("priority", 1)),
            estimated_duration=data.get("estimated_duration", 60.0),
            estimated_resources=data.get("estimated_resources", {}),
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {})
        )
        
        task.created_at = data.get("created_at", time.time())
        task.scheduled_at = data.get("scheduled_at")
        task.started_at = data.get("started_at")
        task.completed_at = data.get("completed_at")
        task.status = data.get("status", "pending")
        task.result = data.get("result")
        task.error = data.get("error")
        
        return task


class TaskExecutor(ABC):
    """
    Abstract base class for task executors.
    
    Task executors are responsible for executing sleep-time tasks.
    """
    
    @abstractmethod
    async def execute(self, task: SleepTimeTask) -> Dict[str, Any]:
        """
        Execute a task.
        
        Args:
            task: Task to execute
            
        Returns:
            Dictionary containing execution result
            
        Raises:
            Exception: If execution fails
        """
        pass


class ResourceMonitor:
    """
    Monitors system resource usage.
    
    This class tracks resource usage and availability to inform
    scheduling decisions.
    """
    
    def __init__(self):
        """Initialize resource monitor."""
        self.resource_usage = {
            "cpu": 0.0,
            "memory": 0.0,
            "credits": 0.0
        }
        self.resource_limits = {
            "cpu": 100.0,  # percentage
            "memory": 1000.0,  # MB
            "credits": float("inf")  # unlimited by default
        }
        self.usage_history = []
        self.last_update = time.time()
    
    def update_usage(self, 
                    cpu: Optional[float] = None,
                    memory: Optional[float] = None,
                    credits: Optional[float] = None) -> None:
        """
        Update current resource usage.
        
        Args:
            cpu: CPU usage percentage (0-100)
            memory: Memory usage in MB
            credits: Credit usage
        """
        if cpu is not None:
            self.resource_usage["cpu"] = cpu
            
        if memory is not None:
            self.resource_usage["memory"] = memory
            
        if credits is not None:
            self.resource_usage["credits"] = credits
            
        # Record history
        self.usage_history.append({
            "timestamp": time.time(),
            "usage": self.resource_usage.copy()
        })
        
        # Trim history if it gets too large
        if len(self.usage_history) > 1000:
            self.usage_history = self.usage_history[-1000:]
            
        self.last_update = time.time()
    
    def set_limits(self, 
                  cpu: Optional[float] = None,
                  memory: Optional[float] = None,
                  credits: Optional[float] = None) -> None:
        """
        Set resource limits.
        
        Args:
            cpu: CPU limit percentage (0-100)
            memory: Memory limit in MB
            credits: Credit limit
        """
        if cpu is not None:
            self.resource_limits["cpu"] = cpu
            
        if memory is not None:
            self.resource_limits["memory"] = memory
            
        if credits is not None:
            self.resource_limits["credits"] = credits
    
    def get_available_resources(self) -> Dict[str, float]:
        """
        Get available resources.
        
        Returns:
            Dictionary of available resources
        """
        return {
            resource: max(0.0, self.resource_limits[resource] - self.resource_usage[resource])
            for resource in self.resource_usage
        }
    
    def can_execute_task(self, task: SleepTimeTask) -> bool:
        """
        Check if a task can be executed with current resources.
        
        Args:
            task: Task to check
            
        Returns:
            True if task can be executed, False otherwise
        """
        available = self.get_available_resources()
        estimated = task.estimated_resources
        
        for resource, required in estimated.items():
            if resource in available and available[resource] < required:
                return False
                
        return True
    
    def get_idle_status(self) -> Dict[str, Any]:
        """
        Get system idle status.
        
        Returns:
            Dictionary with idle status information
        """
        # Calculate average usage over the last minute
        now = time.time()
        recent_history = [
            entry for entry in self.usage_history
            if entry["timestamp"] >= now - 60
        ]
        
        if not recent_history:
            return {
                "is_idle": True,
                "idle_resources": self.get_available_resources(),
                "confidence": 0.5  # Medium confidence due to lack of data
            }
            
        avg_usage = {}
        for resource in self.resource_usage:
            avg_usage[resource] = sum(
                entry["usage"].get(resource, 0) for entry in recent_history
            ) / len(recent_history)
            
        # Calculate idle threshold (30% of limit)
        idle_threshold = {
            resource: limit * 0.3
            for resource, limit in self.resource_limits.items()
        }
        
        # Check if system is idle
        is_idle = all(
            avg_usage.get(resource, 0) <= threshold
            for resource, threshold in idle_threshold.items()
        )
        
        # Calculate idle resources
        idle_resources = {
            resource: max(0.0, self.resource_limits[resource] - avg_usage.get(resource, 0))
            for resource in self.resource_usage
        }
        
        # Calculate confidence based on data recency and consistency
        data_age = now - self.last_update
        age_factor = max(0.0, min(1.0, 1.0 - data_age / 60))  # 0 if data is 60s old or more
        
        # Consistency factor based on standard deviation
        consistency = 1.0  # Default high consistency
        if len(recent_history) > 1:
            for resource in self.resource_usage:
                values = [entry["usage"].get(resource, 0) for entry in recent_history]
                mean = sum(values) / len(values)
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                std_dev = variance ** 0.5
                
                # Normalize std_dev relative to the resource limit
                normalized_std_dev = std_dev / max(1.0, self.resource_limits[resource])
                
                # Lower consistency for higher std_dev
                resource_consistency = max(0.0, 1.0 - normalized_std_dev * 5.0)
                consistency = min(consistency, resource_consistency)
                
        confidence = (age_factor + consistency) / 2.0
        
        return {
            "is_idle": is_idle,
            "idle_resources": idle_resources,
            "avg_usage": avg_usage,
            "confidence": confidence
        }


class TaskScheduler:
    """
    Schedules sleep-time tasks for execution.
    
    This class manages the task queue and determines when tasks
    should be executed.
    """
    
    def __init__(self, resource_monitor: ResourceMonitor):
        """
        Initialize scheduler.
        
        Args:
            resource_monitor: ResourceMonitor instance
        """
        self.resource_monitor = resource_monitor
        self.task_queue = []  # Priority queue of (priority_score, task_id)
        self.tasks = {}  # task_id -> SleepTimeTask
        self.scheduled_tasks = set()  # Set of scheduled task IDs
        self.completed_tasks = set()  # Set of completed task IDs
        self.failed_tasks = set()  # Set of failed task IDs
    
    def add_task(self, task: SleepTimeTask) -> str:
        """
        Add a task to the scheduler.
        
        Args:
            task: Task to add
            
        Returns:
            Task ID
            
        Raises:
            ValueError: If task with same ID already exists
        """
        if task.task_id in self.tasks:
            raise ValueError(f"Task with ID '{task.task_id}' already exists")
            
        self.tasks[task.task_id] = task
        
        # Calculate priority score (lower is higher priority)
        # Inverted priority value (so HIGH is lower score than LOW)
        priority_score = -task.priority.value
        
        # Add to priority queue
        heapq.heappush(self.task_queue, (priority_score, task.task_id))
        
        return task.task_id
    
    def get_task(self, task_id: str) -> Optional[SleepTimeTask]:
        """
        Get a task by ID.
        
        Args:
            task_id: ID of the task
            
        Returns:
            SleepTimeTask instance or None if not found
        """
        return self.tasks.get(task_id)
    
    def get_next_task(self) -> Optional[SleepTimeTask]:
        """
        Get the next task to execute.
        
        Returns:
            SleepTimeTask instance or None if no tasks are ready
        """
        # Check if there are any tasks in the queue
        if not self.task_queue:
            return None
            
        # Find the highest priority task that is ready to execute
        while self.task_queue:
            _, task_id = self.task_queue[0]  # Peek at the top task
            task = self.tasks[task_id]
            
            # Skip tasks that are already scheduled or completed
            if task_id in self.scheduled_tasks or task_id in self.completed_tasks:
                heapq.heappop(self.task_queue)  # Remove from queue
                continue
                
            # Check if all dependencies are completed
            dependencies_met = all(
                dep_id in self.completed_tasks
                for dep_id in task.dependencies
            )
            
            if not dependencies_met:
                # Move this task to the back of the queue
                heapq.heappop(self.task_queue)  # Remove from queue
                heapq.heappush(self.task_queue, (-task.priority.value, task_id))  # Add back with same priority
                continue
                
            # Check if resources are available
            if not self.resource_monitor.can_execute_task(task):
                # No resources available, return None
                return None
                
            # Task is ready to execute
            heapq.heappop(self.task_queue)  # Remove from queue
            self.scheduled_tasks.add(task_id)
            task.status = "scheduled"
            task.scheduled_at = time.time()
            return task
            
        return None
    
    def mark_task_completed(self, 
                          task_id: str,
                          result: Optional[Dict[str, Any]] = None) -> bool:
        """
        Mark a task as completed.
        
        Args:
            task_id: ID of the task
            result: Optional task result
            
        Returns:
            True if task was marked as completed, False if not found
        """
        task = self.get_task(task_id)
        if not task:
            return False
            
        task.status = "completed"
        task.completed_at = time.time()
        task.result = result
        
        self.scheduled_tasks.discard(task_id)
        self.completed_tasks.add(task_id)
        
        return True
    
    def mark_task_failed(self, 
                       task_id: str,
                       error: Optional[str] = None) -> bool:
        """
        Mark a task as failed.
        
        Args:
            task_id: ID of the task
            error: Optional error message
            
        Returns:
            True if task was marked as failed, False if not found
        """
        task = self.get_task(task_id)
        if not task:
            return False
            
        task.status = "failed"
        task.completed_at = time.time()
        task.error = error
        
        self.scheduled_tasks.discard(task_id)
        self.failed_tasks.add(task_id)
        
        # Re-queue the task with lower priority if it's not a critical failure
        if error and "critical" not in error.lower():
            # Calculate new priority (one level lower)
            new_priority = max(0, task.priority.value - 1)
            task.priority = TaskPriority(new_priority)
            
            # Reset task status
            task.status = "pending"
            task.scheduled_at = None
            task.completed_at = None
            
            # Add back to queue
            heapq.heappush(self.task_queue, (-task.priority.value, task_id))
            
        return True
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get the current status of the task queue.
        
        Returns:
            Dictionary with queue status information
        """
        pending_count = len(self.task_queue)
        scheduled_count = len(self.scheduled_tasks)
        completed_count = len(self.completed_tasks)
        failed_count = len(self.failed_tasks)
        
        # Count tasks by priority
        priority_counts = {
            priority.name: 0 for priority in TaskPriority
        }
        
        for _, task_id in self.task_queue:
            task = self.tasks[task_id]
            priority_counts[task.priority.name] += 1
            
        return {
            "pending_count": pending_count,
            "scheduled_count": scheduled_count,
            "completed_count": completed_count,
            "failed_count": failed_count,
            "priority_counts": priority_counts,
            "total_tasks": len(self.tasks)
        }


class SleepDetector:
    """
    Detects when the system is in a sleep state.
    
    This class monitors system activity and resource usage to determine
    when the system is idle and can execute sleep-time tasks.
    """
    
    def __init__(self, 
                resource_monitor: ResourceMonitor,
                idle_threshold: float = 0.3,
                min_idle_time: float = 10.0):
        """
        Initialize sleep detector.
        
        Args:
            resource_monitor: ResourceMonitor instance
            idle_threshold: Resource usage threshold for idle state (0.0-1.0)
            min_idle_time: Minimum time in seconds to consider system idle
        """
        self.resource_monitor = resource_monitor
        self.idle_threshold = idle_threshold
        self.min_idle_time = min_idle_time
        self.idle_start_time = None
        self.is_idle = False
    
    def check_idle_state(self) -> Dict[str, Any]:
        """
        Check if the system is in an idle state.
        
        Returns:
            Dictionary with idle state information
        """
        idle_status = self.resource_monitor.get_idle_status()
        
        # Check if system is idle based on resource usage
        current_is_idle = idle_status["is_idle"]
        
        # Update idle state
        current_time = time.time()
        
        if current_is_idle:
            # System is currently idle
            if not self.is_idle:
                # Transition to idle state
                if self.idle_start_time is None:
                    # Start counting idle time
                    self.idle_start_time = current_time
                elif current_time - self.idle_start_time >= self.min_idle_time:
                    # Idle for long enough, consider system idle
                    self.is_idle = True
            
        else:
            # System is not idle
            self.is_idle = False
            self.idle_start_time = None
            
        # Calculate idle duration
        idle_duration = 0.0
        if self.idle_start_time is not None:
            idle_duration = current_time - self.idle_start_time
            
        return {
            "is_idle": self.is_idle,
            "idle_duration": idle_duration,
            "idle_resources": idle_status["idle_resources"],
            "confidence": idle_status["confidence"]
        }
    
    def predict_idle_periods(self, 
                           lookahead_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Predict future idle periods based on historical patterns.
        
        Args:
            lookahead_hours: Number of hours to look ahead
            
        Returns:
            List of predicted idle periods
        """
        # Simple prediction based on time of day
        # In a real implementation, this would use more sophisticated analysis
        
        # Get current time
        now = datetime.now()
        
        # Predict idle periods for each hour
        idle_periods = []
        
        for hour_offset in range(lookahead_hours):
            future_time = now + timedelta(hours=hour_offset)
            hour = future_time.hour
            
            # Assume system is idle during night hours (0-6) and lunch (12-13)
            is_night = 0 <= hour < 6
            is_lunch = 12 <= hour < 13
            
            if is_night or is_lunch:
                # Predict idle period
                start_time = future_time.replace(minute=0, second=0)
                
                # Set end time
                if is_night:
                    end_hour = 6
                    if hour >= end_hour:
                        # Skip this period (already past end time)
                        continue
                    end_time = start_time.replace(hour=end_hour, minute=0, second=0)
                else:  # is_lunch
                    end_hour = 13
                    if hour >= end_hour:
                        # Skip this period (already past end time)
                        continue
                    end_time = start_time.replace(hour=end_hour, minute=0, second=0)
                
                # Calculate duration
                duration = (end_time - start_time).total_seconds()
                
                # Estimate available resources during this period
                # Assume more resources available during night than lunch
                available_resources = {
                    "cpu": 90.0 if is_night else 50.0,
                    "memory": 900.0 if is_night else 500.0,
                    "credits": 100.0 if is_night else 20.0
                }
                
                idle_periods.append({
                    "start_time": start_time.timestamp(),
                    "end_time": end_time.timestamp(),
                    "duration": duration,
                    "available_resources": available_resources,
                    "confidence": 0.8 if is_night else 0.6  # Higher confidence for night
                })
                
        return idle_periods


class BackgroundTaskRegistry:
    """
    Registry for background task executors.
    
    This class manages the registration and retrieval of task executors
    for different types of background tasks.
    """
    
    def __init__(self):
        """Initialize an empty registry."""
        self._executors = {}  # task_type -> TaskExecutor
    
    def register_executor(self, 
                         task_type: str,
                         executor: TaskExecutor) -> None:
        """
        Register a task executor.
        
        Args:
            task_type: Type of tasks this executor can handle
            executor: TaskExecutor instance
            
        Raises:
            ValueError: If executor for this task type already registered
        """
        if task_type in self._executors:
            raise ValueError(f"Executor for task type '{task_type}' already registered")
            
        self._executors[task_type] = executor
    
    def get_executor(self, task_type: str) -> Optional[TaskExecutor]:
        """
        Get a task executor by task type.
        
        Args:
            task_type: Type of tasks
            
        Returns:
            TaskExecutor instance or None if not found
        """
        return self._executors.get(task_type)
    
    def list_task_types(self) -> List[str]:
        """
        List all registered task types.
        
        Returns:
            List of task types
        """
        return list(self._executors.keys())


class SleepTimeOptimizer:
    """
    Main entry point for the Sleep-Time Optimization system.
    
    This class coordinates task scheduling, resource monitoring, and
    sleep detection to optimize resource usage during idle periods.
    """
    
    def __init__(self, 
                resource_monitor: ResourceMonitor,
                task_scheduler: TaskScheduler,
                sleep_detector: SleepDetector,
                task_registry: BackgroundTaskRegistry):
        """
        Initialize optimizer.
        
        Args:
            resource_monitor: ResourceMonitor instance
            task_scheduler: TaskScheduler instance
            sleep_detector: SleepDetector instance
            task_registry: BackgroundTaskRegistry instance
        """
        self.resource_monitor = resource_monitor
        self.task_scheduler = task_scheduler
        self.sleep_detector = sleep_detector
        self.task_registry = task_registry
        self.running = False
        self.worker_thread = None
        self.execution_history = []
    
    def start(self) -> None:
        """
        Start the optimizer.
        
        This method starts the background worker thread that monitors
        system state and executes tasks during idle periods.
        """
        if self.running:
            return
            
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop)
        self.worker_thread.daemon = True
        self.worker_thread.start()
    
    def stop(self) -> None:
        """
        Stop the optimizer.
        
        This method stops the background worker thread.
        """
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
            self.worker_thread = None
    
    def add_task(self, 
                name: str,
                task_type: str,
                parameters: Dict[str, Any],
                priority: TaskPriority = TaskPriority.MEDIUM,
                estimated_duration: float = 60.0,
                estimated_resources: Optional[Dict[str, float]] = None,
                dependencies: Optional[List[str]] = None) -> str:
        """
        Add a task to be executed during sleep time.
        
        Args:
            name: Human-readable name
            task_type: Type of task (must be registered in task registry)
            parameters: Parameters for task execution
            priority: Priority level
            estimated_duration: Estimated duration in seconds
            estimated_resources: Dictionary of estimated resource requirements
            dependencies: List of task IDs that must complete before this task
            
        Returns:
            Task ID
            
        Raises:
            ValueError: If task type is not registered
        """
        if task_type not in self.task_registry.list_task_types():
            raise ValueError(f"Task type '{task_type}' is not registered")
            
        task = SleepTimeTask(
            name=name,
            description=f"Sleep-time task of type '{task_type}'",
            priority=priority,
            estimated_duration=estimated_duration,
            estimated_resources=estimated_resources or {},
            dependencies=dependencies or [],
            metadata={
                "task_type": task_type,
                "parameters": parameters
            }
        )
        
        return self.task_scheduler.add_task(task)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Dictionary with task status or None if not found
        """
        task = self.task_scheduler.get_task(task_id)
        if not task:
            return None
            
        return task.to_dict()
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get the current system status.
        
        Returns:
            Dictionary with system status information
        """
        idle_status = self.sleep_detector.check_idle_state()
        queue_status = self.task_scheduler.get_queue_status()
        resource_status = {
            "usage": self.resource_monitor.resource_usage,
            "limits": self.resource_monitor.resource_limits,
            "available": self.resource_monitor.get_available_resources()
        }
        
        return {
            "idle_status": idle_status,
            "queue_status": queue_status,
            "resource_status": resource_status,
            "optimizer_running": self.running
        }
    
    def get_execution_history(self, 
                            max_entries: int = 100) -> List[Dict[str, Any]]:
        """
        Get the execution history.
        
        Args:
            max_entries: Maximum number of history entries to return
            
        Returns:
            List of execution history entries
        """
        # Return most recent entries first
        return sorted(
            self.execution_history[-max_entries:],
            key=lambda entry: entry["timestamp"],
            reverse=True
        )
    
    def predict_completion_times(self) -> Dict[str, float]:
        """
        Predict when pending tasks will be completed.
        
        Returns:
            Dictionary mapping task IDs to predicted completion timestamps
        """
        # Get current time
        now = time.time()
        
        # Get idle periods
        idle_periods = self.sleep_detector.predict_idle_periods()
        
        # Get pending tasks
        pending_tasks = []
        for task_id, task in self.task_scheduler.tasks.items():
            if task.status == "pending" and task_id not in self.task_scheduler.scheduled_tasks:
                pending_tasks.append(task)
                
        # Sort tasks by priority
        pending_tasks.sort(key=lambda t: -t.priority.value)
        
        # Simulate task execution during idle periods
        completion_times = {}
        remaining_tasks = pending_tasks.copy()
        
        for period in idle_periods:
            start_time = period["start_time"]
            end_time = period["end_time"]
            available_resources = period["available_resources"]
            
            # Skip periods in the past
            if end_time <= now:
                continue
                
            # Adjust start time if period has already started
            if start_time < now:
                start_time = now
                
            # Calculate available time
            available_time = end_time - start_time
            
            # Simulate task execution
            current_time = start_time
            
            while remaining_tasks and current_time < end_time:
                # Find the next task that can be executed
                executable_task = None
                
                for i, task in enumerate(remaining_tasks):
                    # Check if all dependencies are completed
                    dependencies_met = all(
                        dep_id in completion_times
                        for dep_id in task.dependencies
                    )
                    
                    if not dependencies_met:
                        continue
                        
                    # Check if resources are available
                    can_execute = True
                    for resource, required in task.estimated_resources.items():
                        if resource in available_resources and available_resources[resource] < required:
                            can_execute = False
                            break
                            
                    if can_execute:
                        executable_task = task
                        remaining_tasks.pop(i)
                        break
                        
                if not executable_task:
                    # No tasks can be executed in this period
                    break
                    
                # Simulate task execution
                execution_time = min(executable_task.estimated_duration, end_time - current_time)
                completion_time = current_time + execution_time
                
                # Record completion time
                completion_times[executable_task.task_id] = completion_time
                
                # Update current time
                current_time = completion_time
                
        # For tasks that couldn't be scheduled, estimate based on average task duration
        if remaining_tasks:
            # Calculate average task duration
            if pending_tasks:
                avg_duration = sum(task.estimated_duration for task in pending_tasks) / len(pending_tasks)
            else:
                avg_duration = 60.0  # Default 1 minute
                
            # Estimate completion times for remaining tasks
            last_completion = max(completion_times.values()) if completion_times else now
            
            for task in remaining_tasks:
                last_completion += avg_duration
                completion_times[task.task_id] = last_completion
                
        return completion_times
    
    def _worker_loop(self) -> None:
        """
        Background worker loop.
        
        This method runs in a separate thread and monitors system state,
        executing tasks during idle periods.
        """
        while self.running:
            try:
                # Check if system is idle
                idle_status = self.sleep_detector.check_idle_state()
                
                if idle_status["is_idle"]:
                    # System is idle, execute tasks
                    self._execute_pending_tasks()
                    
                # Sleep for a short time
                time.sleep(1.0)
                
            except Exception as e:
                # Log error and continue
                print(f"Error in sleep-time optimizer worker: {e}")
                time.sleep(5.0)
    
    def _execute_pending_tasks(self) -> None:
        """
        Execute pending tasks.
        
        This method executes tasks from the scheduler during idle periods.
        """
        # Get the next task to execute
        task = self.task_scheduler.get_next_task()
        
        if not task:
            # No tasks ready to execute
            return
            
        # Get task executor
        task_type = task.metadata.get("task_type")
        parameters = task.metadata.get("parameters", {})
        
        executor = self.task_registry.get_executor(task_type)
        if not executor:
            # No executor for this task type
            self.task_scheduler.mark_task_failed(
                task.task_id,
                f"No executor found for task type '{task_type}'"
            )
            return
            
        # Execute task
        task.status = "running"
        task.started_at = time.time()
        
        try:
            # Create asyncio event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Execute task
            result = loop.run_until_complete(executor.execute(task))
            
            # Mark task as completed
            self.task_scheduler.mark_task_completed(task.task_id, result)
            
            # Record execution
            self.execution_history.append({
                "timestamp": time.time(),
                "task_id": task.task_id,
                "task_type": task_type,
                "status": "completed",
                "duration": time.time() - task.started_at
            })
            
        except Exception as e:
            # Mark task as failed
            self.task_scheduler.mark_task_failed(task.task_id, str(e))
            
            # Record execution
            self.execution_history.append({
                "timestamp": time.time(),
                "task_id": task.task_id,
                "task_type": task_type,
                "status": "failed",
                "error": str(e),
                "duration": time.time() - task.started_at
            })
            
        finally:
            # Close event loop
            loop.close()
