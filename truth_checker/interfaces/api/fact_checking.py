"""FastAPI endpoints for fact checking."""

import logging
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from truth_checker.domain.models import Claim, FactCheckResult, FactCheckVerdict, Transcript
from truth_checker.domain.ports import ClaimDetectionService, FactCheckingService
from truth_checker.application.factory import (
    create_claim_detection_service,
    create_fact_checking_service,
    create_knowledge_repository,
    create_llm,
    LLM_PROVIDER_ANTHROPIC,
    LLM_PROVIDER_OPENAI,
    LLM_PROVIDER_MOCK
)

logger = logging.getLogger(__name__)

# Define API models
class ClaimRequest(BaseModel):
    """Request model for claim verification."""
    
    text: str = Field(..., description="The claim text to verify")
    context: Optional[str] = Field(None, description="Additional context for the claim")


class ClaimResponse(BaseModel):
    """Response model for detected claim."""
    
    text: str = Field(..., description="The claim text")
    confidence: float = Field(..., description="Confidence score for this being a factual claim")
    context: Optional[str] = Field(None, description="Context for the claim")


class TranscriptRequest(BaseModel):
    """Request model for analyzing a transcript."""
    
    text: str = Field(..., description="The transcript text to analyze")


class FactCheckResponse(BaseModel):
    """Response model for fact check results."""
    
    claim: str = Field(..., description="The claim that was verified")
    verdict: str = Field(..., description="Verification verdict (TRUE, FALSE, etc.)")
    confidence: float = Field(..., description="Confidence score for the verdict")
    explanation: str = Field(..., description="Explanation for the verdict")
    sources: List[str] = Field(default_factory=list, description="Sources used for verification")
    is_true: bool = Field(..., description="Whether the claim is true")


# Create router
router = APIRouter(
    prefix="/fact-check",
    tags=["fact-checking"],
    responses={404: {"description": "Not found"}},
)


# Get the LLM provider from environment
def get_llm_provider():
    """Get the LLM provider from environment variables."""
    provider = os.environ.get("LLM_PROVIDER", LLM_PROVIDER_ANTHROPIC)
    logger.info(f"Using LLM provider: {provider}")
    return provider


# Service providers for dependency injection
def get_claim_detection_service() -> ClaimDetectionService:
    """Get or create a claim detection service for dependency injection."""
    llm_provider = get_llm_provider()
    llm = create_llm(provider=llm_provider)
    return create_claim_detection_service(llm=llm)


def get_fact_checking_service() -> FactCheckingService:
    """Get or create a fact checking service for dependency injection."""
    llm_provider = get_llm_provider()
    
    # Create a knowledge repository
    knowledge_repo = create_knowledge_repository(
        collection_name="api_knowledge_base",
        persist_directory="./data/vector_db"
    )
    
    # Create LLM
    llm = create_llm(provider=llm_provider)
    
    # Create and return service
    return create_fact_checking_service(
        llm=llm,
        knowledge_repository=knowledge_repo
    )


# API endpoints
@router.post("/claims", response_model=List[ClaimResponse])
async def detect_claims(
    request: TranscriptRequest,
    claim_service: ClaimDetectionService = Depends(get_claim_detection_service)
):
    """Detect claims in a transcript."""
    try:
        # Create a transcript from the request
        transcript = Transcript(
            text=request.text,
            confidence=1.0,
            is_final=True
        )
        
        # Detect claims
        claims = await claim_service.detect_claims(transcript)
        
        # Convert to response format
        return [
            ClaimResponse(
                text=claim.text,
                confidence=claim.confidence,
                context=claim.context
            )
            for claim in claims
        ]
    except Exception as e:
        logger.error(f"Error detecting claims: {e}")
        raise HTTPException(status_code=500, detail=f"Error detecting claims: {str(e)}")


@router.post("/verify", response_model=FactCheckResponse)
async def verify_claim(
    request: ClaimRequest,
    fact_service: FactCheckingService = Depends(get_fact_checking_service)
):
    """Verify a single claim."""
    try:
        # Create a claim object
        claim = Claim(
            text=request.text,
            transcript_id="api-request",
            confidence=1.0,
            source_text=request.text,
            context=request.context
        )
        
        # Check the claim
        result = await fact_service.check_claim(claim)
        
        # Convert to response format
        return FactCheckResponse(
            claim=result.claim.text,
            verdict=result.verdict.name,
            confidence=result.confidence,
            explanation=result.explanation,
            sources=result.sources,
            is_true=result.is_true
        )
    except Exception as e:
        logger.error(f"Error verifying claim: {e}")
        raise HTTPException(status_code=500, detail=f"Error verifying claim: {str(e)}")


@router.post("/analyze", response_model=List[FactCheckResponse])
async def analyze_transcript(
    request: TranscriptRequest,
    claim_service: ClaimDetectionService = Depends(get_claim_detection_service),
    fact_service: FactCheckingService = Depends(get_fact_checking_service)
):
    """Analyze a transcript by detecting and verifying all claims."""
    try:
        # Create a transcript from the request
        transcript = Transcript(
            text=request.text,
            confidence=1.0,
            is_final=True
        )
        
        # Detect claims
        claims = await claim_service.detect_claims(transcript)
        
        # Check each claim
        results = []
        for claim in claims:
            result = await fact_service.check_claim(claim)
            results.append(result)
        
        # Convert to response format
        return [
            FactCheckResponse(
                claim=result.claim.text,
                verdict=result.verdict.name,
                confidence=result.confidence,
                explanation=result.explanation,
                sources=result.sources,
                is_true=result.is_true
            )
            for result in results
        ]
    except Exception as e:
        logger.error(f"Error analyzing transcript: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing transcript: {str(e)}") 