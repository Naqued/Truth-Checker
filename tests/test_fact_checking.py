"""Tests for the fact checking components."""

import os
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from truth_checker.domain.models import Transcript, Claim, FactCheckVerdict, FactCheckResult
from truth_checker.application.claim_detection_service import LangChainClaimDetectionService
from truth_checker.application.knowledge_repository import ChromaKnowledgeRepository
from truth_checker.application.fact_checking_service import LangGraphFactCheckingService


@pytest.mark.asyncio
async def test_claim_detection_service():
    """Test the claim detection service."""
    # Create a mock LLM that returns a predefined response
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value.content = """
    [
        {
            "text": "The Earth is 4.54 billion years old",
            "confidence": 0.95,
            "context": "Statement about Earth's age"
        },
        {
            "text": "Water boils at 100 degrees Celsius at standard pressure",
            "confidence": 0.98,
            "context": "Statement about boiling point of water"
        }
    ]
    """
    
    # Create the claim detection service with the mock LLM
    service = LangChainClaimDetectionService(llm=mock_llm)
    
    # Create a test transcript
    transcript = Transcript(
        text="The Earth is 4.54 billion years old. Water boils at 100 degrees Celsius at standard pressure.",
        confidence=1.0,
        is_final=True,
        timestamp=datetime.now()
    )
    
    # Detect claims
    with patch('json.loads', return_value=[
        {
            "text": "The Earth is 4.54 billion years old",
            "confidence": 0.95,
            "context": "Statement about Earth's age"
        },
        {
            "text": "Water boils at 100 degrees Celsius at standard pressure",
            "confidence": 0.98,
            "context": "Statement about boiling point of water"
        }
    ]):
        claims = await service.detect_claims(transcript)
    
    # Assertions
    assert len(claims) == 2
    assert claims[0].text == "The Earth is 4.54 billion years old"
    assert claims[1].text == "Water boils at 100 degrees Celsius at standard pressure"
    assert claims[0].confidence == 0.95
    assert claims[1].confidence == 0.98


@pytest.mark.asyncio
async def test_fact_checking_service():
    """Test the fact checking service."""
    # Mock LLM for different stages of the workflow
    mock_llm = AsyncMock()
    
    # Mock the query construction response
    mock_llm.ainvoke.side_effect = [
        # Query construction response
        Mock(content='{"queries": ["Earth age", "How old is Earth", "Earth formation age"]}'),
        
        # Evidence analysis response
        Mock(content="""
        {
            "verdict": "SUPPORTED",
            "confidence": 0.9,
            "key_evidence": "The Earth is approximately 4.54 billion years old",
            "needs_more_evidence": false
        }
        """),
        
        # Final verdict response
        Mock(content="""
        {
            "verdict": "TRUE",
            "confidence": 0.95,
            "explanation": "The claim is accurate. Scientific evidence from radiometric dating confirms Earth is approximately 4.54 billion years old.",
            "sources": ["Scientific consensus"]
        }
        """)
    ]
    
    # Mock knowledge repository
    mock_repository = AsyncMock()
    mock_repository.search.return_value = [
        {
            "content": "The Earth is approximately 4.54 billion years old, determined through radiometric dating.",
            "relevance_score": 0.95,
            "metadata": {
                "source": "Scientific consensus",
                "source_type": "scientific_database"
            }
        }
    ]
    
    # Create the fact checking service with mocks
    service = LangGraphFactCheckingService(
        llm=mock_llm,
        knowledge_repository=mock_repository,
        max_iterations=2
    )
    
    # Create a test claim
    claim = Claim(
        text="The Earth is 4.54 billion years old",
        transcript_id="test",
        confidence=0.9,
        source_text="The Earth is 4.54 billion years old",
        context="Statement about Earth's age"
    )
    
    # Check the claim
    with patch('json.loads', side_effect=[
        {"queries": ["Earth age", "How old is Earth", "Earth formation age"]},
        {
            "verdict": "SUPPORTED",
            "confidence": 0.9,
            "key_evidence": "The Earth is approximately 4.54 billion years old",
            "needs_more_evidence": False
        },
        {
            "verdict": "TRUE",
            "confidence": 0.95,
            "explanation": "The claim is accurate. Scientific evidence from radiometric dating confirms Earth is approximately 4.54 billion years old.",
            "sources": ["Scientific consensus"]
        }
    ]):
        result = await service.check_claim(claim)
    
    # Assertions
    assert result.verdict == FactCheckVerdict.TRUE
    assert result.confidence == 0.95
    assert "Scientific evidence" in result.explanation
    assert "Scientific consensus" in result.sources
    assert result.is_true is True 