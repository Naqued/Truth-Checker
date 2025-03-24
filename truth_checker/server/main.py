#!/usr/bin/env python3
"""
Truth Checker API Server

This module runs the Truth Checker API server with options to configure the language model.
"""

import argparse
import asyncio
import logging
import os
import sys
from typing import Dict, Any

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from dotenv import load_dotenv
from fastapi import FastAPI

from truth_checker.interfaces.api.server import start_server
from truth_checker.application.factory import (
    LLM_PROVIDER_ANTHROPIC,
    LLM_PROVIDER_OPENAI, 
    LLM_PROVIDER_MOCK
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("truth_checker_server")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Truth Checker API Server")
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host address to bind the server to"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to"
    )
    
    parser.add_argument(
        "--llm",
        type=str,
        choices=["anthropic", "openai", "mock"],
        default="anthropic",
        help="LLM provider to use for fact checking"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point for the server."""
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Set log level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Set the LLM provider in the environment
    if args.llm == "mock":
        os.environ["LLM_PROVIDER"] = LLM_PROVIDER_MOCK
        logger.info("Using mock LLM provider for fact checking")
    elif args.llm == "openai":
        os.environ["LLM_PROVIDER"] = LLM_PROVIDER_OPENAI
        logger.info("Using OpenAI LLM provider for fact checking")
    else:
        os.environ["LLM_PROVIDER"] = LLM_PROVIDER_ANTHROPIC
        logger.info("Using Anthropic LLM provider for fact checking")
    
    # Start the server
    logger.info(f"Starting Truth Checker API server on {args.host}:{args.port}")
    await start_server(host=args.host, port=args.port)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1) 