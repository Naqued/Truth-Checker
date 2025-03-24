"""Factory for creating and configuring service instances."""

import os
import logging
from typing import Optional, Dict, Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

from truth_checker.domain.ports import ClaimDetectionService, FactCheckingService, KnowledgeRepository
from truth_checker.application.claim_detection_service import LangChainClaimDetectionService
from truth_checker.application.fact_checking_service import LangGraphFactCheckingService
from truth_checker.application.knowledge_repository import ChromaKnowledgeRepository

logger = logging.getLogger(__name__)

# LLM provider options
LLM_PROVIDER_ANTHROPIC = "anthropic"
LLM_PROVIDER_OPENAI = "openai"
LLM_PROVIDER_MOCK = "mock"


class MockChatModel(BaseChatModel):
    """Mock chat model for testing without API keys."""
    
    model_name: str = "mock-llm"
    temperature: float = 0.0
    
    def _call(self, messages, **kwargs):
        """Return a mock response."""
        return AIMessage(content=self._get_mock_response(messages))
    
    def _generate(self, messages, **kwargs):
        """Generate mock chat completions."""
        from langchain_core.outputs import ChatGeneration, ChatResult
        
        message = AIMessage(content=self._get_mock_response(messages))
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])
    
    async def _agenerate(self, messages, **kwargs):
        """Generate mock chat completions."""
        from langchain_core.outputs import ChatGeneration, ChatResult
        
        message = AIMessage(content=self._get_mock_response(messages))
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])
    
    def _get_mock_response(self, messages: list[BaseMessage]) -> str:
        """Get a mock response based on the input."""
        last_message = messages[-1].content
        
        # For claim detection
        if "identify factual claims" in last_message or "factual claims" in last_message or "Transcript:" in last_message:
            return """
            [
                {
                    "text": "The Earth is 4.54 billion years old",
                    "confidence": 0.95,
                    "context": "Statement about Earth's age"
                },
                {
                    "text": "Water boils at exactly 100 degrees Celsius at all elevations",
                    "confidence": 0.98,
                    "context": "Statement about water boiling point"
                },
                {
                    "text": "Climate change is primarily caused by natural cycles rather than human activities",
                    "confidence": 0.9,
                    "context": "Statement about climate change causes"
                },
                {
                    "text": "The speed of light in a vacuum is 299,792,458 meters per second",
                    "confidence": 0.99,
                    "context": "Statement about light speed"
                },
                {
                    "text": "The tallest mountain in the world is K2",
                    "confidence": 0.97,
                    "context": "Statement about tallest mountain"
                },
                {
                    "text": "Vaccines cause autism",
                    "confidence": 0.92,
                    "context": "Statement about vaccines and autism"
                }
            ]
            """
        
        # For query construction
        elif "search queries" in last_message or "CLAIM TO VERIFY:" in last_message:
            query = ""
            if "Earth is 4.54 billion" in last_message:
                query = "Earth age scientific consensus"
            elif "boils at" in last_message:
                query = "water boiling point elevation"
            elif "climate change" in last_message:
                query = "climate change human vs natural causes"
            elif "speed of light" in last_message:
                query = "speed of light vacuum"
            elif "tallest mountain" in last_message:
                query = "tallest mountain world Everest K2"
            elif "vaccines" in last_message and "autism" in last_message:
                query = "vaccines autism connection study"
            else:
                query = "factual information"
                
            return """
            {
                "queries": [
                    "%s",
                    "scientific evidence related to the claim",
                    "expert consensus on the subject"
                ]
            }
            """ % query
        
        # For evidence analysis
        elif "analyze this evidence" in last_message or "EVIDENCE:" in last_message:
            if "Earth is 4.54 billion" in last_message:
                return """
                {
                    "verdict": "SUPPORTED",
                    "confidence": 0.95,
                    "key_evidence": "Multiple scientific studies using radiometric dating have consistently shown the Earth to be approximately 4.54 billion years old.",
                    "needs_more_evidence": false
                }
                """
            elif "boils at" in last_message and ("all elevations" in last_message or "elevation" in last_message):
                return """
                {
                    "verdict": "CONTRADICTED",
                    "confidence": 0.98,
                    "key_evidence": "Scientific evidence clearly shows that water boils at different temperatures depending on atmospheric pressure, which varies with elevation.",
                    "needs_more_evidence": false
                }
                """
            elif "climate change" in last_message and "natural cycles" in last_message:
                return """
                {
                    "verdict": "CONTRADICTED",
                    "confidence": 0.97,
                    "key_evidence": "The IPCC and scientific consensus indicate that current climate change is primarily caused by human activities, particularly greenhouse gas emissions.",
                    "needs_more_evidence": false
                }
                """
            elif "speed of light" in last_message:
                return """
                {
                    "verdict": "SUPPORTED",
                    "confidence": 0.99,
                    "key_evidence": "The defined speed of light in a vacuum is exactly 299,792,458 meters per second according to the International System of Units.",
                    "needs_more_evidence": false
                }
                """
            elif "tallest mountain" in last_message and "K2" in last_message:
                return """
                {
                    "verdict": "CONTRADICTED",
                    "confidence": 0.98,
                    "key_evidence": "Mount Everest is recognized as the tallest mountain in the world at 8,849 meters, while K2 is the second-tallest at 8,611 meters.",
                    "needs_more_evidence": false
                }
                """
            elif "vaccines" in last_message and "autism" in last_message:
                return """
                {
                    "verdict": "CONTRADICTED",
                    "confidence": 0.99,
                    "key_evidence": "Numerous large-scale studies have found no link between vaccines and autism. The original study suggesting this link was retracted due to methodological flaws and ethical concerns.",
                    "needs_more_evidence": false
                }
                """
            else:
                return """
                {
                    "verdict": "INSUFFICIENT_EVIDENCE",
                    "confidence": 0.5,
                    "key_evidence": "The available evidence does not clearly support or contradict the claim.",
                    "needs_more_evidence": true,
                    "missing_information": "More specific scientific studies on this topic would be helpful."
                }
                """
        
        # For final verdict
        elif "final verdict" in last_message or "EVIDENCE ANALYSIS" in last_message:
            if "Earth is 4.54 billion" in last_message:
                return """
                {
                    "verdict": "TRUE",
                    "confidence": 0.95,
                    "explanation": "This claim is accurate. The scientific consensus based on radiometric dating of meteorites and Earth's oldest rocks establishes the Earth's age at approximately 4.54 billion years, with an error margin of about 50 million years.",
                    "sources": ["Scientific consensus", "Radiometric dating studies"]
                }
                """
            elif "boils at" in last_message and "all elevations" in last_message:
                return """
                {
                    "verdict": "FALSE",
                    "confidence": 0.98,
                    "explanation": "This claim is false. While water boils at 100°C (212°F) at standard atmospheric pressure (1 atmosphere or sea level), the boiling point decreases at higher elevations due to lower atmospheric pressure. For example, at the top of Mount Everest, water boils at approximately 68°C (154°F).",
                    "sources": ["Basic physics", "Atmospheric pressure studies"]
                }
                """
            elif "climate change" in last_message and "natural cycles" in last_message:
                return """
                {
                    "verdict": "FALSE",
                    "confidence": 0.97,
                    "explanation": "This claim is false. The scientific consensus, supported by multiple independent lines of evidence, confirms that human activities are the primary drivers of current climate change, primarily through greenhouse gas emissions from burning fossil fuels.",
                    "sources": ["IPCC reports", "Scientific consensus studies", "Climate research data"]
                }
                """
            elif "speed of light" in last_message:
                return """
                {
                    "verdict": "TRUE",
                    "confidence": 0.99,
                    "explanation": "This claim is accurate. The speed of light in a vacuum is precisely 299,792,458 meters per second, as defined by the International System of Units (SI).",
                    "sources": ["International Bureau of Weights and Measures", "Physics textbooks"]
                }
                """
            elif "tallest mountain" in last_message and "K2" in last_message:
                return """
                {
                    "verdict": "FALSE",
                    "confidence": 0.98,
                    "explanation": "This claim is false. Mount Everest is the tallest mountain in the world, with a height of 29,032 feet (8,849 meters) above sea level. K2 is the second-tallest at 28,251 feet (8,611 meters).",
                    "sources": ["Geographical surveys", "National Geographic"]
                }
                """
            elif "vaccines" in last_message and "autism" in last_message:
                return """
                {
                    "verdict": "FALSE",
                    "confidence": 0.99,
                    "explanation": "This claim is false. Extensive scientific research has found no link between vaccines and autism. The original study suggesting this connection was retracted due to serious procedural errors, undisclosed financial conflicts of interest, and ethical violations.",
                    "sources": ["Multiple large-scale epidemiological studies", "Centers for Disease Control", "World Health Organization"]
                }
                """
            else:
                return """
                {
                    "verdict": "UNVERIFIABLE",
                    "confidence": 0.5,
                    "explanation": "This claim cannot be verified with the available evidence.",
                    "sources": ["Insufficient information"]
                }
                """
        
        # Default response
        return '{"result": "This is a mock response for testing purposes."}'
    
    @property
    def _llm_type(self) -> str:
        """Return the type of LLM."""
        return "mock-chat-model"


def create_llm(
    provider: str = LLM_PROVIDER_ANTHROPIC,
    model_name: Optional[str] = None,
    temperature: float = 0.0,
    **kwargs
) -> BaseChatModel:
    """Create a language model instance.
    
    Args:
        provider: The LLM provider to use (anthropic, openai, or mock)
        model_name: The model name to use (defaults to provider's default)
        temperature: Temperature for model generation
        **kwargs: Additional model parameters
        
    Returns:
        A configured language model
    """
    # Use mock mode if specified or if neither Anthropic nor OpenAI keys are available
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    if provider == LLM_PROVIDER_MOCK or (provider != LLM_PROVIDER_MOCK and not anthropic_key and not openai_key):
        logger.info("Using mock language model for testing")
        return MockChatModel(temperature=temperature)
    
    if provider == LLM_PROVIDER_ANTHROPIC:
        default_model = "claude-3-sonnet-20240229"
        
        if not anthropic_key:
            logger.warning("No Anthropic API key found in environment")
            return MockChatModel(temperature=temperature)
        
        if ChatAnthropic is None:
            logger.warning("langchain_anthropic module not found, using mock model instead")
            return MockChatModel(temperature=temperature)
            
        return ChatAnthropic(
            model_name=model_name or default_model,
            temperature=temperature,
            anthropic_api_key=anthropic_key,
            **kwargs
        )
    
    elif provider == LLM_PROVIDER_OPENAI:
        default_model = "gpt-4o"
        
        if not openai_key:
            logger.warning("No OpenAI API key found in environment")
            return MockChatModel(temperature=temperature)
        
        if ChatOpenAI is None:
            logger.warning("langchain_openai module not found, using mock model instead")
            return MockChatModel(temperature=temperature)
            
        return ChatOpenAI(
            model_name=model_name or default_model,
            temperature=temperature,
            openai_api_key=openai_key,
            **kwargs
        )
    
    else:
        logger.warning(f"Unsupported LLM provider: {provider}, using mock model")
        return MockChatModel(temperature=temperature)


def create_knowledge_repository(
    collection_name: str = "truth_checker_kb",
    embedding_model_name: str = "BAAI/bge-base-en-v1.5",
    persist_directory: Optional[str] = None
) -> KnowledgeRepository:
    """Create a knowledge repository instance.
    
    Args:
        collection_name: Name of the ChromaDB collection
        embedding_model_name: Name of the embedding model to use
        persist_directory: Directory to persist the database
        
    Returns:
        A configured knowledge repository
    """
    return ChromaKnowledgeRepository(
        collection_name=collection_name,
        embedding_model_name=embedding_model_name,
        persist_directory=persist_directory
    )


def create_claim_detection_service(
    llm: Optional[BaseChatModel] = None,
    llm_config: Optional[Dict[str, Any]] = None
) -> ClaimDetectionService:
    """Create a claim detection service instance.
    
    Args:
        llm: Language model to use (created if not provided)
        llm_config: Configuration for the language model if creating one
        
    Returns:
        A configured claim detection service
    """
    # Create LLM if not provided
    if llm is None:
        config = llm_config or {}
        llm = create_llm(**config)
    
    return LangChainClaimDetectionService(llm=llm)


def create_fact_checking_service(
    knowledge_repository: Optional[KnowledgeRepository] = None,
    llm: Optional[BaseChatModel] = None,
    llm_config: Optional[Dict[str, Any]] = None,
    max_iterations: int = 3,
    kb_config: Optional[Dict[str, Any]] = None
) -> FactCheckingService:
    """Create a fact checking service instance.
    
    Args:
        knowledge_repository: Knowledge repository to use (created if not provided)
        llm: Language model to use (created if not provided)
        llm_config: Configuration for the language model if creating one
        max_iterations: Maximum number of iterations for the retrieval loop
        kb_config: Configuration for the knowledge repository if creating one
        
    Returns:
        A configured fact checking service
    """
    # Create LLM if not provided
    if llm is None:
        config = llm_config or {}
        llm = create_llm(**config)
    
    # Create knowledge repository if not provided
    if knowledge_repository is None:
        config = kb_config or {}
        knowledge_repository = create_knowledge_repository(**config)
    
    return LangGraphFactCheckingService(
        llm=llm,
        knowledge_repository=knowledge_repository,
        max_iterations=max_iterations
    ) 