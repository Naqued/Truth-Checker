#!/usr/bin/env python3
"""Debug script for WebSocket streaming with Deepgram."""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from websockets.client import connect

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def stream_audio_file(file_path, server_url="ws://localhost:8000/api/stream"):
    """Stream an audio file to the WebSocket server with debug logging."""
    if not Path(file_path).exists():
        logger.error(f"Audio file not found: {file_path}")
        return
        
    logger.info(f"Streaming file: {file_path}")
    logger.info(f"Server URL: {server_url}")
    
    try:
        # Connect to WebSocket
        async with connect(server_url) as websocket:
            logger.info("Connected to WebSocket")
            
            # Receive welcome message
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received welcome message: {data}")
            
            # Send start command
            start_command = {
                "command": "start",
                "audio_format": {
                    "mimetype": "audio/mpeg",
                    "sample_rate": 48000,  # 48kHz for this MP3 file
                    "channels": 2  # Stereo audio
                }
            }
            await websocket.send(json.dumps(start_command))
            logger.info("Sent start command")
            
            # Receive start confirmation
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received start confirmation: {data}")
            
            # Check if using mock mode
            if "note" in data and "mock" in data["note"].lower():
                logger.warning("Server is using mock transcription mode!")
            
            # Open and stream the audio file
            with open(file_path, "rb") as audio_file:
                # Read in chunks of 4KB
                chunk_size = 4096
                chunk_number = 0
                
                while True:
                    chunk = audio_file.read(chunk_size)
                    if not chunk:
                        break
                        
                    # Send audio chunk
                    await websocket.send(chunk)
                    logger.debug(f"Sent chunk #{chunk_number}, size: {len(chunk)} bytes")
                    chunk_number += 1
                    
                    # Brief pause to simulate real-time
                    await asyncio.sleep(0.05)
                    
                    # Check for any incoming messages
                    try:
                        # Use a timeout to avoid blocking
                        response = await asyncio.wait_for(websocket.recv(), 0.01)
                        data = json.loads(response)
                        if "transcript" in data:
                            logger.info(f"Transcript received: '{data['transcript']}' (confidence: {data['confidence']}, final: {data['is_final']})")
                        else:
                            logger.info(f"Received message: {data}")
                    except asyncio.TimeoutError:
                        # No message yet, continue
                        pass
                    except Exception as e:
                        logger.error(f"Error receiving message: {e}")
            
            logger.info("File sent, waiting for final transcripts...")
            
            # Wait for any final transcripts
            try:
                while True:
                    # Use a timeout to allow graceful exit
                    response = await asyncio.wait_for(websocket.recv(), 2.0)
                    data = json.loads(response)
                    if "transcript" in data:
                        logger.info(f"Final transcript: '{data['transcript']}' (confidence: {data['confidence']}, final: {data['is_final']})")
                    else:
                        logger.info(f"Received message: {data}")
            except asyncio.TimeoutError:
                # No more messages
                logger.info("No more messages after timeout, assuming transcription complete")
            except Exception as e:
                logger.error(f"Error receiving final messages: {e}")
                
            # Send stop command
            await websocket.send(json.dumps({"command": "stop"}))
            logger.info("Sent stop command")
            
            logger.info("WebSocket streaming complete")
                
    except Exception as e:
        logger.error(f"Error in WebSocket streaming: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    # Get file path from command line
    if len(sys.argv) < 2:
        logger.error("Please provide an audio file path")
        sys.exit(1)
        
    file_path = sys.argv[1]
    server_url = sys.argv[2] if len(sys.argv) > 2 else "ws://localhost:8000/api/stream"
    
    # Run the async function
    asyncio.run(stream_audio_file(file_path, server_url))
