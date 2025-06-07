"""
Model Provider Interface for Vertex Full-Stack System.

This module defines the core interfaces for model-agnostic operations,
allowing the system to work with any AI model provider.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from enum import Enum


class ModelCapability(Enum):
    """Enum representing different model capabilities."""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    CLASSIFICATION = "classification"
    QUESTION_ANSWERING = "question_answering"
    IMAGE_GENERATION = "image_generation"
    AUDIO_GENERATION = "audio_generation"
    MULTIMODAL = "multimodal"


class ModelRole(Enum):
    """Enum representing different roles a model can play in the system."""
    ORCHESTRATOR = "orchestrator"
    EXECUTOR = "executor"
    ANALYZER = "analyzer"
    GENERATOR = "generator"
    VALIDATOR = "validator"
    OPTIMIZER = "optimizer"


class ModelProvider(ABC):
    """
    Abstract base class for model providers.
    
    This interface must be implemented by all model providers to ensure
    model-agnostic operation throughout the system.
    """
    
    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about this provider.
        
        Returns:
            Dict containing provider metadata such as name, version, etc.
        """
        pass
    
    @abstractmethod
    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List all available models from this provider.
        
        Returns:
            List of dictionaries, each containing model metadata.
        """
        pass
    
    @abstractmethod
    def get_model_capabilities(self, model_id: str) -> List[ModelCapability]:
        """
        Get the capabilities of a specific model.
        
        Args:
            model_id: Identifier for the model
            
        Returns:
            List of ModelCapability enums representing the model's capabilities.
        """
        pass
    
    @abstractmethod
    def execute_prompt(self, 
                      model_id: str, 
                      prompt: str, 
                      parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a prompt using the specified model.
        
        Args:
            model_id: Identifier for the model to use
            prompt: The prompt text to send to the model
            parameters: Optional parameters for execution (temperature, etc.)
            
        Returns:
            Dictionary containing the model's response and metadata.
        """
        pass
    
    @abstractmethod
    def stream_prompt(self, 
                     model_id: str, 
                     prompt: str, 
                     parameters: Optional[Dict[str, Any]] = None) -> Any:
        """
        Stream a prompt execution using the specified model.
        
        Args:
            model_id: Identifier for the model to use
            prompt: The prompt text to send to the model
            parameters: Optional parameters for execution (temperature, etc.)
            
        Returns:
            An iterable that yields response chunks as they become available.
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, 
                     model_id: str, 
                     prompt: str, 
                     parameters: Optional[Dict[str, Any]] = None) -> float:
        """
        Estimate the cost of executing a prompt.
        
        Args:
            model_id: Identifier for the model to use
            prompt: The prompt text to send to the model
            parameters: Optional parameters for execution (temperature, etc.)
            
        Returns:
            Estimated cost in credits.
        """
        pass


class ProviderRegistry:
    """
    Registry for model providers.
    
    This class manages the registration and retrieval of model providers,
    allowing dynamic provider management.
    """
    
    def __init__(self):
        """Initialize an empty provider registry."""
        self._providers = {}
    
    def register_provider(self, provider_id: str, provider: ModelProvider) -> None:
        """
        Register a model provider.
        
        Args:
            provider_id: Unique identifier for the provider
            provider: ModelProvider instance
        """
        if provider_id in self._providers:
            raise ValueError(f"Provider with ID '{provider_id}' already registered")
        
        self._providers[provider_id] = provider
    
    def get_provider(self, provider_id: str) -> ModelProvider:
        """
        Get a registered provider by ID.
        
        Args:
            provider_id: Identifier for the provider
            
        Returns:
            ModelProvider instance
            
        Raises:
            KeyError: If no provider with the given ID is registered
        """
        if provider_id not in self._providers:
            raise KeyError(f"No provider registered with ID '{provider_id}'")
        
        return self._providers[provider_id]
    
    def list_providers(self) -> List[str]:
        """
        List all registered provider IDs.
        
        Returns:
            List of provider IDs
        """
        return list(self._providers.keys())
    
    def get_provider_for_capability(self, capability: ModelCapability) -> List[str]:
        """
        Find providers that offer models with a specific capability.
        
        Args:
            capability: The capability to search for
            
        Returns:
            List of provider IDs that offer the capability
        """
        matching_providers = []
        
        for provider_id, provider in self._providers.items():
            for model in provider.list_available_models():
                model_id = model.get('id')
                if capability in provider.get_model_capabilities(model_id):
                    matching_providers.append(provider_id)
                    break
        
        return matching_providers


class PromptTemplate:
    """
    Template for generating prompts adaptively based on model capabilities.
    
    This class handles the generation of prompts tailored to specific models,
    taking into account their capabilities and optimal prompting strategies.
    """
    
    def __init__(self, 
                template_id: str, 
                template_text: str,
                required_capabilities: List[ModelCapability],
                variants: Optional[Dict[str, str]] = None):
        """
        Initialize a prompt template.
        
        Args:
            template_id: Unique identifier for this template
            template_text: Base template text with placeholders
            required_capabilities: Capabilities required to use this template
            variants: Optional model-specific variants of the template
        """
        self.template_id = template_id
        self.template_text = template_text
        self.required_capabilities = required_capabilities
        self.variants = variants or {}
    
    def render(self, 
              model_id: str, 
              provider: ModelProvider, 
              parameters: Dict[str, Any]) -> str:
        """
        Render the template for a specific model.
        
        Args:
            model_id: ID of the model to render for
            provider: ModelProvider instance for the model
            parameters: Parameters to fill in the template
            
        Returns:
            Rendered prompt text
            
        Raises:
            ValueError: If the model lacks required capabilities
        """
        # Check if model has required capabilities
        model_capabilities = provider.get_model_capabilities(model_id)
        for required_capability in self.required_capabilities:
            if required_capability not in model_capabilities:
                raise ValueError(
                    f"Model {model_id} lacks required capability: {required_capability}"
                )
        
        # Use model-specific variant if available
        template = self.variants.get(model_id, self.template_text)
        
        # Fill in template with parameters
        for key, value in parameters.items():
            placeholder = f"{{{key}}}"
            template = template.replace(placeholder, str(value))
        
        return template


class ModelRoleManager:
    """
    Manager for assigning and tracking model roles.
    
    This class handles the assignment of roles to models based on their
    capabilities and historical performance.
    """
    
    def __init__(self, provider_registry: ProviderRegistry):
        """
        Initialize the role manager.
        
        Args:
            provider_registry: ProviderRegistry instance for accessing models
        """
        self.provider_registry = provider_registry
        self.role_assignments = {}
    
    def assign_role(self, 
                   role: ModelRole, 
                   provider_id: str, 
                   model_id: str) -> None:
        """
        Manually assign a role to a specific model.
        
        Args:
            role: The role to assign
            provider_id: ID of the provider
            model_id: ID of the model
        """
        if role not in self.role_assignments:
            self.role_assignments[role] = []
        
        self.role_assignments[role].append((provider_id, model_id))
    
    def get_models_for_role(self, role: ModelRole) -> List[Dict[str, str]]:
        """
        Get all models assigned to a specific role.
        
        Args:
            role: The role to query
            
        Returns:
            List of dictionaries with provider_id and model_id
        """
        if role not in self.role_assignments:
            return []
        
        return [
            {"provider_id": provider_id, "model_id": model_id}
            for provider_id, model_id in self.role_assignments[role]
        ]
    
    def auto_assign_roles(self) -> None:
        """
        Automatically assign roles based on model capabilities.
        
        This method analyzes all available models and assigns them to
        appropriate roles based on their capabilities.
        """
        # Reset current assignments
        self.role_assignments = {role: [] for role in ModelRole}
        
        # For each provider
        for provider_id in self.provider_registry.list_providers():
            provider = self.provider_registry.get_provider(provider_id)
            
            # For each model from this provider
            for model_info in provider.list_available_models():
                model_id = model_info.get('id')
                capabilities = provider.get_model_capabilities(model_id)
                
                # Assign roles based on capabilities
                if ModelCapability.CODE_GENERATION in capabilities:
                    self.assign_role(ModelRole.EXECUTOR, provider_id, model_id)
                
                if ModelCapability.SUMMARIZATION in capabilities:
                    self.assign_role(ModelRole.ANALYZER, provider_id, model_id)
                
                if ModelCapability.TEXT_GENERATION in capabilities:
                    self.assign_role(ModelRole.GENERATOR, provider_id, model_id)
                
                # Models with multiple capabilities can be orchestrators
                if len(capabilities) >= 3:
                    self.assign_role(ModelRole.ORCHESTRATOR, provider_id, model_id)
    
    def get_best_model_for_role(self, 
                               role: ModelRole, 
                               historical_data: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Get the best model for a specific role based on historical performance.
        
        Args:
            role: The role to find a model for
            historical_data: Optional historical performance data
            
        Returns:
            Dictionary with provider_id and model_id
            
        Raises:
            ValueError: If no models are available for the role
        """
        candidates = self.get_models_for_role(role)
        
        if not candidates:
            raise ValueError(f"No models available for role: {role}")
        
        if not historical_data:
            # Without historical data, just return the first candidate
            return candidates[0]
        
        # With historical data, rank candidates by performance
        # (Implementation would depend on the structure of historical_data)
        # For now, just return the first candidate
        return candidates[0]
