#!/usr/bin/env python3
"""Example script demonstrating WebSocket audio streaming."""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import the truth_checker package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truth_checker.interfaces.clients.websocket_client import WebSocketClient


async def stream_audio_file(file_path, server_url, verbose=False):
    """Stream an audio file to the WebSocket server and print transcriptions.
    
    Args:
        file_path: Path to the audio file to stream
        server_url: URL of the WebSocket server
        verbose: Whether to enable verbose logging
    """
    # Set up logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    
    # Create WebSocket client
    client = WebSocketClient(server_url=server_url)
    
    # Set up transcript callback
    def on_transcript(transcript):
        if transcript.is_final:
            confidence = f"({transcript.confidence:.2f})"
            print(f"\nFinal {confidence}: {transcript.text}")
        else:
            # Print without newline to allow updates
            print(f"\rInterim: {transcript.text}", end="", flush=True)
    
    # Register callback
    client.register_transcript_callback(on_transcript)
    
    try:
        # Start the client
        logger.info("Starting WebSocket client...")
        await client.start()
        
        # Stream the audio file
        logger.info(f"Streaming audio file: {file_path}")
        await client.stream_wav_file(file_path, real_time=True)
        
        # Wait for final transcriptions
        logger.info("Finished streaming, waiting for final transcriptions...")
        await asyncio.sleep(2)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    finally:
        # Stop the client
        logger.info("Stopping WebSocket client...")
        await client.stop()
    
    return 0


def main():
    """Parse arguments and run the WebSocket client example."""
    parser = argparse.ArgumentParser(description="WebSocket Client Example")
    parser.add_argument(
        "file_path",
        help="Path to the audio file to stream"
    )
    parser.add_argument(
        "--server",
        default="ws://localhost:8000/api/stream",
        help="WebSocket server URL (default: ws://localhost:8000/api/stream)"
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
    return asyncio.run(stream_audio_file(args.file_path, args.server, args.verbose))


if __name__ == "__main__":
    sys.exit(main()) 