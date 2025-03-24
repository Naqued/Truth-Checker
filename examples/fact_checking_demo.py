#!/usr/bin/env python3
"""
Truth Checker Fact Checking Demo

This script demonstrates how to use the fact checking components of the Truth Checker
to verify claims from text input.
"""

import argparse
import asyncio
import os
import sys
import logging
from typing import List, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from truth_checker.domain.models import Claim, Transcript, FactCheckResult
from truth_checker.application.factory import (
    create_claim_detection_service,
    create_fact_checking_service,
    create_knowledge_repository,
    create_llm,
    LLM_PROVIDER_ANTHROPIC,
    LLM_PROVIDER_OPENAI,
    LLM_PROVIDER_MOCK
)
from truth_checker.application.knowledge_loader import populate_sample_knowledge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fact_checking_demo")


async def detect_and_check_claims(text: str, llm_provider: str) -> List[FactCheckResult]:
    """Detect claims in text and fact check them.
    
    Args:
        text: Text to analyze for claims
        llm_provider: LLM provider to use
        
    Returns:
        List of fact check results
    """
    results = []
    
    # Create a transcript from the text
    transcript = Transcript(
        text=text,
        confidence=1.0,
        is_final=True,
        start_time=0.0,
        end_time=0.0,
        timestamp=datetime.now()
    )
    
    # Initialize services
    logger.info(f"Initializing services with {llm_provider} as LLM provider")
    llm = create_llm(provider=llm_provider)
    claim_detector = create_claim_detection_service(llm=llm)
    
    # Create knowledge repository and populate with sample data
    knowledge_repo = create_knowledge_repository(
        collection_name="demo_knowledge",
        persist_directory="./data/vector_db"
    )
    
    # Populate with sample knowledge
    await populate_sample_knowledge(knowledge_repo)
    
    # Create fact checking service
    fact_checker = create_fact_checking_service(
        llm=llm,
        knowledge_repository=knowledge_repo,
        max_iterations=2
    )
    
    # Detect claims
    logger.info(f"Detecting claims in: {text[:100]}...")
    claims = await claim_detector.detect_claims(transcript)
    logger.info(f"Detected {len(claims)} claims")
    
    # Fact check each claim
    for i, claim in enumerate(claims):
        logger.info(f"Fact checking claim {i+1}/{len(claims)}: {claim.text}")
        result = await fact_checker.check_claim(claim)
        results.append(result)
        
        # Display result
        print(f"\nClaim: {claim.text}")
        print(f"Verdict: {result.verdict.name}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Explanation: {result.explanation}")
        print("Sources:")
        for source in result.sources:
            print(f"  - {source}")
        print("-" * 80)
    
    return results


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Truth Checker Fact Checking Demo")
    
    parser.add_argument(
        "--text",
        type=str,
        help="Text to analyze for claims"
    )
    
    parser.add_argument(
        "--file",
        type=str,
        help="Path to text file containing content to analyze"
    )
    
    parser.add_argument(
        "--llm",
        type=str,
        choices=["anthropic", "openai", "mock"],
        default="anthropic",
        help="LLM provider to use"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point for the script."""
    args = parse_args()
    
    # Get the text to analyze
    if args.text:
        text = args.text
    elif args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        # Default demo text
        text = """
        The Earth is 4.54 billion years old. Water boils at exactly 100 degrees Celsius 
        at all elevations. Climate change is primarily caused by natural cycles rather than 
        human activities. The speed of light in a vacuum is 299,792,458 meters per second.
        The tallest mountain in the world is K2. Vaccines cause autism.
        """
        print("No input provided, using default demo text:\n")
        print(text)
    
    # Choose LLM provider
    if args.llm == "anthropic":
        llm_provider = LLM_PROVIDER_ANTHROPIC
    elif args.llm == "openai":
        llm_provider = LLM_PROVIDER_OPENAI
    else:
        llm_provider = LLM_PROVIDER_MOCK
    
    # Run the demo
    results = await detect_and_check_claims(text, llm_provider)
    
    # Summarize results
    true_count = sum(1 for r in results if r.verdict.name == "TRUE")
    false_count = sum(1 for r in results if r.verdict.name == "FALSE")
    other_count = len(results) - true_count - false_count
    
    print("\nSummary:")
    print(f"Total claims detected: {len(results)}")
    print(f"True claims: {true_count}")
    print(f"False claims: {false_count}")
    print(f"Other verdicts: {other_count}")


if __name__ == "__main__":
    # Set up the event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        loop.close() 