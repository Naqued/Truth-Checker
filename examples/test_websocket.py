#!/usr/bin/env python3
"""Test client for WebSocket transcription streaming without sending audio."""

import asyncio
import json
import logging
import sys
from websockets.client import connect

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def listen_for_transcripts(server_url="ws://localhost:8000/api/stream"):
    """Connect to WebSocket and listen for transcripts without sending audio."""
    try:
        async with connect(server_url) as websocket:
            logger.info(f"Connected to WebSocket: {server_url}")
            
            # Receive and print welcome message
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received: {data}")
            
            # Send start command with audio format parameters
            await websocket.send(json.dumps({
                "command": "start",
                "audio_format": {
                    "mimetype": "audio/mpeg",
                    "encoding": "linear16",
                    "sample_rate": 16000,
                    "channels": 1
                }
            }))
            logger.info("Sent start command")
            
            # Listen for transcripts for 30 seconds
            start_time = asyncio.get_event_loop().time()
            
            try:
                while asyncio.get_event_loop().time() - start_time < 30:
                    try:
                        # Set a timeout to allow for checking the elapsed time
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(response)
                        
                        # Check for transcript
                        if "transcript" in data:
                            logger.info(f"Transcript: {data['transcript']} (confidence: {data['confidence']}, final: {data['is_final']})")
                        else:
                            logger.info(f"Received: {data}")
                    except asyncio.TimeoutError:
                        # Just a timeout, continue
                        continue
            finally:
                # Send stop command before exiting
                await websocket.send(json.dumps({"command": "stop"}))
                logger.info("Sent stop command")
                
                # Wait for confirmation
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    logger.info(f"Final response: {response}")
                except asyncio.TimeoutError:
                    pass
                    
            logger.info("Test complete")
    except Exception as e:
        logger.error(f"Error: {e}")
        
if __name__ == "__main__":
    # Get server URL from command line or use default
    server_url = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8000/api/stream"
    
    logger.info(f"Starting WebSocket test client for: {server_url}")
    asyncio.run(listen_for_transcripts(server_url)) 