"""
LLM Client abstraction layer for supporting multiple LLM providers.
Supports OpenAI and Azure OpenAI with a unified interface.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from loguru import logger

from .config import get_settings


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        response_format: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> str:
        """
        Send a chat completion request and return the response content.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (optional, uses default from config)
            temperature: Temperature for generation (optional)
            response_format: Response format specification (e.g., {"type": "json_object"})
            
        Returns:
            Response content as string
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM client is properly configured and available"""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API client implementation"""
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.default_model = settings.llm_model
        self.default_temperature = settings.llm_temperature
        self._client = None
        
        if self.api_key:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
            logger.info("OpenAI client initialized successfully")
        else:
            logger.warning("OpenAI API key not configured (set OPENAI_API_KEY environment variable)")
    
    def is_available(self) -> bool:
        return self._client is not None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        response_format: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> str:
        if not self.is_available():
            raise RuntimeError("OpenAI client is not available")
        
        use_model = model or self.default_model
        
        params = {
            "model": use_model,
            "messages": messages,
        }
        
        # GPT-5 models don't support temperature parameter
        if not use_model.startswith("gpt-5"):
            params["temperature"] = temperature if temperature is not None else self.default_temperature
        
        if response_format:
            params["response_format"] = response_format
        
        response = await self._client.chat.completions.create(**params)
        return response.choices[0].message.content


class AzureOpenAIClient(BaseLLMClient):
    """Azure OpenAI API client implementation"""
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.azure_openai_api_key
        self.endpoint = settings.azure_openai_endpoint
        self.deployment = settings.azure_openai_deployment
        self.api_version = settings.azure_openai_api_version
        self.default_model = settings.llm_model  # Used as fallback
        self.default_temperature = settings.llm_temperature
        self._client = None
        
        if all([self.api_key, self.endpoint, self.deployment]):
            from openai import AsyncAzureOpenAI
            self._client = AsyncAzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint
            )
            logger.info(f"Azure OpenAI client initialized successfully (deployment: {self.deployment})")
        else:
            missing = []
            if not self.api_key:
                missing.append("AZURE_OPENAI_API_KEY")
            if not self.endpoint:
                missing.append("AZURE_OPENAI_ENDPOINT")
            if not self.deployment:
                missing.append("AZURE_OPENAI_DEPLOYMENT")
            logger.warning(f"Azure OpenAI not configured. Missing: {', '.join(missing)}")
    
    def is_available(self) -> bool:
        return self._client is not None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        response_format: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> str:
        if not self.is_available():
            raise RuntimeError("Azure OpenAI client is not available")
        
        params = {
            "model": self.deployment,  # Azure uses deployment name as model
            "messages": messages,
        }
        
        # GPT-5 models don't support temperature parameter
        if not self.deployment.startswith("gpt-5"):
            params["temperature"] = temperature if temperature is not None else self.default_temperature
        
        if response_format:
            params["response_format"] = response_format
        
        response = await self._client.chat.completions.create(**params)
        return response.choices[0].message.content


class ClaudeClient(BaseLLMClient):
    """
    Anthropic Claude API client implementation.
    
    Supported models (as of 2025):
    - claude-sonnet-4-20250514 (latest, recommended)
    - claude-3-5-sonnet-20241022
    - claude-3-opus-20240229
    """
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.anthropic_api_key
        self.default_model = settings.claude_model
        self.default_temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self._client = None
        
        if self.api_key:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.api_key)
                logger.info(f"Claude client initialized successfully (model: {self.default_model})")
            except ImportError:
                logger.warning("Anthropic package not installed. Run: pip install anthropic")
        else:
            logger.warning("Anthropic API key not configured (set ANTHROPIC_API_KEY environment variable)")
    
    def is_available(self) -> bool:
        return self._client is not None
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> tuple:
        """
        Convert OpenAI message format to Claude format.
        Claude expects system message separately and uses 'user'/'assistant' roles.
        """
        system_message = None
        converted = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_message = content
            elif role in ("user", "assistant"):
                converted.append({"role": role, "content": content})
            else:
                # Convert unknown roles to user
                converted.append({"role": "user", "content": content})
        
        return system_message, converted
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        response_format: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> str:
        if not self.is_available():
            raise RuntimeError("Claude client is not available")
        
        use_model = model or self.default_model
        system_message, converted_messages = self._convert_messages(messages)
        
        params = {
            "model": use_model,
            "max_tokens": self.max_tokens,
            "messages": converted_messages,
        }
        
        if system_message:
            params["system"] = system_message
        
        if temperature is not None:
            params["temperature"] = temperature
        else:
            params["temperature"] = self.default_temperature
        
        response = await self._client.messages.create(**params)
        return response.content[0].text


class GeminiClient(BaseLLMClient):
    """
    Google Gemini API client implementation.
    
    Supported models (as of 2025):
    - gemini-2.5-flash (latest, recommended)
    - gemini-2.0-flash
    - gemini-1.5-pro
    
    Note: Uses google-generativeai package. For the new google.genai SDK,
    consider migrating to google-genai package in future versions.
    """
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.google_api_key
        self.default_model = settings.gemini_model
        self.default_temperature = settings.llm_temperature
        self._model = None
        
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._model = genai.GenerativeModel(self.default_model)
                logger.info(f"Gemini client initialized successfully (model: {self.default_model})")
            except ImportError:
                logger.warning("Google Generative AI package not installed. Run: pip install google-generativeai")
        else:
            logger.warning("Google API key not configured (set GOOGLE_API_KEY environment variable)")
    
    def is_available(self) -> bool:
        return self._model is not None
    
    def _convert_to_gemini_format(self, messages: List[Dict[str, str]]) -> tuple:
        """
        Convert OpenAI message format to Gemini format.
        Returns (history, last_message) where history is for chat context.
        """
        history = []
        system_instruction = None
        
        for msg in messages[:-1]:  # All except last
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_instruction = content
            elif role == "user":
                history.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                history.append({"role": "model", "parts": [content]})
        
        last_message = messages[-1]["content"] if messages else ""
        return history, last_message, system_instruction
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        response_format: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> str:
        if not self.is_available():
            raise RuntimeError("Gemini client is not available")
        
        import google.generativeai as genai
        
        history, last_message, system_instruction = self._convert_to_gemini_format(messages)
        
        # Use different model if specified
        if model and model != self.default_model:
            model_instance = genai.GenerativeModel(model)
        else:
            model_instance = self._model
        
        # Configure generation
        generation_config = genai.types.GenerationConfig(
            temperature=temperature if temperature is not None else self.default_temperature,
        )
        
        # Start chat with history
        chat = model_instance.start_chat(history=history)
        
        # Send message
        response = await chat.send_message_async(
            last_message,
            generation_config=generation_config
        )
        
        return response.text


class LLMClientFactory:
    """Factory class to create the appropriate LLM client based on configuration"""
    
    _instance: Optional[BaseLLMClient] = None
    
    # Supported providers and their client classes
    _providers = {
        "openai": OpenAIClient,
        "azure": AzureOpenAIClient,
        "claude": ClaudeClient,
        "gemini": GeminiClient,
    }
    
    @classmethod
    def get_client(cls, provider: Optional[str] = None) -> Optional[BaseLLMClient]:
        """
        Get or create the LLM client based on configuration.
        
        Args:
            provider: Override the configured provider (optional)
        
        Returns:
            LLM client instance or None if not configured
        """
        settings = get_settings()
        use_provider = (provider or settings.llm_provider).lower()
        
        # If requesting a different provider than cached, create new
        if provider and cls._instance is not None:
            # Check if current instance matches requested provider
            current_type = type(cls._instance).__name__.lower()
            if use_provider not in current_type:
                logger.info(f"Switching LLM provider to: {use_provider}")
                cls._instance = None
        
        if cls._instance is not None:
            return cls._instance
        
        logger.info(f"Initializing LLM client with provider: {use_provider}")
        
        # Try the specified provider
        if use_provider in cls._providers:
            client_class = cls._providers[use_provider]
            client = client_class()
            if client.is_available():
                cls._instance = client
                logger.info(f"Using {use_provider.upper()} as LLM provider")
                return cls._instance
            else:
                logger.warning(f"{use_provider.upper()} configured but not available")
        else:
            logger.warning(f"Unknown provider: {use_provider}")
        
        # Fallback: try other providers in order
        fallback_order = ["openai", "azure", "claude", "gemini"]
        for fallback_provider in fallback_order:
            if fallback_provider == use_provider:
                continue
            
            client_class = cls._providers[fallback_provider]
            client = client_class()
            if client.is_available():
                cls._instance = client
                logger.info(f"Falling back to {fallback_provider.upper()} as LLM provider")
                return cls._instance
        
        logger.warning("No LLM provider is available")
        return None
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """
        Get list of available (configured) providers.
        
        Returns:
            List of available provider names
        """
        available = []
        for name, client_class in cls._providers.items():
            try:
                client = client_class()
                if client.is_available():
                    available.append(name)
            except Exception:
                pass
        return available
    
    @classmethod
    def reset(cls):
        """Reset the singleton instance (useful for testing)"""
        cls._instance = None


def get_llm_client() -> Optional[BaseLLMClient]:
    """
    Convenience function to get the configured LLM client.
    
    Returns:
        LLM client instance or None if not configured
    """
    return LLMClientFactory.get_client()




