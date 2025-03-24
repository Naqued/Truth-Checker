"""Implementation of the claim detection service using LangChain."""

import json
import logging
from typing import Dict, List, Optional, Any

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from truth_checker.domain.models import Claim, Transcript
from truth_checker.domain.ports import ClaimDetectionService

logger = logging.getLogger(__name__)

# Define the prompt templates for claim detection
CLAIM_DETECTION_PROMPT = """You are an expert fact-checker who specializes in identifying factual claims.

Analyze the following transcript and identify all verifiable factual claims. A factual claim is an assertion about the world that can be verified as true or false based on evidence.

Examples of factual claims:
- "The Earth is 4.5 billion years old"
- "The president signed the bill yesterday"
- "This technology reduces carbon emissions by 30%"

Do NOT include as claims:
- Opinions ("I think the movie was good")
- Subjective statements ("She is the best athlete")
- Questions ("Is the economy improving?")
- Hypotheticals ("If we invested more, we might see better results")

For each claim you identify:
1. Extract the exact statement
2. Rate your confidence in it being a factual claim (0.0-1.0)
3. Provide any context needed to understand the claim

Transcript:
{transcript_text}

Format your response as a JSON list of claims:
"""


class LangChainClaimDetectionService(ClaimDetectionService):
    """Implementation of ClaimDetectionService using LangChain and LLMs."""

    def __init__(self, llm: BaseChatModel):
        """Initialize the claim detection service.
        
        Args:
            llm: Language model to use for claim detection
        """
        self.llm = llm
        self.parser = JsonOutputParser()
        
        # Create the claim detection chain
        self.prompt = ChatPromptTemplate.from_template(CLAIM_DETECTION_PROMPT)
        self.claim_detection_chain = self.prompt | self.llm | self.parser
    
    async def detect_claims(self, transcript: Transcript) -> List[Claim]:
        """Detect claims in a transcript.

        Args:
            transcript: The transcript to analyze

        Returns:
            List of detected claims
        """
        logger.info(f"Detecting claims in transcript: {transcript.text[:100]}...")
        
        try:
            # Run the claim detection chain
            response = await self.claim_detection_chain.ainvoke({
                "transcript_text": transcript.text
            })
            
            # Parse the claims from the response
            claims = self._parse_claims(response, transcript)
            
            logger.info(f"Detected {len(claims)} claims in transcript.")
            return claims
            
        except Exception as e:
            logger.error(f"Error detecting claims: {e}")
            return []
    
    def _parse_claims(self, response: Dict[str, Any], transcript: Transcript) -> List[Claim]:
        """Parse the claims from the LLM response.
        
        Args:
            response: The parsed JSON response from the LLM
            transcript: The original transcript
            
        Returns:
            List of Claim objects
        """
        claims_list = []
        
        # Handle different possible response formats
        if isinstance(response, list):
            claims_data = response
        elif isinstance(response, dict) and "claims" in response:
            claims_data = response.get("claims", [])
        else:
            logger.warning(f"Unexpected response format: {response}")
            return []
        
        # Convert each claim to a Claim object
        for claim_data in claims_data:
            # Skip if required fields are missing
            if not claim_data.get("text"):
                continue
                
            # Create a Claim object
            claim = Claim(
                text=claim_data.get("text", ""),
                transcript_id=str(transcript.timestamp),
                confidence=float(claim_data.get("confidence", 0.7)),
                source_text=transcript.text,
                start_time=transcript.start_time,
                end_time=transcript.end_time,
                context=claim_data.get("context"),
                metadata={
                    "model": getattr(self.llm, "model_name", "unknown"),
                    "original_response": claim_data
                }
            )
            
            claims_list.append(claim)
            
        return claims_list 