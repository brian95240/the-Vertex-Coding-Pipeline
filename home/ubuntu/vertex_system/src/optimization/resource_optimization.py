"""
Resource Optimization Layer for Vertex Full-Stack System.

This module implements the resource optimization components that manage
credit usage, provider selection, and workload scheduling.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Tuple
import time
from enum import Enum

# Import interfaces
from ..interfaces.model_provider import ModelProvider, ProviderRegistry, ModelCapability


class ResourceType(Enum):
    """Enum representing different types of resources."""
    CREDITS = "credits"
    COMPUTE = "compute"
    MEMORY = "memory"
    NETWORK = "network"
    TIME = "time"


class CreditManager:
    """
    Manages credit allocation and tracking.
    
    Tracks credit usage across the system and enforces budget constraints.
    """
    
    def __init__(self, initial_balance: float = 0.0, budget_limit: Optional[float] = None):
        """
        Initialize credit manager.
        
        Args:
            initial_balance: Initial credit balance
            budget_limit: Optional maximum budget (None for unlimited)
        """
        self.balance = initial_balance
        self.budget_limit = budget_limit
        self.usage_history = []
        self.allocations = {}  # component_id -> allocation
    
    def allocate_credits(self, component_id: str, amount: float) -> bool:
        """
        Allocate credits to a component.
        
        Args:
            component_id: ID of the component requesting credits
            amount: Amount of credits to allocate
            
        Returns:
            True if allocation successful, False if insufficient credits
        """
        if self.budget_limit is not None and self.balance + amount > self.budget_limit:
            return False
            
        self.allocations[component_id] = self.allocations.get(component_id, 0.0) + amount
        self.balance += amount
        
        self.usage_history.append({
            "timestamp": time.time(),
            "component_id": component_id,
            "action": "allocate",
            "amount": amount,
            "balance": self.balance
        })
        
        return True
    
    def use_credits(self, component_id: str, amount: float) -> bool:
        """
        Use credits from a component's allocation.
        
        Args:
            component_id: ID of the component using credits
            amount: Amount of credits to use
            
        Returns:
            True if usage successful, False if insufficient allocation
        """
        allocation = self.allocations.get(component_id, 0.0)
        
        if allocation < amount:
            return False
            
        self.allocations[component_id] = allocation - amount
        
        self.usage_history.append({
            "timestamp": time.time(),
            "component_id": component_id,
            "action": "use",
            "amount": amount,
            "allocation_remaining": self.allocations[component_id]
        })
        
        return True
    
    def get_balance(self) -> float:
        """
        Get current total credit balance.
        
        Returns:
            Current balance
        """
        return self.balance
    
    def get_allocation(self, component_id: str) -> float:
        """
        Get current allocation for a component.
        
        Args:
            component_id: ID of the component
            
        Returns:
            Current allocation (0.0 if none)
        """
        return self.allocations.get(component_id, 0.0)
    
    def get_usage_report(self, 
                        component_id: Optional[str] = None, 
                        start_time: Optional[float] = None,
                        end_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Get usage report for a time period.
        
        Args:
            component_id: Optional component ID to filter by
            start_time: Optional start time (timestamp)
            end_time: Optional end time (timestamp)
            
        Returns:
            Dictionary containing usage statistics
        """
        # Filter history by parameters
        filtered_history = self.usage_history
        
        if component_id is not None:
            filtered_history = [
                entry for entry in filtered_history
                if entry["component_id"] == component_id
            ]
            
        if start_time is not None:
            filtered_history = [
                entry for entry in filtered_history
                if entry["timestamp"] >= start_time
            ]
            
        if end_time is not None:
            filtered_history = [
                entry for entry in filtered_history
                if entry["timestamp"] <= end_time
            ]
        
        # Calculate statistics
        total_allocated = sum(
            entry["amount"] for entry in filtered_history
            if entry["action"] == "allocate"
        )
        
        total_used = sum(
            entry["amount"] for entry in filtered_history
            if entry["action"] == "use"
        )
        
        # Group by component
        component_usage = {}
        for entry in filtered_history:
            component_id = entry["component_id"]
            if component_id not in component_usage:
                component_usage[component_id] = {"allocated": 0.0, "used": 0.0}
                
            if entry["action"] == "allocate":
                component_usage[component_id]["allocated"] += entry["amount"]
            elif entry["action"] == "use":
                component_usage[component_id]["used"] += entry["amount"]
        
        return {
            "total_allocated": total_allocated,
            "total_used": total_used,
            "component_usage": component_usage,
            "current_balance": self.balance,
            "current_allocations": self.allocations.copy()
        }


class CostAwareSelector:
    """
    Selects providers based on cost and capability.
    
    Optimizes provider selection to minimize cost while meeting requirements.
    """
    
    def __init__(self, 
                provider_registry: ProviderRegistry,
                credit_manager: CreditManager):
        """
        Initialize selector.
        
        Args:
            provider_registry: Registry of available providers
            credit_manager: Credit manager for budget constraints
        """
        self.provider_registry = provider_registry
        self.credit_manager = credit_manager
        self.cost_cache = {}  # (provider_id, model_id) -> cost_info
    
    def select_provider(self, 
                       component_id: str,
                       requirements: Dict[str, Any]) -> Tuple[str, ModelProvider]:
        """
        Select the most cost-effective provider meeting requirements.
        
        Args:
            component_id: ID of the component requesting a provider
            requirements: Dictionary of requirements (capabilities, etc.)
            
        Returns:
            Tuple of (provider_id, provider_instance)
            
        Raises:
            ValueError: If no suitable provider found or insufficient credits
        """
        # Extract requirements
        required_capabilities = requirements.get("capabilities", [])
        max_cost = requirements.get("max_cost")
        
        # Find providers with required capabilities
        candidate_providers = []
        
        for provider_id in self.provider_registry.list_providers():
            provider = self.provider_registry.get_provider(provider_id)
            
            # Check if provider has models with all required capabilities
            has_all_capabilities = True
            for capability in required_capabilities:
                capability_models = []
                for model in provider.list_available_models():
                    model_id = model.get("id")
                    model_capabilities = provider.get_model_capabilities(model_id)
                    if capability in model_capabilities:
                        capability_models.append(model_id)
                        break
                
                if not capability_models:
                    has_all_capabilities = False
                    break
            
            if has_all_capabilities:
                candidate_providers.append((provider_id, provider))
        
        if not candidate_providers:
            raise ValueError("No provider found with required capabilities")
        
        # Rank candidates by cost
        ranked_candidates = self._rank_by_cost(candidate_providers, required_capabilities, max_cost)
        
        if not ranked_candidates:
            raise ValueError("No provider found within cost constraints")
        
        # Select the top-ranked provider
        provider_id, provider = ranked_candidates[0]
        
        # Check credit allocation
        estimated_cost = self._estimate_provider_cost(provider_id, provider, requirements)
        
        if not self.credit_manager.get_allocation(component_id) >= estimated_cost:
            # Try to allocate more credits
            if not self.credit_manager.allocate_credits(component_id, estimated_cost):
                raise ValueError("Insufficient credits for provider selection")
        
        return provider_id, provider
    
    def _rank_by_cost(self, 
                     candidates: List[Tuple[str, ModelProvider]],
                     required_capabilities: List[str],
                     max_cost: Optional[float]) -> List[Tuple[str, ModelProvider]]:
        """
        Rank candidate providers by cost.
        
        Args:
            candidates: List of (provider_id, provider) tuples
            required_capabilities: List of required capabilities
            max_cost: Maximum cost constraint
            
        Returns:
            List of (provider_id, provider) tuples, sorted by cost
        """
        provider_costs = []
        
        for provider_id, provider in candidates:
            # Estimate cost for this provider
            cost = self._estimate_provider_cost(provider_id, provider, {
                "capabilities": required_capabilities
            })
            
            # Check max cost constraint
            if max_cost is not None and cost > max_cost:
                continue
                
            provider_costs.append((provider_id, provider, cost))
        
        # Sort by cost (ascending)
        provider_costs.sort(key=lambda x: x[2])
        
        # Return sorted providers without cost
        return [(pid, p) for pid, p, _ in provider_costs]
    
    def _estimate_provider_cost(self, 
                              provider_id: str,
                              provider: ModelProvider,
                              requirements: Dict[str, Any]) -> float:
        """
        Estimate the cost of using a provider.
        
        Args:
            provider_id: ID of the provider
            provider: Provider instance
            requirements: Dictionary of requirements
            
        Returns:
            Estimated cost
        """
        # Simple estimation based on a standard prompt
        # In a real implementation, this would be more sophisticated
        standard_prompt = "This is a standard test prompt to estimate cost."
        
        # Find the cheapest model that meets requirements
        min_cost = float("inf")
        
        for model in provider.list_available_models():
            model_id = model.get("id")
            
            # Check if model meets capability requirements
            if "capabilities" in requirements:
                model_capabilities = provider.get_model_capabilities(model_id)
                if not all(cap in model_capabilities for cap in requirements["capabilities"]):
                    continue
            
            # Check cost cache
            cache_key = (provider_id, model_id)
            if cache_key in self.cost_cache:
                cost = self.cost_cache[cache_key]["cost"]
            else:
                # Estimate cost
                try:
                    cost = provider.estimate_cost(model_id, standard_prompt)
                    self.cost_cache[cache_key] = {
                        "cost": cost,
                        "timestamp": time.time()
                    }
                except Exception:
                    # If estimation fails, use a high default
                    cost = float("inf")
            
            min_cost = min(min_cost, cost)
        
        return min_cost if min_cost != float("inf") else 1.0  # Default if no models found


class PredictiveBatchScheduler:
    """
    Schedules batches based on workload prediction.
    
    Optimizes batch scheduling to maximize resource utilization.
    """
    
    def __init__(self, credit_manager: CreditManager):
        """
        Initialize scheduler.
        
        Args:
            credit_manager: Credit manager for budget constraints
        """
        self.credit_manager = credit_manager
        self.workload_history = []
        self.current_schedule = []
    
    def record_workload(self, 
                       timestamp: float,
                       batch_size: int,
                       execution_time: float,
                       resource_usage: Dict[str, float]):
        """
        Record workload data for prediction.
        
        Args:
            timestamp: Time of execution
            batch_size: Size of the batch
            execution_time: Time taken to execute
            resource_usage: Dictionary of resource usage metrics
        """
        self.workload_history.append({
            "timestamp": timestamp,
            "batch_size": batch_size,
            "execution_time": execution_time,
            "resource_usage": resource_usage
        })
        
        # Trim history if it gets too large
        if len(self.workload_history) > 1000:
            self.workload_history = self.workload_history[-1000:]
    
    def predict_execution_time(self, batch_size: int) -> float:
        """
        Predict execution time for a batch size.
        
        Args:
            batch_size: Size of the batch
            
        Returns:
            Predicted execution time
        """
        if not self.workload_history:
            # No history, use simple linear estimate
            return batch_size * 0.1  # 100ms per task
        
        # Find similar batch sizes in history
        similar_batches = [
            entry for entry in self.workload_history
            if 0.8 * batch_size <= entry["batch_size"] <= 1.2 * batch_size
        ]
        
        if similar_batches:
            # Average execution time of similar batches
            avg_time = sum(entry["execution_time"] for entry in similar_batches) / len(similar_batches)
            return avg_time
        else:
            # Linear extrapolation from closest batch size
            closest_entry = min(
                self.workload_history,
                key=lambda entry: abs(entry["batch_size"] - batch_size)
            )
            
            # Simple linear scaling
            scale_factor = batch_size / closest_entry["batch_size"]
            return closest_entry["execution_time"] * scale_factor
    
    def predict_resource_usage(self, batch_size: int) -> Dict[str, float]:
        """
        Predict resource usage for a batch size.
        
        Args:
            batch_size: Size of the batch
            
        Returns:
            Dictionary of predicted resource usage
        """
        if not self.workload_history:
            # No history, use simple linear estimate
            return {
                "credits": batch_size * 0.01,  # 0.01 credits per task
                "memory": batch_size * 10,     # 10MB per task
                "compute": batch_size * 0.05   # 5% CPU per task
            }
        
        # Find similar batch sizes in history
        similar_batches = [
            entry for entry in self.workload_history
            if 0.8 * batch_size <= entry["batch_size"] <= 1.2 * batch_size
        ]
        
        if similar_batches:
            # Average resource usage of similar batches
            avg_usage = {}
            for resource in similar_batches[0]["resource_usage"]:
                avg_usage[resource] = sum(
                    entry["resource_usage"].get(resource, 0) 
                    for entry in similar_batches
                ) / len(similar_batches)
            return avg_usage
        else:
            # Linear extrapolation from closest batch size
            closest_entry = min(
                self.workload_history,
                key=lambda entry: abs(entry["batch_size"] - batch_size)
            )
            
            # Simple linear scaling
            scale_factor = batch_size / closest_entry["batch_size"]
            return {
                resource: value * scale_factor
                for resource, value in closest_entry["resource_usage"].items()
            }
    
    def schedule_batch(self, 
                      component_id: str,
                      batch_size: int,
                      priority: int = 1,
                      deadline: Optional[float] = None) -> Dict[str, Any]:
        """
        Schedule a batch for execution.
        
        Args:
            component_id: ID of the component scheduling the batch
            batch_size: Size of the batch
            priority: Priority level (higher is more important)
            deadline: Optional deadline (timestamp)
            
        Returns:
            Dictionary containing schedule information
            
        Raises:
            ValueError: If insufficient credits or resources
        """
        # Predict resource usage
        predicted_resources = self.predict_resource_usage(batch_size)
        predicted_time = self.predict_execution_time(batch_size)
        
        # Check credit allocation
        required_credits = predicted_resources.get("credits", 0.0)
        
        if not self.credit_manager.get_allocation(component_id) >= required_credits:
            # Try to allocate more credits
            if not self.credit_manager.allocate_credits(component_id, required_credits):
                raise ValueError("Insufficient credits for batch scheduling")
        
        # Create schedule entry
        schedule_id = f"batch_{int(time.time())}_{len(self.current_schedule)}"
        
        schedule_entry = {
            "schedule_id": schedule_id,
            "component_id": component_id,
            "batch_size": batch_size,
            "priority": priority,
            "deadline": deadline,
            "predicted_time": predicted_time,
            "predicted_resources": predicted_resources,
            "scheduled_at": time.time(),
            "status": "scheduled"
        }
        
        # Add to schedule
        self.current_schedule.append(schedule_entry)
        
        # Sort schedule by priority and deadline
        self._sort_schedule()
        
        return schedule_entry
    
    def get_next_batch(self) -> Optional[Dict[str, Any]]:
        """
        Get the next batch to execute.
        
        Returns:
            Schedule entry for the next batch, or None if none ready
        """
        if not self.current_schedule:
            return None
            
        # Return the highest priority batch
        next_batch = self.current_schedule[0]
        next_batch["status"] = "executing"
        
        return next_batch
    
    def complete_batch(self, 
                      schedule_id: str,
                      execution_time: float,
                      resource_usage: Dict[str, float],
                      success: bool = True) -> None:
        """
        Mark a batch as completed.
        
        Args:
            schedule_id: ID of the schedule entry
            execution_time: Actual execution time
            resource_usage: Actual resource usage
            success: Whether execution was successful
            
        Raises:
            ValueError: If schedule ID not found
        """
        # Find the schedule entry
        for i, entry in enumerate(self.current_schedule):
            if entry["schedule_id"] == schedule_id:
                # Record workload data
                self.record_workload(
                    time.time(),
                    entry["batch_size"],
                    execution_time,
                    resource_usage
                )
                
                # Use credits
                self.credit_manager.use_credits(
                    entry["component_id"],
                    resource_usage.get("credits", 0.0)
                )
                
                # Remove from schedule
                self.current_schedule.pop(i)
                return
                
        raise ValueError(f"Schedule ID not found: {schedule_id}")
    
    def _sort_schedule(self) -> None:
        """
        Sort the schedule by priority and deadline.
        """
        def sort_key(entry):
            # Higher priority comes first
            priority_key = -entry["priority"]
            
            # Earlier deadline comes first (if specified)
            deadline_key = entry["deadline"] if entry["deadline"] is not None else float("inf")
            
            return (priority_key, deadline_key)
            
        self.current_schedule.sort(key=sort_key)


class ResourceOptimizationLayer:
    """
    Main entry point for the resource optimization layer.
    
    Coordinates credit management, provider selection, and batch scheduling.
    """
    
    def __init__(self, 
                credit_manager: CreditManager,
                cost_selector: CostAwareSelector,
                batch_scheduler: PredictiveBatchScheduler):
        """
        Initialize with required components.
        
        Args:
            credit_manager: CreditManager instance
            cost_selector: CostAwareSelector instance
            batch_scheduler: PredictiveBatchScheduler instance
        """
        self.credit_manager = credit_manager
        self.cost_selector = cost_selector
        self.batch_scheduler = batch_scheduler
    
    def register_component(self, 
                         component_id: str,
                         initial_allocation: float = 0.0) -> bool:
        """
        Register a component with the optimization layer.
        
        Args:
            component_id: ID of the component
            initial_allocation: Initial credit allocation
            
        Returns:
            True if registration successful, False otherwise
        """
        return self.credit_manager.allocate_credits(component_id, initial_allocation)
    
    def select_provider(self, 
                       component_id: str,
                       requirements: Dict[str, Any]) -> Tuple[str, ModelProvider]:
        """
        Select a provider based on requirements and cost.
        
        Args:
            component_id: ID of the component
            requirements: Dictionary of requirements
            
        Returns:
            Tuple of (provider_id, provider_instance)
            
        Raises:
            ValueError: If no suitable provider found or insufficient credits
        """
        return self.cost_selector.select_provider(component_id, requirements)
    
    def schedule_batch(self, 
                      component_id: str,
                      batch_size: int,
                      priority: int = 1,
                      deadline: Optional[float] = None) -> Dict[str, Any]:
        """
        Schedule a batch for execution.
        
        Args:
            component_id: ID of the component
            batch_size: Size of the batch
            priority: Priority level
            deadline: Optional deadline
            
        Returns:
            Dictionary containing schedule information
            
        Raises:
            ValueError: If insufficient credits or resources
        """
        return self.batch_scheduler.schedule_batch(
            component_id, batch_size, priority, deadline)
    
    def get_usage_report(self, 
                        component_id: Optional[str] = None,
                        start_time: Optional[float] = None,
                        end_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Get resource usage report.
        
        Args:
            component_id: Optional component ID filter
            start_time: Optional start time
            end_time: Optional end time
            
        Returns:
            Dictionary containing usage statistics
        """
        return self.credit_manager.get_usage_report(
            component_id, start_time, end_time)
    
    def optimize_resource_allocation(self) -> Dict[str, Any]:
        """
        Optimize resource allocation based on usage patterns.
        
        Returns:
            Dictionary containing optimization results
        """
        # Get current allocations
        current_allocations = self.credit_manager.get_usage_report()["current_allocations"]
        
        # Get usage history
        usage_report = self.credit_manager.get_usage_report()
        
        # Simple optimization: reallocate based on usage ratio
        optimized_allocations = {}
        total_used = 0.0
        
        for component_id, usage in usage_report["component_usage"].items():
            allocated = usage["allocated"]
            used = usage["used"]
            
            # Calculate usage ratio (with minimum to avoid division by zero)
            usage_ratio = used / max(allocated, 0.001)
            
            # Store for later normalization
            optimized_allocations[component_id] = usage_ratio
            total_used += used
        
        # Normalize to maintain total allocation
        total_allocation = sum(current_allocations.values())
        
        for component_id in optimized_allocations:
            # Allocate proportionally to usage ratio
            if total_used > 0:
                optimized_allocations[component_id] = (
                    optimized_allocations[component_id] / total_used * total_allocation
                )
            else:
                # Equal allocation if no usage data
                optimized_allocations[component_id] = total_allocation / len(optimized_allocations)
        
        # Return optimization results
        return {
            "current_allocations": current_allocations,
            "optimized_allocations": optimized_allocations,
            "total_allocation": total_allocation
        }
