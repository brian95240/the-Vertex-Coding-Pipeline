"""
MCP Integration Layer for Vertex Full-Stack System.

This module implements the integration layer for Model Context Protocol (MCP)
servers, providing a unified interface for accessing external capabilities.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Type
import importlib
import time
import asyncio
import uuid
import json
import requests
from enum import Enum


class MCPCapability(Enum):
    """Enum representing different MCP server capabilities."""
    UI_GENERATION = "ui_generation"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    SEARCH = "search"
    TASK_MANAGEMENT = "task_management"


class MCPServer(ABC):
    """
    Abstract base class for MCP server integrations.
    
    This interface must be implemented by all MCP server integrations to ensure
    consistent access patterns.
    """
    
    @abstractmethod
    def get_server_info(self) -> Dict[str, Any]:
        """
        Get information about this MCP server.
        
        Returns:
            Dict containing server metadata such as name, version, capabilities, etc.
        """
        pass
    
    @abstractmethod
    def list_available_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools from this MCP server.
        
        Returns:
            List of dictionaries, each containing tool metadata.
        """
        pass
    
    @abstractmethod
    def execute_tool(self, 
                    tool_id: str, 
                    parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool using the specified parameters.
        
        Args:
            tool_id: Identifier for the tool to use
            parameters: Parameters for tool execution
            
        Returns:
            Dictionary containing the tool's response and metadata.
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, 
                     tool_id: str, 
                     parameters: Dict[str, Any]) -> float:
        """
        Estimate the cost of executing a tool.
        
        Args:
            tool_id: Identifier for the tool to use
            parameters: Parameters for tool execution
            
        Returns:
            Estimated cost in credits.
        """
        pass


class MCPServerRegistry:
    """
    Registry for MCP servers.
    
    This class manages the registration and retrieval of MCP servers,
    allowing dynamic server management.
    """
    
    def __init__(self):
        """Initialize an empty server registry."""
        self._servers = {}
        self._server_metadata = {}
    
    def register_server(self, 
                       server_id: str, 
                       server_metadata: Dict[str, Any],
                       server_module_path: str,
                       server_class_name: str) -> None:
        """
        Register an MCP server.
        
        Args:
            server_id: Unique identifier for the server
            server_metadata: Metadata for the server
            server_module_path: Import path to the module containing the server
            server_class_name: Name of the server class
            
        Raises:
            ValueError: If server with same ID already registered
        """
        if server_id in self._server_metadata:
            raise ValueError(f"Server with ID '{server_id}' already registered")
        
        # Store metadata for lazy loading
        self._server_metadata[server_id] = {
            "metadata": server_metadata,
            "module_path": server_module_path,
            "class_name": server_class_name
        }
    
    def get_server(self, server_id: str) -> MCPServer:
        """
        Get a registered server by ID.
        
        Args:
            server_id: Identifier for the server
            
        Returns:
            MCPServer instance
            
        Raises:
            KeyError: If no server with the given ID is registered
            ImportError: If server module cannot be imported
            AttributeError: If server class cannot be found in module
        """
        if server_id not in self._server_metadata:
            raise KeyError(f"No server registered with ID '{server_id}'")
        
        # Lazy loading of server
        if server_id not in self._servers:
            metadata = self._server_metadata[server_id]
            
            try:
                module = importlib.import_module(metadata["module_path"])
                server_class = getattr(module, metadata["class_name"])
                self._servers[server_id] = server_class()
            except (ImportError, AttributeError) as e:
                raise ValueError(f"Failed to load server {server_id}: {e}")
        
        return self._servers[server_id]
    
    def list_servers(self) -> List[str]:
        """
        List all registered server IDs.
        
        Returns:
            List of server IDs
        """
        return list(self._server_metadata.keys())
    
    def get_server_metadata(self, server_id: str) -> Dict[str, Any]:
        """
        Get metadata for a server.
        
        Args:
            server_id: Identifier for the server
            
        Returns:
            Dictionary containing server metadata
            
        Raises:
            KeyError: If no server with the given ID is registered
        """
        if server_id not in self._server_metadata:
            raise KeyError(f"No server registered with ID '{server_id}'")
        
        return self._server_metadata[server_id]["metadata"]
    
    def get_servers_for_capability(self, capability: MCPCapability) -> List[str]:
        """
        Find servers that offer a specific capability.
        
        Args:
            capability: The capability to search for
            
        Returns:
            List of server IDs that offer the capability
        """
        matching_servers = []
        
        for server_id, metadata in self._server_metadata.items():
            server_capabilities = metadata["metadata"].get("capabilities", [])
            if capability.value in server_capabilities:
                matching_servers.append(server_id)
        
        return matching_servers


class MCPToolExecutor:
    """
    Executes tools from MCP servers.
    
    This class handles the execution of tools, including error handling,
    retries, and credit tracking.
    """
    
    def __init__(self, 
                registry: MCPServerRegistry,
                credit_tracker: Any):  # Use Any to avoid circular dependency
        """
        Initialize with server registry and credit tracker.
        
        Args:
            registry: MCPServerRegistry instance
            credit_tracker: Component for tracking credit usage
        """
        self.registry = registry
        self.credit_tracker = credit_tracker
        self.execution_history = []
    
    async def execute_tool(self, 
                         server_id: str,
                         tool_id: str,
                         parameters: Dict[str, Any],
                         component_id: str,
                         max_retries: int = 3) -> Dict[str, Any]:
        """
        Execute a tool from an MCP server.
        
        Args:
            server_id: ID of the MCP server
            tool_id: ID of the tool to execute
            parameters: Parameters for tool execution
            component_id: ID of the component requesting execution
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary containing tool response and metadata
            
        Raises:
            ValueError: If server or tool not found
            RuntimeError: If execution fails after retries
        """
        # Get server
        try:
            server = self.registry.get_server(server_id)
        except (KeyError, ValueError) as e:
            raise ValueError(f"Failed to get server {server_id}: {e}")
        
        # Estimate cost
        try:
            estimated_cost = server.estimate_cost(tool_id, parameters)
        except Exception as e:
            # If cost estimation fails, use a default
            estimated_cost = 1.0
        
        # Check credit allocation
        if hasattr(self.credit_tracker, "get_allocation"):
            if self.credit_tracker.get_allocation(component_id) < estimated_cost:
                raise ValueError(f"Insufficient credits for tool execution: {estimated_cost} required")
        
        # Execute with retries
        retry_count = 0
        last_error = None
        
        while retry_count <= max_retries:
            try:
                start_time = time.time()
                result = server.execute_tool(tool_id, parameters)
                end_time = time.time()
                
                # Record execution
                execution_record = {
                    "timestamp": time.time(),
                    "server_id": server_id,
                    "tool_id": tool_id,
                    "parameters": parameters,
                    "component_id": component_id,
                    "execution_time": end_time - start_time,
                    "estimated_cost": estimated_cost,
                    "success": True
                }
                
                self.execution_history.append(execution_record)
                
                # Track credit usage
                if hasattr(self.credit_tracker, "use_credits"):
                    self.credit_tracker.use_credits(component_id, estimated_cost)
                
                # Return result with metadata
                return {
                    "result": result,
                    "metadata": {
                        "server_id": server_id,
                        "tool_id": tool_id,
                        "execution_time": end_time - start_time,
                        "estimated_cost": estimated_cost
                    }
                }
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                # Record failed execution
                execution_record = {
                    "timestamp": time.time(),
                    "server_id": server_id,
                    "tool_id": tool_id,
                    "parameters": parameters,
                    "component_id": component_id,
                    "error": str(e),
                    "retry_count": retry_count,
                    "success": False
                }
                
                self.execution_history.append(execution_record)
                
                # Wait before retry (exponential backoff)
                if retry_count <= max_retries:
                    await asyncio.sleep(2 ** retry_count)
        
        # All retries failed
        raise RuntimeError(f"Tool execution failed after {max_retries} retries: {last_error}")
    
    def get_execution_history(self, 
                            server_id: Optional[str] = None,
                            tool_id: Optional[str] = None,
                            component_id: Optional[str] = None,
                            success_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get execution history, optionally filtered.
        
        Args:
            server_id: Optional server ID filter
            tool_id: Optional tool ID filter
            component_id: Optional component ID filter
            success_only: If True, only return successful executions
            
        Returns:
            List of execution records
        """
        filtered_history = self.execution_history
        
        if server_id is not None:
            filtered_history = [
                record for record in filtered_history
                if record.get("server_id") == server_id
            ]
            
        if tool_id is not None:
            filtered_history = [
                record for record in filtered_history
                if record.get("tool_id") == tool_id
            ]
            
        if component_id is not None:
            filtered_history = [
                record for record in filtered_history
                if record.get("component_id") == component_id
            ]
            
        if success_only:
            filtered_history = [
                record for record in filtered_history
                if record.get("success", False)
            ]
            
        return filtered_history


class MCPToolSelector:
    """
    Selects appropriate MCP tools based on requirements.
    
    This class helps choose the right MCP server and tool for a given task.
    """
    
    def __init__(self, registry: MCPServerRegistry):
        """
        Initialize with server registry.
        
        Args:
            registry: MCPServerRegistry instance
        """
        self.registry = registry
    
    def select_tool(self, 
                   capability: MCPCapability,
                   requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select the most appropriate tool for a capability.
        
        Args:
            capability: Required capability
            requirements: Additional requirements
            
        Returns:
            Dictionary with server_id, tool_id, and metadata
            
        Raises:
            ValueError: If no suitable tool found
        """
        # Find servers with the capability
        server_ids = self.registry.get_servers_for_capability(capability)
        
        if not server_ids:
            raise ValueError(f"No servers found with capability: {capability}")
        
        # Find tools from each server
        candidate_tools = []
        
        for server_id in server_ids:
            try:
                server = self.registry.get_server(server_id)
                tools = server.list_available_tools()
                
                for tool in tools:
                    tool_capabilities = tool.get("capabilities", [])
                    
                    if capability.value in tool_capabilities:
                        # Check if tool meets additional requirements
                        if self._tool_meets_requirements(tool, requirements):
                            candidate_tools.append({
                                "server_id": server_id,
                                "tool_id": tool["id"],
                                "metadata": tool
                            })
            except Exception as e:
                # Skip servers that fail to load or list tools
                continue
        
        if not candidate_tools:
            raise ValueError(f"No suitable tools found for capability: {capability}")
        
        # Rank tools by suitability
        ranked_tools = self._rank_tools(candidate_tools, requirements)
        
        # Return the top-ranked tool
        return ranked_tools[0]
    
    def _tool_meets_requirements(self, 
                               tool: Dict[str, Any],
                               requirements: Dict[str, Any]) -> bool:
        """
        Check if a tool meets additional requirements.
        
        Args:
            tool: Tool metadata
            requirements: Additional requirements
            
        Returns:
            True if tool meets requirements, False otherwise
        """
        # Check required features
        if "required_features" in requirements:
            tool_features = tool.get("features", [])
            for feature in requirements["required_features"]:
                if feature not in tool_features:
                    return False
        
        # Check input schema compatibility
        if "input_schema" in requirements:
            tool_schema = tool.get("input_schema", {})
            req_schema = requirements["input_schema"]
            
            # Simple schema compatibility check
            for key, value_type in req_schema.items():
                if key not in tool_schema:
                    return False
                
                tool_type = tool_schema[key]
                if tool_type != value_type:
                    return False
        
        return True
    
    def _rank_tools(self, 
                   candidates: List[Dict[str, Any]],
                   requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rank candidate tools by suitability.
        
        Args:
            candidates: List of candidate tools
            requirements: Additional requirements
            
        Returns:
            List of tools, sorted by rank (best first)
        """
        # Simple ranking based on feature count
        for candidate in candidates:
            tool = candidate["metadata"]
            
            # Count matching features
            tool_features = tool.get("features", [])
            preferred_features = requirements.get("preferred_features", [])
            
            matching_features = sum(1 for f in preferred_features if f in tool_features)
            
            # Store score in candidate
            candidate["score"] = matching_features
        
        # Sort by score (descending)
        return sorted(candidates, key=lambda c: c.get("score", 0), reverse=True)


class MCPIntegrationLayer:
    """
    Main entry point for the MCP integration layer.
    
    Coordinates server registration, tool selection, and execution.
    """
    
    def __init__(self, 
                registry: MCPServerRegistry,
                executor: MCPToolExecutor,
                selector: MCPToolSelector):
        """
        Initialize with required components.
        
        Args:
            registry: MCPServerRegistry instance
            executor: MCPToolExecutor instance
            selector: MCPToolSelector instance
        """
        self.registry = registry
        self.executor = executor
        self.selector = selector
    
    def register_server(self, 
                       server_id: str, 
                       server_metadata: Dict[str, Any],
                       server_module_path: str,
                       server_class_name: str) -> None:
        """
        Register an MCP server.
        
        Args:
            server_id: Unique identifier for the server
            server_metadata: Metadata for the server
            server_module_path: Import path to the module containing the server
            server_class_name: Name of the server class
            
        Raises:
            ValueError: If server with same ID already registered
        """
        self.registry.register_server(
            server_id, server_metadata, server_module_path, server_class_name)
    
    async def execute_capability(self, 
                               capability: MCPCapability,
                               parameters: Dict[str, Any],
                               requirements: Dict[str, Any],
                               component_id: str) -> Dict[str, Any]:
        """
        Execute a capability using the most appropriate tool.
        
        Args:
            capability: Required capability
            parameters: Parameters for tool execution
            requirements: Additional requirements for tool selection
            component_id: ID of the component requesting execution
            
        Returns:
            Dictionary containing tool response and metadata
            
        Raises:
            ValueError: If no suitable tool found
            RuntimeError: If execution fails
        """
        # Select tool
        tool_info = self.selector.select_tool(capability, requirements)
        
        # Execute tool
        return await self.executor.execute_tool(
            tool_info["server_id"],
            tool_info["tool_id"],
            parameters,
            component_id
        )
    
    async def execute_specific_tool(self, 
                                  server_id: str,
                                  tool_id: str,
                                  parameters: Dict[str, Any],
                                  component_id: str) -> Dict[str, Any]:
        """
        Execute a specific tool from a specific server.
        
        Args:
            server_id: ID of the MCP server
            tool_id: ID of the tool to execute
            parameters: Parameters for tool execution
            component_id: ID of the component requesting execution
            
        Returns:
            Dictionary containing tool response and metadata
            
        Raises:
            ValueError: If server or tool not found
            RuntimeError: If execution fails
        """
        return await self.executor.execute_tool(
            server_id, tool_id, parameters, component_id)
    
    def get_execution_history(self, 
                            server_id: Optional[str] = None,
                            tool_id: Optional[str] = None,
                            component_id: Optional[str] = None,
                            success_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get execution history, optionally filtered.
        
        Args:
            server_id: Optional server ID filter
            tool_id: Optional tool ID filter
            component_id: Optional component ID filter
            success_only: If True, only return successful executions
            
        Returns:
            List of execution records
        """
        return self.executor.get_execution_history(
            server_id, tool_id, component_id, success_only)
    
    def list_capabilities(self) -> Dict[MCPCapability, List[str]]:
        """
        List all available capabilities and the servers that provide them.
        
        Returns:
            Dictionary mapping capabilities to lists of server IDs
        """
        capabilities = {}
        
        for capability in MCPCapability:
            server_ids = self.registry.get_servers_for_capability(capability)
            capabilities[capability] = server_ids
            
        return capabilities
