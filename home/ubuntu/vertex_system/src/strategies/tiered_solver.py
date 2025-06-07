"""
Tiered Problem-Solving Framework for Vertex Full-Stack System.

This module implements the tiered problem-solving framework with various
recursive strategies for handling complex tasks efficiently.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Type, Callable
import importlib
import time
import asyncio
import uuid
from enum import Enum

# Import Task definition
from ..orchestration.task_orchestrator import Task, TaskStatus


class RecursionType(Enum):
    """Enum representing different types of recursion strategies."""
    TAIL = "tail_recursion"
    NON_TAIL = "non_tail_recursion"
    TREE = "tree_recursion"
    MUTUAL = "mutual_recursion"
    DIVIDE_AND_CONQUER = "divide_and_conquer"
    BACKTRACKING = "backtracking"


class ProblemType(Enum):
    """Enum representing different types of problems."""
    TRANSFORMATION = "transformation"
    SEARCH = "search"
    OPTIMIZATION = "optimization"
    GENERATION = "generation"
    ANALYSIS = "analysis"
    VALIDATION = "validation"


class Strategy(ABC):
    """
    Abstract base class for problem-solving strategies.
    
    Strategies implement specific recursive approaches to solving problems.
    """
    
    @abstractmethod
    def process(self, data: Any, context: Dict[str, Any], **kwargs) -> Any:
        """
        Process input data using this strategy.
        
        Args:
            data: Input data to process
            context: Execution context
            **kwargs: Additional parameters
            
        Returns:
            Processing result
        """
        pass
    
    @abstractmethod
    def validate_input(self, data: Any) -> bool:
        """
        Validate input data for this strategy.
        
        Args:
            data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of this strategy.
        
        Returns:
            Dictionary containing health status
        """
        pass


class StrategyMetadata:
    """
    Metadata for a problem-solving strategy.
    
    Contains information about a strategy's capabilities, requirements,
    and performance characteristics.
    """
    
    def __init__(self,
                strategy_id: str,
                name: str,
                recursion_type: RecursionType,
                problem_types: List[ProblemType],
                description: str,
                module_path: str,
                class_name: str,
                complexity_profile: Dict[str, str],
                resource_requirements: Dict[str, Any],
                input_schema: Optional[Dict[str, Any]] = None,
                output_schema: Optional[Dict[str, Any]] = None):
        """
        Initialize strategy metadata.
        
        Args:
            strategy_id: Unique identifier
            name: Human-readable name
            recursion_type: Type of recursion used
            problem_types: Types of problems this strategy can solve
            description: Detailed description
            module_path: Import path to the module containing the strategy
            class_name: Name of the strategy class
            complexity_profile: Time/space complexity characteristics
            resource_requirements: Estimated resource needs
            input_schema: Expected input data format
            output_schema: Expected output data format
        """
        self.strategy_id = strategy_id
        self.name = name
        self.recursion_type = recursion_type
        self.problem_types = problem_types
        self.description = description
        self.module_path = module_path
        self.class_name = class_name
        self.complexity_profile = complexity_profile
        self.resource_requirements = resource_requirements
        self.input_schema = input_schema or {}
        self.output_schema = output_schema or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metadata to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "recursion_type": self.recursion_type.value,
            "problem_types": [pt.value for pt in self.problem_types],
            "description": self.description,
            "module_path": self.module_path,
            "class_name": self.class_name,
            "complexity_profile": self.complexity_profile,
            "resource_requirements": self.resource_requirements,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyMetadata':
        """
        Create metadata from dictionary.
        
        Args:
            data: Dictionary containing metadata
            
        Returns:
            StrategyMetadata instance
        """
        return cls(
            strategy_id=data["strategy_id"],
            name=data["name"],
            recursion_type=RecursionType(data["recursion_type"]),
            problem_types=[ProblemType(pt) for pt in data["problem_types"]],
            description=data["description"],
            module_path=data["module_path"],
            class_name=data["class_name"],
            complexity_profile=data["complexity_profile"],
            resource_requirements=data["resource_requirements"],
            input_schema=data.get("input_schema"),
            output_schema=data.get("output_schema")
        )


class StrategyProxy:
    """
    Proxy for lazy-loading strategies.
    
    Acts as a virtual proxy that loads the actual strategy only when needed.
    """
    
    def __init__(self, metadata: StrategyMetadata):
        """
        Initialize with strategy metadata.
        
        Args:
            metadata: Metadata for the strategy to proxy
        """
        self.metadata = metadata
        self._strategy = None
    
    def _load_strategy(self) -> Strategy:
        """
        Load the actual strategy implementation.
        
        Returns:
            Strategy instance
            
        Raises:
            ImportError: If module cannot be imported
            AttributeError: If class cannot be found in module
        """
        if self._strategy is None:
            try:
                module = importlib.import_module(self.metadata.module_path)
                strategy_class = getattr(module, self.metadata.class_name)
                self._strategy = strategy_class()
            except (ImportError, AttributeError) as e:
                raise ValueError(f"Failed to load strategy {self.metadata.strategy_id}: {e}")
        
        return self._strategy
    
    def process(self, data: Any, context: Dict[str, Any], **kwargs) -> Any:
        """
        Process input data using the strategy.
        
        Args:
            data: Input data to process
            context: Execution context
            **kwargs: Additional parameters
            
        Returns:
            Processing result
        """
        strategy = self._load_strategy()
        return strategy.process(data, context, **kwargs)
    
    def validate_input(self, data: Any) -> bool:
        """
        Validate input data for the strategy.
        
        Args:
            data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        strategy = self._load_strategy()
        return strategy.validate_input(data)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the strategy.
        
        Returns:
            Dictionary containing health status
        """
        if self._strategy is None:
            return {"status": "unloaded", "strategy_id": self.metadata.strategy_id}
        
        return self._strategy.health_check()


class StrategyRegistry:
    """
    Registry for problem-solving strategies.
    
    Manages strategy registration, discovery, and lazy loading.
    """
    
    def __init__(self):
        """Initialize an empty strategy registry."""
        self._strategies = {}  # strategy_id -> StrategyProxy
        self._metadata = {}    # strategy_id -> StrategyMetadata
    
    def register_strategy(self, metadata: StrategyMetadata) -> None:
        """
        Register a strategy.
        
        Args:
            metadata: Strategy metadata
            
        Raises:
            ValueError: If strategy with same ID already registered
        """
        if metadata.strategy_id in self._metadata:
            raise ValueError(f"Strategy with ID '{metadata.strategy_id}' already registered")
        
        self._metadata[metadata.strategy_id] = metadata
        self._strategies[metadata.strategy_id] = StrategyProxy(metadata)
    
    def get_strategy(self, strategy_id: str) -> Strategy:
        """
        Get a strategy by ID.
        
        Args:
            strategy_id: ID of the strategy
            
        Returns:
            Strategy instance (via proxy)
            
        Raises:
            KeyError: If strategy not found
        """
        if strategy_id not in self._strategies:
            raise KeyError(f"No strategy registered with ID '{strategy_id}'")
        
        return self._strategies[strategy_id]
    
    def get_strategy_metadata(self, strategy_id: str) -> StrategyMetadata:
        """
        Get metadata for a strategy.
        
        Args:
            strategy_id: ID of the strategy
            
        Returns:
            StrategyMetadata instance
            
        Raises:
            KeyError: If strategy not found
        """
        if strategy_id not in self._metadata:
            raise KeyError(f"No strategy registered with ID '{strategy_id}'")
        
        return self._metadata[strategy_id]
    
    def list_strategies(self, 
                       problem_type: Optional[ProblemType] = None,
                       recursion_type: Optional[RecursionType] = None) -> List[str]:
        """
        List strategies, optionally filtered by type.
        
        Args:
            problem_type: Optional filter by problem type
            recursion_type: Optional filter by recursion type
            
        Returns:
            List of strategy IDs
        """
        result = []
        
        for strategy_id, metadata in self._metadata.items():
            if problem_type and problem_type not in metadata.problem_types:
                continue
                
            if recursion_type and metadata.recursion_type != recursion_type:
                continue
                
            result.append(strategy_id)
            
        return result


class ProblemProfile:
    """
    Profile of a problem for strategy selection.
    
    Contains analysis of a problem's characteristics to help select
    the most appropriate strategy.
    """
    
    def __init__(self,
                problem_id: str,
                problem_type: ProblemType,
                input_size: int,
                estimated_complexity: str,
                constraints: Dict[str, Any],
                features: Dict[str, Any]):
        """
        Initialize a problem profile.
        
        Args:
            problem_id: Unique identifier
            problem_type: Type of problem
            input_size: Size of input data
            estimated_complexity: Estimated complexity (e.g., "O(n)", "O(n^2)")
            constraints: Resource constraints (e.g., time, memory)
            features: Additional problem features
        """
        self.problem_id = problem_id
        self.problem_type = problem_type
        self.input_size = input_size
        self.estimated_complexity = estimated_complexity
        self.constraints = constraints
        self.features = features
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert profile to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "problem_id": self.problem_id,
            "problem_type": self.problem_type.value,
            "input_size": self.input_size,
            "estimated_complexity": self.estimated_complexity,
            "constraints": self.constraints,
            "features": self.features
        }


class ProblemAnalyzer:
    """
    Analyzes problems to create profiles for strategy selection.
    
    Extracts key characteristics from tasks to guide strategy selection.
    """
    
    def analyze_problem(self, task: Task) -> ProblemProfile:
        """
        Analyze a task to create a problem profile.
        
        Args:
            task: Task to analyze
            
        Returns:
            ProblemProfile instance
        """
        # Extract problem type from task description or input data
        problem_type = self._determine_problem_type(task)
        
        # Estimate input size
        input_size = self._estimate_input_size(task.input_data)
        
        # Estimate complexity
        complexity = self._estimate_complexity(task, problem_type, input_size)
        
        # Extract constraints
        constraints = {
            "time_limit": task.timeout_seconds,
            "max_retries": task.max_retries
        }
        
        # Extract additional features
        features = self._extract_features(task)
        
        return ProblemProfile(
            problem_id=task.task_id,
            problem_type=problem_type,
            input_size=input_size,
            estimated_complexity=complexity,
            constraints=constraints,
            features=features
        )
    
    def _determine_problem_type(self, task: Task) -> ProblemType:
        """
        Determine the type of problem from a task.
        
        Args:
            task: Task to analyze
            
        Returns:
            ProblemType enum value
        """
        # Simple keyword-based classification for now
        description = task.description.lower()
        
        if any(kw in description for kw in ["transform", "convert", "process"]):
            return ProblemType.TRANSFORMATION
        elif any(kw in description for kw in ["search", "find", "locate"]):
            return ProblemType.SEARCH
        elif any(kw in description for kw in ["optimize", "maximize", "minimize"]):
            return ProblemType.OPTIMIZATION
        elif any(kw in description for kw in ["generate", "create", "produce"]):
            return ProblemType.GENERATION
        elif any(kw in description for kw in ["analyze", "examine", "assess"]):
            return ProblemType.ANALYSIS
        elif any(kw in description for kw in ["validate", "verify", "check"]):
            return ProblemType.VALIDATION
        else:
            # Default to transformation
            return ProblemType.TRANSFORMATION
    
    def _estimate_input_size(self, input_data: Dict[str, Any]) -> int:
        """
        Estimate the size of input data.
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Estimated size (arbitrary units)
        """
        # Simple estimation based on dictionary size
        # In a real implementation, this would be more sophisticated
        return len(str(input_data))
    
    def _estimate_complexity(self, 
                           task: Task, 
                           problem_type: ProblemType, 
                           input_size: int) -> str:
        """
        Estimate the complexity of a problem.
        
        Args:
            task: Task to analyze
            problem_type: Type of problem
            input_size: Size of input data
            
        Returns:
            Complexity estimate as a string (e.g., "O(n)", "O(n^2)")
        """
        # Simple heuristic based on problem type and input size
        if problem_type == ProblemType.SEARCH:
            return "O(n)" if input_size < 1000 else "O(n log n)"
        elif problem_type == ProblemType.OPTIMIZATION:
            return "O(n^2)" if input_size < 500 else "O(n^3)"
        elif problem_type == ProblemType.TRANSFORMATION:
            return "O(n)"
        else:
            return "O(n)"
    
    def _extract_features(self, task: Task) -> Dict[str, Any]:
        """
        Extract additional features from a task.
        
        Args:
            task: Task to analyze
            
        Returns:
            Dictionary of features
        """
        # Extract features from task description and input data
        # In a real implementation, this would use more sophisticated analysis
        features = {
            "has_dependencies": len(task.dependencies) > 0,
            "priority": task.priority.value
        }
        
        return features


class StrategySelector:
    """
    Selects the most appropriate strategy for a problem.
    
    Uses problem profiles and historical performance data to choose
    the optimal strategy or sequence of strategies.
    """
    
    def __init__(self, registry: StrategyRegistry):
        """
        Initialize with strategy registry.
        
        Args:
            registry: StrategyRegistry instance
        """
        self.registry = registry
    
    def select_strategy(self, 
                       profile: ProblemProfile, 
                       historical_data: Optional[Dict[str, Any]] = None) -> Union[str, List[str]]:
        """
        Select the best strategy for a problem.
        
        Args:
            profile: Problem profile
            historical_data: Optional historical performance data
            
        Returns:
            Strategy ID or list of strategy IDs (for a workflow)
            
        Raises:
            ValueError: If no suitable strategy found
        """
        # Get candidate strategies for this problem type
        candidates = self.registry.list_strategies(problem_type=profile.problem_type)
        
        if not candidates:
            # Fall back to any strategy if no type-specific ones found
            candidates = self.registry.list_strategies()
            
        if not candidates:
            raise ValueError(f"No strategies available for problem type {profile.problem_type}")
        
        # Rank candidates based on problem profile and historical data
        ranked_candidates = self._rank_candidates(candidates, profile, historical_data)
        
        # Determine if we need a single strategy or a workflow
        if self._needs_workflow(profile):
            # Create a workflow of complementary strategies
            return self._create_workflow(ranked_candidates, profile)
        else:
            # Return the top-ranked strategy
            return ranked_candidates[0]
    
    def _rank_candidates(self, 
                        candidates: List[str], 
                        profile: ProblemProfile,
                        historical_data: Optional[Dict[str, Any]]) -> List[str]:
        """
        Rank candidate strategies based on suitability.
        
        Args:
            candidates: List of candidate strategy IDs
            profile: Problem profile
            historical_data: Optional historical performance data
            
        Returns:
            List of strategy IDs, sorted by rank (best first)
        """
        scores = {}
        
        for strategy_id in candidates:
            metadata = self.registry.get_strategy_metadata(strategy_id)
            
            # Base score: problem type match
            scores[strategy_id] = 10 if profile.problem_type in metadata.problem_types else 0
            
            # Adjust for complexity match
            complexity_score = self._score_complexity_match(metadata, profile)
            scores[strategy_id] += complexity_score
            
            # Adjust for resource constraints
            constraint_score = self._score_constraint_match(metadata, profile)
            scores[strategy_id] += constraint_score
            
            # Adjust for historical performance if available
            if historical_data and strategy_id in historical_data:
                history_score = self._score_historical_performance(
                    strategy_id, profile, historical_data)
                scores[strategy_id] += history_score
        
        # Sort candidates by score (descending)
        return sorted(candidates, key=lambda sid: scores[sid], reverse=True)
    
    def _score_complexity_match(self, 
                              metadata: StrategyMetadata, 
                              profile: ProblemProfile) -> float:
        """
        Score how well a strategy's complexity profile matches a problem.
        
        Args:
            metadata: Strategy metadata
            profile: Problem profile
            
        Returns:
            Score (higher is better)
        """
        # Simple scoring based on complexity class
        # In a real implementation, this would be more sophisticated
        strategy_complexity = metadata.complexity_profile.get("time", "O(n)")
        problem_complexity = profile.estimated_complexity
        
        # Exact match is best
        if strategy_complexity == problem_complexity:
            return 5.0
            
        # Strategy with better complexity than needed is good
        if strategy_complexity == "O(n)" and problem_complexity in ["O(n log n)", "O(n^2)"]:
            return 3.0
            
        # Strategy with worse complexity than ideal is less good
        if strategy_complexity in ["O(n log n)", "O(n^2)"] and problem_complexity == "O(n)":
            return 1.0
            
        # Default score
        return 0.0
    
    def _score_constraint_match(self, 
                              metadata: StrategyMetadata, 
                              profile: ProblemProfile) -> float:
        """
        Score how well a strategy meets a problem's constraints.
        
        Args:
            metadata: Strategy metadata
            profile: Problem profile
            
        Returns:
            Score (higher is better)
        """
        score = 0.0
        
        # Check time constraint
        if profile.constraints.get("time_limit"):
            strategy_time = metadata.resource_requirements.get("avg_time_ms", 1000)
            time_limit = profile.constraints["time_limit"] * 1000  # convert to ms
            
            if strategy_time <= time_limit / 2:
                score += 3.0  # Well within limit
            elif strategy_time <= time_limit:
                score += 1.0  # Within limit
            else:
                score -= 5.0  # Exceeds limit
        
        # Add more constraint checks as needed
        
        return score
    
    def _score_historical_performance(self, 
                                    strategy_id: str, 
                                    profile: ProblemProfile,
                                    historical_data: Dict[str, Any]) -> float:
        """
        Score a strategy based on historical performance.
        
        Args:
            strategy_id: Strategy ID
            profile: Problem profile
            historical_data: Historical performance data
            
        Returns:
            Score (higher is better)
        """
        # Extract relevant history for this strategy
        strategy_history = historical_data.get(strategy_id, {})
        
        # No history for this strategy
        if not strategy_history:
            return 0.0
            
        # Check success rate
        success_rate = strategy_history.get("success_rate", 0.0)
        
        # Check average execution time
        avg_time = strategy_history.get("avg_execution_time", float("inf"))
        
        # Combine metrics into a score
        score = success_rate * 5.0  # Up to 5 points for 100% success
        
        # Add time-based score if we have a time constraint
        if profile.constraints.get("time_limit") and avg_time != float("inf"):
            time_limit = profile.constraints["time_limit"] * 1000  # convert to ms
            time_ratio = min(1.0, time_limit / avg_time)
            score += time_ratio * 3.0  # Up to 3 points for being fast
        
        return score
    
    def _needs_workflow(self, profile: ProblemProfile) -> bool:
        """
        Determine if a problem needs a workflow of multiple strategies.
        
        Args:
            profile: Problem profile
            
        Returns:
            True if a workflow is needed, False otherwise
        """
        # Simple heuristic: complex problems or large inputs may benefit from workflows
        if profile.estimated_complexity in ["O(n^2)", "O(n^3)"]:
            return True
            
        if profile.input_size > 10000:
            return True
            
        # Check for specific features that suggest workflow need
        if profile.features.get("has_dependencies", False):
            return True
            
        return False
    
    def _create_workflow(self, 
                       ranked_candidates: List[str], 
                       profile: ProblemProfile) -> List[str]:
        """
        Create a workflow of complementary strategies.
        
        Args:
            ranked_candidates: List of strategy IDs, ranked by suitability
            profile: Problem profile
            
        Returns:
            List of strategy IDs forming a workflow
        """
        workflow = []
        
        # Start with the top-ranked strategy
        if ranked_candidates:
            workflow.append(ranked_candidates[0])
        
        # Add complementary strategies based on recursion type
        # Try to create a balanced workflow with different recursion types
        recursion_types_in_workflow = set()
        
        if workflow:
            top_metadata = self.registry.get_strategy_metadata(workflow[0])
            recursion_types_in_workflow.add(top_metadata.recursion_type)
        
        # Add strategies with different recursion types
        for strategy_id in ranked_candidates[1:]:
            metadata = self.registry.get_strategy_metadata(strategy_id)
            
            if metadata.recursion_type not in recursion_types_in_workflow:
                workflow.append(strategy_id)
                recursion_types_in_workflow.add(metadata.recursion_type)
                
                # Limit workflow size
                if len(workflow) >= 3:
                    break
        
        return workflow


class StrategyExecutor:
    """
    Executes strategies to solve problems.
    
    Manages the execution of individual strategies or workflows of strategies.
    """
    
    def __init__(self, registry: StrategyRegistry):
        """
        Initialize with strategy registry.
        
        Args:
            registry: StrategyRegistry instance
        """
        self.registry = registry
    
    async def execute(self, 
                    strategy_id_or_workflow: Union[str, List[str]], 
                    data: Any, 
                    context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a strategy or workflow.
        
        Args:
            strategy_id_or_workflow: Strategy ID or list of strategy IDs
            data: Input data
            context: Execution context
            
        Returns:
            Execution result
            
        Raises:
            ValueError: If strategy not found or execution fails
        """
        if isinstance(strategy_id_or_workflow, list):
            # Execute workflow
            return await self._execute_workflow(strategy_id_or_workflow, data, context)
        else:
            # Execute single strategy
            return await self._execute_strategy(strategy_id_or_workflow, data, context)
    
    async def _execute_strategy(self, 
                              strategy_id: str, 
                              data: Any, 
                              context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single strategy.
        
        Args:
            strategy_id: Strategy ID
            data: Input data
            context: Execution context
            
        Returns:
            Execution result
            
        Raises:
            ValueError: If strategy not found or execution fails
        """
        try:
            # Get strategy
            strategy = self.registry.get_strategy(strategy_id)
            
            # Validate input
            if not strategy.validate_input(data):
                raise ValueError(f"Invalid input for strategy {strategy_id}")
            
            # Execute strategy
            start_time = time.time()
            result = strategy.process(data, context)
            end_time = time.time()
            
            # Return result with metadata
            return {
                "result": result,
                "metadata": {
                    "strategy_id": strategy_id,
                    "execution_time": end_time - start_time
                }
            }
        
        except Exception as e:
            # Handle strategy execution failure
            raise ValueError(f"Strategy execution failed: {e}")
    
    async def _execute_workflow(self, 
                              workflow: List[str], 
                              data: Any, 
                              context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow of strategies.
        
        Args:
            workflow: List of strategy IDs
            data: Input data
            context: Execution context
            
        Returns:
            Execution result
            
        Raises:
            ValueError: If any strategy not found or execution fails
        """
        current_data = data
        results = []
        
        # Execute strategies in sequence, passing output to next strategy
        for strategy_id in workflow:
            try:
                # Execute strategy
                result = await self._execute_strategy(strategy_id, current_data, context)
                
                # Update data for next strategy
                current_data = result["result"]
                
                # Record result
                results.append(result)
            
            except ValueError as e:
                # Handle strategy failure
                # If this is not the first strategy, we can still return partial results
                if results:
                    return {
                        "result": current_data,
                        "metadata": {
                            "workflow": workflow,
                            "completed_strategies": [r["metadata"]["strategy_id"] for r in results],
                            "error": str(e),
                            "partial": True
                        }
                    }
                else:
                    # No successful results yet, re-raise
                    raise
        
        # Return final result with workflow metadata
        return {
            "result": current_data,
            "metadata": {
                "workflow": workflow,
                "completed_strategies": [r["metadata"]["strategy_id"] for r in results],
                "partial": False
            }
        }


class TieredProblemSolver:
    """
    Main entry point for the tiered problem-solving framework.
    
    Coordinates problem analysis, strategy selection, and execution.
    """
    
    def __init__(self, 
                registry: StrategyRegistry,
                analyzer: ProblemAnalyzer,
                selector: StrategySelector,
                executor: StrategyExecutor):
        """
        Initialize with required components.
        
        Args:
            registry: StrategyRegistry instance
            analyzer: ProblemAnalyzer instance
            selector: StrategySelector instance
            executor: StrategyExecutor instance
        """
        self.registry = registry
        self.analyzer = analyzer
        self.selector = selector
        self.executor = executor
    
    async def solve(self, 
                  task: Task, 
                  historical_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Solve a problem represented by a task.
        
        Args:
            task: Task representing the problem
            historical_data: Optional historical performance data
            
        Returns:
            Solution result
            
        Raises:
            ValueError: If problem cannot be solved
        """
        # Analyze problem
        profile = self.analyzer.analyze_problem(task)
        
        # Select strategy
        strategy_id_or_workflow = self.selector.select_strategy(profile, historical_data)
        
        # Execute strategy
        context = {
            "task_id": task.task_id,
            "problem_profile": profile.to_dict()
        }
        
        return await self.executor.execute(strategy_id_or_workflow, task.input_data, context)
