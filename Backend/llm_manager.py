import os
from typing import Optional, Dict, Any
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import BaseLanguageModel
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    GPT_4O = "gpt-4o"
    CLAUDE_35_SONNET = "claude-3-5-sonnet-20241022"
    GEMINI_2_FLASH = "gemini-2.0-flash-exp"
    DEEPSEEK_R1 = "deepseek-r1"

class LLMManager:
    """Manages multiple LLM providers with a unified interface."""
    
    def __init__(self):
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available LLM providers based on available API keys."""
        
        # OpenAI GPT-4o
        if os.getenv("OPENAI_API_KEY"):
            try:
                self.providers[LLMProvider.GPT_4O] = ChatOpenAI(
                    model="gpt-4o",
                    temperature=0.7,
                    max_tokens=4000,
                    openai_api_key=os.getenv("OPENAI_API_KEY")
                )
                logger.info("GPT-4o initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize GPT-4o: {e}")
        
        # Anthropic Claude 3.5 Sonnet
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                self.providers[LLMProvider.CLAUDE_35_SONNET] = ChatAnthropic(
                    model="claude-3-5-sonnet-20241022",
                    temperature=0.7,
                    max_tokens=4000,
                    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
                )
                logger.info("Claude 3.5 Sonnet initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Claude 3.5: {e}")
        
        # Google Gemini 2.0 Flash
        if os.getenv("GOOGLE_API_KEY"):
            try:
                self.providers[LLMProvider.GEMINI_2_FLASH] = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash-exp",
                    temperature=0.7,
                    max_output_tokens=4000,
                    google_api_key=os.getenv("GOOGLE_API_KEY")
                )
                logger.info("Gemini 2.0 Flash initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini 2.0: {e}")
        
        # DeepSeek R1 (using OpenAI-compatible API)
        if os.getenv("DEEPSEEK_API_KEY"):
            try:
                self.providers[LLMProvider.DEEPSEEK_R1] = ChatOpenAI(
                    model="DeepSeek-R1",
                    temperature=0.7,
                    max_tokens=4000,
                    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
                    openai_api_base="https://api.deepseek.com"
                )
                logger.info("DeepSeek R1 initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize DeepSeek R1: {e}")
    
    def get_llm(self, provider: LLMProvider) -> Optional[BaseLanguageModel]:
        """Get an LLM instance for the specified provider."""
        return self.providers.get(provider)
    
    def get_available_providers(self) -> Dict[str, str]:
        """Get a list of available LLM providers."""
        available = {}
        for provider in self.providers.keys():
            available[provider.value] = self._get_provider_display_name(provider)
        return available
    
    def _get_provider_display_name(self, provider: LLMProvider) -> str:
        """Get a user-friendly display name for the provider."""
        display_names = {
            LLMProvider.GPT_4O: "GPT-4o (OpenAI)",
            LLMProvider.CLAUDE_35_SONNET: "Claude 3.5 Sonnet (Anthropic)",
            LLMProvider.GEMINI_2_FLASH: "Gemini 2.0 Flash (Google)",
            LLMProvider.DEEPSEEK_R1: "DeepSeek R1"
        }
        return display_names.get(provider, provider.value)
    
    def get_provider_by_name(self, provider_name: str) -> Optional[LLMProvider]:
        """Get LLMProvider enum by string name."""
        try:
            return LLMProvider(provider_name)
        except ValueError:
            return None
    
    def is_provider_available(self, provider: LLMProvider) -> bool:
        """Check if a provider is available."""
        return provider in self.providers 