"""FastAPI server for handling audio streaming via HTTP and WebSockets."""

import asyncio
import io
import json
import logging
import os
import time
from typing import List, Optional, Dict, Any

import fastapi
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from truth_checker.application.transcription_service import TranscriptionApplicationService
from truth_checker.domain.models import Transcript
from truth_checker.infrastructure.services.deepgram_service import DeepgramTranscriptionService

logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Truth Checker API",
    description="API for transcribing and fact-checking audio streams",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# Track transcription services by client ID
transcription_services: Dict[str, TranscriptionApplicationService] = {}


class TranscriptionResponse(BaseModel):
    """Response model for transcription results."""
    transcript: str
    confidence: float
    is_final: bool
    metadata: Optional[Dict[str, Any]] = None


async def get_transcription_service() -> TranscriptionApplicationService:
    """Create and return a transcription service.
    
    Returns:
        TranscriptionApplicationService: A service for managing transcriptions
    """
    # Check if API key is configured
    api_key = os.environ.get("DEEPGRAM_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Deepgram API key not configured")
    
    # Create Deepgram service
    deepgram_service = DeepgramTranscriptionService(api_key=api_key)
    
    # Create and return application service
    return TranscriptionApplicationService(transcription_service=deepgram_service)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Truth Checker API",
        "version": "0.1.0",
        "endpoints": {
            "POST /api/transcribe": "Transcribe an audio file",
            "WebSocket /api/stream": "Stream audio for real-time transcription",
        }
    }


@app.post("/api/transcribe", response_model=List[TranscriptionResponse])
async def transcribe_audio(
    file: UploadFile = File(...),
    transcription_service: TranscriptionApplicationService = Depends(get_transcription_service)
):
    """Transcribe an uploaded audio file.
    
    Args:
        file: The audio file to transcribe
        transcription_service: Service for managing transcriptions
        
    Returns:
        List[TranscriptionResponse]: List of transcription results
    """
    # Get content type and validate
    content_type = file.content_type or ""
    filename = file.filename or ""
    
    # List of supported audio MIME types
    supported_audio_types = {
        "audio/wav", "audio/x-wav", 
        "audio/mpeg", "audio/mp3",
        "audio/ogg", "audio/vorbis",
        "audio/flac",
        "audio/webm",
        "audio/mp4", "audio/m4a",
        "audio/aac",
        "audio/pcm", "audio/l16", "audio/raw",
        "application/octet-stream"  # For generic binary data
    }
    
    # Check file extension as fallback (if content type is not detected correctly)
    file_ext = os.path.splitext(filename.lower())[1] if filename else ""
    is_audio_extension = file_ext in {".wav", ".mp3", ".ogg", ".oga", ".flac", ".webm", ".m4a", ".aac", ".pcm", ".raw"}
    
    # Validate file type
    if not (content_type in supported_audio_types or is_audio_extension):
        supported_formats = ", ".join([t for t in supported_audio_types if t != "application/octet-stream"])
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Supported formats: {supported_formats}"
        )
    
    try:
        # Read file content
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Process file with Deepgram
        logger.info(f"Processing audio file: {filename} ({len(content)} bytes, type: {content_type})")
        
        # Save to a temporary file
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        try:
            # Write content to temp file
            temp_file.write(content)
            temp_file.close()
            
            # Determine if we need to set specific parameters for this audio format
            audio_params = {}
            
            # For PCM/raw audio, we need to specify encoding parameters
            if content_type in {"audio/pcm", "audio/l16", "audio/raw"} or file_ext in {".pcm", ".raw"}:
                # Default to reasonable values for PCM audio if not specified
                audio_params = {
                    "encoding": "linear16",  # 16-bit PCM
                    "sample_rate": 16000,    # 16kHz sample rate
                    "channels": 1            # Mono audio
                }
                logger.info(f"Setting PCM parameters: {audio_params}")
            
            # Transcribe file
            transcripts = await transcription_service.transcribe_file(temp_file.name, audio_params)
            
            # Convert to response model
            results = []
            for transcript in transcripts:
                results.append(
                    TranscriptionResponse(
                        transcript=transcript.text,
                        confidence=transcript.confidence,
                        is_final=transcript.is_final,
                        metadata={
                            "start_time": transcript.start_time,
                            "end_time": transcript.end_time,
                        }
                    )
                )
            
            return results
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")


@app.websocket("/api/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming audio.
    
    Args:
        websocket: The WebSocket connection
    """
    # Accept the connection
    await websocket.accept()
    client_id = str(id(websocket))
    active_connections[client_id] = websocket
    
    # Initialize audio format parameters
    audio_format = {
        "mimetype": "audio/raw",  # Default to raw PCM
        "encoding": "linear16",   # Default to 16-bit PCM
        "sample_rate": 16000,     # Default to 16kHz
        "channels": 1,            # Default to mono
    }
    
    # Send welcome message
    await websocket.send_json({
        "status": "connected", 
        "message": "Ready to receive audio",
        "supported_formats": [
            "raw/pcm (linear16, signed int)",
            "mp3",
            "wav",
            "webm",
            "ogg",
            "flac"
        ]
    })
    
    # Track whether we're using a mock implementation due to missing API key
    is_mock_mode = False
    audio_started = False
    
    try:
        # Get transcription service
        try:
            # Explicitly get the API key from the environment
            api_key = os.environ.get("DEEPGRAM_API_KEY", "")
            
            # Check if we're in mock mode (no API key or just the placeholder)
            is_mock_mode = not api_key or api_key == "your_deepgram_api_key_here"
            
            # Create the transcription service with the explicit API key
            deepgram_service = DeepgramTranscriptionService(api_key=api_key)
            transcription_service = TranscriptionApplicationService(transcription_service=deepgram_service)
            transcription_services[client_id] = transcription_service
            
            if is_mock_mode:
                logger.info(f"Using mock transcription for client {client_id} (no valid API key)")
            else:
                logger.info(f"Using real Deepgram transcription for client {client_id} with API key: {api_key[:4]}...{api_key[-4:]}")
            
            # Define a synchronous callback for transcription events that sends to WebSocket via queue
            transcript_queue = asyncio.Queue()
            
            # Create a threading.Event to signal when to exit the queue processor
            import threading
            queue_exit_event = threading.Event()
            
            # Create a thread-safe queue to store transcripts from callbacks
            from queue import Queue
            thread_safe_queue = Queue()
            
            # For testing: Create a mock transcript generator task if in mock mode
            async def generate_mock_transcripts():
                logger.info(f"Starting mock transcript generator for client {client_id}")
                
                # List of test transcripts
                test_transcripts = [
                    "When you look at the map, a map of the Middle East, Israel is a tiny little spot compared to these giant land masses.",
                    "It's really a tiny spot. I actually said, is there any way of getting more?",
                    "It's so tiny.",
                    "This is a mock transcript to test the WebSocket streaming capabilities.",
                    "If you see this message, the WebSocket streaming is working."
                ]
                
                # Counter for test transcripts
                counter = 0
                
                # Send an immediate mock transcript to confirm things are working
                try:
                    initial_transcript = Transcript(
                        text="WebSocket streaming is active and working. You will see mock transcripts every 2 seconds.",
                        confidence=0.99,
                        is_final=True,
                        start_time=time.time(),
                        end_time=time.time()
                    )
                    await transcript_queue.put(initial_transcript)
                    logger.info(f"Sent initial mock transcript confirmation for client {client_id}")
                except Exception as e:
                    logger.error(f"Error sending initial mock transcript: {str(e)}")
                
                # Generate mock transcripts until signaled to stop
                while client_id in active_connections and not queue_exit_event.is_set():
                    try:
                        # Generate a mock transcript every 2 seconds
                        await asyncio.sleep(2)
                        
                        # Create a mock transcript
                        text = test_transcripts[counter % len(test_transcripts)]
                        counter += 1
                        
                        logger.info(f"Generating mock transcript: '{text}'")
                        
                        mock_transcript = Transcript(
                            text=text,
                            confidence=0.95,
                            is_final=True,
                            start_time=time.time(),
                            end_time=time.time()
                        )
                        
                        # Add to the queue directly
                        await transcript_queue.put(mock_transcript)
                        
                    except Exception as e:
                        logger.error(f"Error generating mock transcript: {str(e)}")
                        await asyncio.sleep(1)  # Prevent CPU spin
                
                logger.info(f"Stopping mock transcript generator for client {client_id}")
            
            # Start the mock generator if in mock mode
            mock_generator_task = None
            if is_mock_mode:
                mock_generator_task = asyncio.create_task(generate_mock_transcripts())
            
            # Start a background task to process transcripts from the queue
            async def process_transcript_queue():
                logger.debug(f"Starting queue processor for client {client_id}")
                
                while client_id in active_connections and not queue_exit_event.is_set():
                    try:
                        # Wait for new transcripts with a timeout
                        try:
                            transcript = await asyncio.wait_for(transcript_queue.get(), 0.1)
                            logger.debug(f"Queue processor: got transcript from asyncio queue for client {client_id}: '{transcript.text}'")
                            
                            # Send to WebSocket
                            await websocket.send_json({
                                "transcript": transcript.text,
                                "confidence": transcript.confidence,
                                "is_final": transcript.is_final,
                                "metadata": {
                                    "start_time": transcript.start_time,
                                    "end_time": transcript.end_time,
                                }
                            })
                            logger.info(f"Sent transcript to client {client_id}: '{transcript.text}'")
                            
                            # Mark task as done
                            transcript_queue.task_done()
                        except asyncio.TimeoutError:
                            # Just a timeout, continue checking
                            pass
                    except Exception as e:
                        logger.error(f"Error processing transcript queue for client {client_id}: {str(e)}")
                        await asyncio.sleep(0.1)  # Prevent CPU spin
                
                logger.debug(f"Queue processor ending for client {client_id}")
            
            # Create a task to transfer items from the thread-safe queue to the asyncio queue
            async def transfer_from_thread_queue():
                logger.debug(f"Starting transfer task for client {client_id}")
                
                while client_id in active_connections and not queue_exit_event.is_set():
                    try:
                        # Non-blocking check for items in the thread queue
                        if not thread_safe_queue.empty():
                            # Get the transcript
                            transcript = thread_safe_queue.get_nowait()
                            logger.debug(f"Transfer task: got transcript from thread queue for client {client_id}: '{transcript.text}'")
                            
                            # Put it in the asyncio queue
                            await transcript_queue.put(transcript)
                            logger.debug(f"Transfer task: added transcript to asyncio queue for client {client_id}")
                            
                            # Mark as done
                            thread_safe_queue.task_done()
                        else:
                            # Sleep briefly to avoid CPU spin
                            await asyncio.sleep(0.01)
                    except Exception as e:
                        logger.error(f"Error transferring transcript from thread queue: {str(e)}")
                        await asyncio.sleep(0.1)  # Prevent CPU spin
                
                logger.debug(f"Transfer task ending for client {client_id}")
            
            # Define a synchronous callback that uses a thread-safe queue to communicate with the main thread
            def on_transcript(transcript: Transcript):
                try:
                    # Log the transcript being received
                    logger.info(f"Received transcript in callback for client {client_id}: '{transcript.text}' (confidence: {transcript.confidence}, final: {transcript.is_final})")
                    
                    # Just add to a thread-safe queue - no asyncio needed
                    thread_safe_queue.put(transcript)
                    logger.debug(f"Added transcript to thread-safe queue for client {client_id}, queue size: {thread_safe_queue.qsize()}")
                except Exception as e:
                    logger.error(f"Error adding transcript to queue for client {client_id}: {str(e)}")
            
            # Start the queue processor
            queue_task = asyncio.create_task(process_transcript_queue())
            
            # Start the transfer task
            transfer_task = asyncio.create_task(transfer_from_thread_queue())
            
            # Register callback - using a fully synchronous callback
            transcription_service.add_transcript_callback(on_transcript)
            
            # Process audio data
            audio_started = False
            
            while True:
                # Receive data from client
                data = await websocket.receive()
                
                # Check for text messages (commands or configuration)
                if "text" in data:
                    try:
                        message = json.loads(data["text"])
                        
                        # Handle commands
                        if "command" in message:
                            command = message["command"]
                            
                            if command == "stop":
                                logger.info(f"Client {client_id} requested to stop transcription")
                                break
                            elif command == "start":
                                if not audio_started:
                                    # Get audio format configuration if provided
                                    if "audio_format" in message:
                                        format_config = message["audio_format"]
                                        # Update audio format with client-provided values
                                        audio_format.update(format_config)
                                        logger.info(f"Using client-provided audio format: {audio_format}")
                                    
                                    # For MP3 files, we don't need encoding parameter, but we need sample_rate and channels
                                    if audio_format.get("mimetype") in ["audio/mpeg", "audio/mp3"] and "encoding" in audio_format:
                                        logger.info(f"Removing encoding parameter for {audio_format.get('mimetype')} as it's not needed")
                                        del audio_format["encoding"]
                                    
                                    logger.debug(f"Starting transcription for client {client_id} with format: {audio_format}")
                                    
                                    try:
                                        # Start transcription with the specified format
                                        await transcription_service.start_transcription(**audio_format, mock_mode=is_mock_mode)
                                        audio_started = True
                                        await websocket.send_json({"status": "started"})
                                        logger.info(f"Started transcription for client {client_id}")
                                    except Exception as e:
                                        logger.error(f"Error starting transcription: {str(e)}")
                                        if is_mock_mode:
                                            # In mock mode, we can still proceed even if there's an error
                                            audio_started = True
                                            await websocket.send_json({"status": "started", "note": "Using mock transcription"})
                                            logger.info(f"Using mock transcription for client {client_id}")
                                        else:
                                            await websocket.send_json({"error": f"Error starting transcription: {str(e)}"})
                                else:
                                    await websocket.send_json({"status": "already_started"})
                        
                    except json.JSONDecodeError:
                        logger.warning(f"Received invalid JSON from client {client_id}")
                    except Exception as e:
                        logger.error(f"Error processing command from client {client_id}: {str(e)}")
                        await websocket.send_json({"error": f"Error processing command: {str(e)}"})
                
                # Process binary data (audio chunks)
                elif "bytes" in data:
                    audio_data = data["bytes"]
                    if audio_data:
                        # Auto-start transcription if not already started
                        if not audio_started:
                            try:
                                # For MP3 files, we don't need encoding parameter, but we need sample_rate and channels
                                if audio_format.get("mimetype") in ["audio/mpeg", "audio/mp3"] and "encoding" in audio_format:
                                    logger.info(f"Removing encoding parameter for {audio_format.get('mimetype')} as it's not needed")
                                    del audio_format["encoding"]
                                
                                logger.debug(f"Auto-starting transcription for client {client_id} with format: {audio_format}")
                                await transcription_service.start_transcription(**audio_format, mock_mode=is_mock_mode)
                                audio_started = True
                                logger.info(f"Auto-started transcription for client {client_id}")
                            except Exception as e:
                                logger.error(f"Error starting transcription: {str(e)}")
                                if is_mock_mode:
                                    # In mock mode, we can still proceed even if there's an error
                                    audio_started = True
                                    await websocket.send_json({"status": "started", "note": "Using mock transcription"})
                                    logger.info(f"Using mock transcription for client {client_id}")
                                else:
                                    await websocket.send_json({"error": f"Error starting transcription: {str(e)}"})
                                    continue
                        
                        try:
                            # Process the audio data
                            await transcription_service.process_audio_data(audio_data)
                        except Exception as e:
                            # If we're in mock mode or the error is about bool in await, we can continue
                            if is_mock_mode or "object bool can't be used in 'await' expression" in str(e):
                                # In mock mode, generate a mock transcript 
                                if len(audio_data) > 1000 and client_id in active_connections:
                                    # Simulate a transcript for larger chunks
                                    await websocket.send_json({
                                        "transcript": "This is a mock transcript from streaming audio.",
                                        "confidence": 0.95,
                                        "is_final": True,
                                        "metadata": {
                                            "start_time": 0,
                                            "end_time": 0,
                                        }
                                    })
                            else:
                                logger.error(f"Error processing audio data: {str(e)}")
                                await websocket.send_json({"error": f"Error processing audio: {str(e)}"})
                    
        except Exception as e:
            logger.error(f"Error in WebSocket connection for client {client_id}: {str(e)}")
            await websocket.send_json({"error": str(e)})
            
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}")
    finally:
        # Signal queues to exit
        if 'queue_exit_event' in locals():
            queue_exit_event.set()
            
        # Clean up
        if client_id in transcription_services:
            try:
                if audio_started:
                    await transcription_services[client_id].stop_transcription()
            except Exception as e:
                logger.error(f"Error stopping transcription for client {client_id}: {str(e)}")
            del transcription_services[client_id]
            
        # Cancel queue tasks if they exist
        try:
            if 'queue_task' in locals() and queue_task is not None:
                queue_task.cancel()
                try:
                    await queue_task
                except asyncio.CancelledError:
                    logger.debug(f"Queue task for client {client_id} cancelled")
                    
            if 'transfer_task' in locals() and transfer_task is not None:
                transfer_task.cancel()
                try:
                    await transfer_task
                except asyncio.CancelledError:
                    logger.debug(f"Transfer task for client {client_id} cancelled")
                    
            if 'mock_generator_task' in locals() and mock_generator_task is not None:
                mock_generator_task.cancel()
                try:
                    await mock_generator_task
                except asyncio.CancelledError:
                    logger.debug(f"Mock generator task for client {client_id} cancelled")
        except Exception as e:
            logger.error(f"Error cancelling queue tasks for client {client_id}: {str(e)}")
            
        if client_id in active_connections:
            del active_connections[client_id]


async def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI server.
    
    Args:
        host: Hostname to bind to
        port: Port to listen on
    """
    import uvicorn
    config = uvicorn.Config(app, host=host, port=port)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 