#!/usr/bin/env python3
"""Example script demonstrating HTTP file upload for transcription."""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import the truth_checker package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truth_checker.interfaces.clients.websocket_client import upload_file


async def upload_audio_file(file_path, server_url, verbose=False):
    """Upload an audio file to the server for transcription.
    
    Args:
        file_path: Path to the audio file to upload
        server_url: URL of the server's file upload endpoint
        verbose: Whether to enable verbose logging
    """
    # Set up logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    
    try:
        # Upload the file
        logger.info(f"Uploading audio file: {file_path}")
        results = await upload_file(server_url, file_path)
        
        # Print results
        print("\nTranscription Results:")
        print("=====================")
        
        for i, result in enumerate(results, 1):
            confidence = result.get("confidence", 0)
            is_final = result.get("is_final", False)
            transcript = result.get("transcript", "")
            
            # Print the transcript with confidence score
            status = "Final" if is_final else "Interim"
            print(f"{i}. [{status}] ({confidence:.2f}): {transcript}")
            
        return 0
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return 1


def main():
    """Parse arguments and run the HTTP client example."""
    parser = argparse.ArgumentParser(description="HTTP Client Example")
    parser.add_argument(
        "file_path",
        help="Path to the audio file to upload"
    )
    parser.add_argument(
        "--server",
        default="http://localhost:8000/api/transcribe",
        help="Server URL (default: http://localhost:8000/api/transcribe)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Check if the file exists
    if not os.path.exists(args.file_path):
        print(f"Error: File not found: {args.file_path}")
        return 1
    
    # Run the example
    return asyncio.run(upload_audio_file(args.file_path, args.server, args.verbose))


if __name__ == "__main__":
    sys.exit(main()) 