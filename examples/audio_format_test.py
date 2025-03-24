#!/usr/bin/env python3
"""Test script that demonstrates processing various audio formats."""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import the truth_checker package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truth_checker.interfaces.clients.websocket_client import upload_file, WebSocketClient


async def test_audio_format(file_path: str, method: str = "http", server_url: str = None, verbose: bool = False):
    """Test processing an audio file with the specified method.
    
    Args:
        file_path: Path to the audio file to test
        method: Method to use for testing (http or websocket)
        server_url: Server URL (default: derived from method)
        verbose: Whether to enable verbose logging
    """
    # Set up logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    
    # Get file extension
    file_ext = os.path.splitext(file_path.lower())[1]
    
    # Set default server URL based on method
    if not server_url:
        if method == "http":
            server_url = "http://localhost:8000/api/transcribe"
        else:  # websocket
            server_url = "ws://localhost:8000/api/stream"
    
    logger.info(f"Testing {file_ext} audio file with {method} method")
    logger.info(f"File: {file_path}")
    logger.info(f"Server URL: {server_url}")
    
    try:
        if method == "http":
            # HTTP upload
            logger.info("Uploading file via HTTP...")
            results = await upload_file(server_url, file_path)
            
            # Print results
            logger.info(f"Received {len(results)} transcription results")
            for i, result in enumerate(results, 1):
                confidence = result.get("confidence", 0)
                is_final = result.get("is_final", False)
                transcript = result.get("transcript", "")
                
                status = "Final" if is_final else "Interim"
                print(f"{i}. [{status}] ({confidence:.2f}): {transcript}")
                
        else:
            # WebSocket streaming
            logger.info("Streaming file via WebSocket...")
            
            # Create WebSocket client with appropriate format hints
            # for the file type
            audio_format = {}
            
            # Configure WebSocket client
            client = WebSocketClient(server_url=server_url, audio_format=audio_format)
            
            # Set up transcript callback
            def on_transcript(transcript):
                if transcript.is_final:
                    confidence = f"({transcript.confidence:.2f})"
                    print(f"\nFinal {confidence}: {transcript.text}")
                else:
                    print(f"\rInterim: {transcript.text}", end="", flush=True)
                    
            client.register_transcript_callback(on_transcript)
            
            # Connect and stream
            try:
                await client.start()
                await client.stream_wav_file(file_path, real_time=False)  # Fast streaming
                
                # Wait for processing to complete
                logger.info("Waiting for transcription to complete...")
                await asyncio.sleep(3)
                
            finally:
                await client.stop()
    
    except Exception as e:
        logger.error(f"Error testing audio format: {e}")
        return 1
        
    return 0


def main():
    """Parse arguments and run the audio format test."""
    parser = argparse.ArgumentParser(description="Audio Format Test")
    parser.add_argument(
        "file_path",
        help="Path to the audio file to test"
    )
    parser.add_argument(
        "--method",
        choices=["http", "websocket"],
        default="http",
        help="Method to use for testing (http or websocket)"
    )
    parser.add_argument(
        "--server",
        help="Server URL (default: derived from method)"
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
    
    # Run the test
    return asyncio.run(test_audio_format(
        args.file_path, 
        method=args.method, 
        server_url=args.server,
        verbose=args.verbose
    ))


if __name__ == "__main__":
    sys.exit(main()) 