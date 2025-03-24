#!/usr/bin/env python3
"""
Demo script for the Truth Checker application.

This script demonstrates the different ways to use the Truth Checker:
1. Direct file transcription
2. API server communication (HTTP/WebSocket)
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add parent directory to Python path to import from the project
sys.path.append(str(Path(__file__).resolve().parent.parent))

from truth_checker.infrastructure.services.deepgram_service import DeepgramTranscriptionService
from truth_checker.application.transcription_service import TranscriptionApplicationService


async def direct_transcription(file_path):
    """Transcribe a file directly using the DeepgramTranscriptionService."""
    print(f"🎤 Transcribing file: {file_path}")
    
    # Initialize services
    api_key = os.environ.get("DEEPGRAM_API_KEY")
    deepgram_service = DeepgramTranscriptionService(api_key=api_key)
    transcription_service = TranscriptionApplicationService(transcription_service=deepgram_service)
    
    # Transcribe the file
    transcripts = await transcription_service.transcribe_file(file_path)
    
    print("\n📝 Transcription Results:")
    print("======================")
    for i, transcript in enumerate(transcripts, 1):
        print(f"Transcript #{i}:")
        print(f"Text: {transcript.text}")
        print(f"Confidence: {transcript.confidence:.2f}")
        print(f"Is Final: {transcript.is_final}")
        
        if transcript.start_time != 0 or transcript.end_time != 0:
            print(f"Time: {transcript.start_time:.2f}s - {transcript.end_time:.2f}s")
        
        print("======================")


async def api_http_transcription(file_path, server_url="http://localhost:8000"):
    """Transcribe a file using the HTTP API endpoint."""
    import aiohttp
    from aiohttp import FormData
    
    print(f"🌐 Transcribing file via HTTP API: {file_path}")
    print(f"Server URL: {server_url}/api/transcribe")
    
    # Create form data for the file upload
    data = FormData()
    data.add_field('file', 
                  open(file_path, 'rb'),
                  filename=os.path.basename(file_path),
                  content_type='audio/mpeg')
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{server_url}/api/transcribe", data=data) as response:
            if response.status != 200:
                print(f"❌ Error: HTTP {response.status} - {await response.text()}")
                return
            
            result = await response.json()
            
            print("\n📝 API Transcription Results:")
            print("======================")
            for i, transcript in enumerate(result, 1):
                print(f"Transcript #{i}:")
                print(f"Text: {transcript['transcript']}")
                print(f"Confidence: {transcript['confidence']:.2f}")
                print(f"Is Final: {transcript['is_final']}")
                
                if transcript['metadata'] and ('start_time' in transcript['metadata'] or 'end_time' in transcript['metadata']):
                    if transcript['metadata']['start_time'] != 0 or transcript['metadata']['end_time'] != 0:
                        print(f"Time: {transcript['metadata']['start_time']:.2f}s - {transcript['metadata']['end_time']:.2f}s")
                
                print("======================")


async def api_websocket_transcription(file_path, server_url="ws://localhost:8000"):
    """Stream audio file to the WebSocket API endpoint."""
    import aiohttp
    from aiohttp import WSMsgType
    
    print(f"🌐 Streaming file via WebSocket API: {file_path}")
    print(f"Server URL: {server_url}/api/stream")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(f"{server_url}/api/stream") as ws:
                print("📶 Connected to WebSocket")
                
                # Listen for messages from server
                async def receiver():
                    async for msg in ws:
                        if msg.type == WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            if "transcript" in data:
                                is_final = "✓" if data["is_final"] else "…"
                                confidence = data["confidence"] if "confidence" in data else 0.0
                                print(f"[{is_final}] ({confidence:.2f}) {data['transcript']}")
                            elif "status" in data:
                                print(f"📢 Status: {data['status']}")
                            elif "error" in data:
                                print(f"❌ Error: {data['error']}")
                            else:
                                print(f"📩 Message: {data}")
                        elif msg.type == WSMsgType.ERROR:
                            print(f"❌ WebSocket error: {msg.data}")
                            break
                
                # Start the receiver in the background
                receiver_task = asyncio.create_task(receiver())
                
                # Send command to start transcription with appropriate format
                await ws.send_json({
                    "command": "start",
                    "audio_format": {
                        "mimetype": "audio/mpeg",  # MP3 format
                        "sample_rate": 48000,  # 48kHz for this MP3 file
                        "channels": 2  # Stereo audio
                    }
                })
                
                # Read and send the file in chunks
                chunk_size = 4096  # 4KB chunks
                with open(file_path, "rb") as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        await ws.send_bytes(chunk)
                        await asyncio.sleep(0.05)  # Simulating real-time streaming
                
                # Let the last transcriptions come in
                print("🔚 File sent, waiting for final results...")
                await asyncio.sleep(2)
                
                # Stop transcription
                await ws.send_json({"command": "stop"})
                
                # Cancel the receiver task
                receiver_task.cancel()
                try:
                    await receiver_task
                except asyncio.CancelledError:
                    pass
                
                print("✅ WebSocket transcription complete")
    
    except Exception as e:
        print(f"❌ Error in WebSocket transcription: {str(e)}")


async def main():
    """Main function to parse arguments and run the demo."""
    parser = argparse.ArgumentParser(description="Truth Checker Demo")
    parser.add_argument("file", help="Path to the audio file to transcribe")
    parser.add_argument("--mode", choices=["direct", "http", "websocket"], default="direct",
                      help="Transcription mode: direct, http, or websocket (default: direct)")
    parser.add_argument("--server", default="http://localhost:8000",
                      help="Server URL (default: http://localhost:8000)")
    parser.add_argument("--verbose", "-v", action="store_true",
                      help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Check if the file exists
    if not os.path.isfile(args.file):
        print(f"❌ File not found: {args.file}")
        return 1
    
    # Run the selected mode
    try:
        if args.mode == "direct":
            await direct_transcription(args.file)
        elif args.mode == "http":
            server_url = args.server
            await api_http_transcription(args.file, server_url)
        elif args.mode == "websocket":
            # Convert HTTP URL to WebSocket URL if needed
            server_url = args.server
            if server_url.startswith("http://"):
                server_url = f"ws://{server_url[7:]}"
            elif server_url.startswith("https://"):
                server_url = f"wss://{server_url[8:]}"
            
            await api_websocket_transcription(args.file, server_url)
        else:
            print(f"❌ Invalid mode: {args.mode}")
            return 1
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 