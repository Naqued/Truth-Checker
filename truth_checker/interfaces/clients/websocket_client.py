"""WebSocket client for streaming audio to the API server."""

import asyncio
import json
import logging
import time
import os
from typing import Callable, Dict, List, Optional, Any

import aiohttp
import wave

from truth_checker.domain.models import Transcript

logger = logging.getLogger(__name__)


class WebSocketClient:
    """Client for streaming audio to a WebSocket server and receiving transcriptions."""
    
    def __init__(
        self, 
        server_url: str = "ws://localhost:8000/api/stream", 
        chunk_size: int = 4096,
        audio_format: Optional[Dict[str, Any]] = None
    ):
        """Initialize the WebSocket client.
        
        Args:
            server_url: URL of the WebSocket server
            chunk_size: Size of audio chunks to send at once
            audio_format: Audio format parameters (mimetype, encoding, sample_rate, channels)
        """
        self.server_url = server_url
        self.chunk_size = chunk_size
        self._running = False
        self._websocket = None
        self._session = None
        self._send_task = None
        self._receive_task = None
        self.audio_queue = asyncio.Queue()
        self.transcript_callbacks: List[Callable[[Transcript], None]] = []
        self.transcripts: List[Transcript] = []
        
        # Default audio format
        self.audio_format = {
            "mimetype": "audio/raw",
            "encoding": "linear16",
            "sample_rate": 16000,
            "channels": 1
        }
        
        # Update with user-provided format if specified
        if audio_format:
            self.audio_format.update(audio_format)
            
    async def connect(self) -> None:
        """Connect to the WebSocket server.
        
        Raises:
            ConnectionError: If connection fails
        """
        if self._websocket:
            logger.warning("Already connected to WebSocket server")
            return
            
        try:
            # Create a new session if needed
            if not self._session:
                self._session = aiohttp.ClientSession()
                
            # Connect to the WebSocket server
            self._websocket = await self._session.ws_connect(self.server_url)
            
            # Wait for welcome message
            msg = await self._websocket.receive()
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                if data.get("status") == "connected":
                    logger.info(f"Connected to WebSocket server at {self.server_url}")
                    
                    # Log supported formats if available
                    if "supported_formats" in data:
                        logger.info(f"Server supports formats: {', '.join(data['supported_formats'])}")
                else:
                    logger.warning(f"Unexpected welcome message: {data}")
            else:
                logger.warning(f"Unexpected message type: {msg.type}")
                
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            if self._session:
                await self._session.close()
                self._session = None
            raise ConnectionError(f"Failed to connect to WebSocket server: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from the WebSocket server."""
        if not self._websocket:
            logger.warning("Not connected to WebSocket server")
            return
            
        try:
            # Close the WebSocket connection
            await self._websocket.close()
            
            # Close the session
            if self._session:
                await self._session.close()
                self._session = None
                
            self._websocket = None
            logger.info("Disconnected from WebSocket server")
        except Exception as e:
            logger.error(f"Error disconnecting from WebSocket server: {e}")
            self._websocket = None
            self._session = None
    
    async def start(self) -> None:
        """Start streaming audio to the server and receiving transcriptions.
        
        Raises:
            ConnectionError: If not connected or connection fails
        """
        if self._running:
            logger.warning("WebSocket client is already running")
            return
            
        try:
            # Connect if not already connected
            if not self._websocket:
                await self.connect()
                
            self._running = True
            
            # Send start command with audio format
            await self._websocket.send_json({
                "command": "start",
                "audio_format": self.audio_format
            })
            
            # Wait for confirmation
            try:
                msg = await asyncio.wait_for(self._websocket.receive(), timeout=5.0)
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data.get("status") == "started":
                        logger.info("Server started transcription")
                    elif "error" in data:
                        logger.error(f"Error starting transcription: {data['error']}")
            except asyncio.TimeoutError:
                logger.warning("No start confirmation received from server, continuing anyway")
            
            # Start sending and receiving in the background
            self._send_task = asyncio.create_task(self._send_audio())
            self._receive_task = asyncio.create_task(self._receive_transcripts())
            
            logger.info("Started WebSocket audio streaming")
        except Exception as e:
            logger.error(f"Failed to start WebSocket client: {e}")
            await self.disconnect()
            self._running = False
            raise
    
    async def stop(self) -> None:
        """Stop streaming audio and disconnect."""
        if not self._running:
            logger.warning("WebSocket client is not running")
            return
            
        try:
            self._running = False
            
            # Send stop command
            if self._websocket:
                await self._websocket.send_json({"command": "stop"})
            
            # Cancel background tasks
            if self._send_task and not self._send_task.done():
                self._send_task.cancel()
                try:
                    await self._send_task
                except asyncio.CancelledError:
                    pass
                
            if self._receive_task and not self._receive_task.done():
                self._receive_task.cancel()
                try:
                    await self._receive_task
                except asyncio.CancelledError:
                    pass
            
            # Disconnect from server
            await self.disconnect()
            
            logger.info("Stopped WebSocket audio streaming")
        except Exception as e:
            logger.error(f"Error stopping WebSocket client: {e}")
            raise
    
    def register_transcript_callback(self, callback: Callable[[Transcript], None]) -> None:
        """Register a callback for transcript events.
        
        Args:
            callback: Function to call when a transcript is received
        """
        self.transcript_callbacks.append(callback)
        logger.debug(f"Registered transcript callback")
    
    def get_transcripts(self) -> List[Transcript]:
        """Get all received transcripts.
        
        Returns:
            List[Transcript]: List of received transcripts
        """
        return self.transcripts.copy()
    
    async def send_audio_data(self, audio_data: bytes) -> None:
        """Send audio data to the server.
        
        Args:
            audio_data: Raw audio bytes to send
        """
        if not self._running:
            logger.warning("Cannot send audio - WebSocket client is not running")
            return
            
        await self.audio_queue.put(audio_data)
    
    async def stream_wav_file(self, file_path: str, real_time: bool = True) -> None:
        """Stream an audio file to the server.
        
        Args:
            file_path: Path to the WAV file to stream
            real_time: If True, stream at real-time rate; if False, stream as fast as possible
        """
        try:
            # Detect file extension and set appropriate audio format
            file_ext = os.path.splitext(file_path.lower())[1]
            
            # Handle WAV files
            if file_ext == ".wav":
                with wave.open(file_path, 'rb') as wav_file:
                    # Get file parameters
                    channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
                    frame_rate = wav_file.getframerate()
                    n_frames = wav_file.getnframes()
                    
                    # Update audio format based on WAV file properties
                    self.audio_format.update({
                        "mimetype": "audio/wav",
                        "channels": channels,
                        "sample_rate": frame_rate,
                        "encoding": f"linear{sample_width * 8}"  # e.g., linear16 for 16-bit
                    })
                    
                    logger.info(f"Streaming WAV file: {file_path}")
                    logger.info(f"  Channels: {channels}")
                    logger.info(f"  Sample width: {sample_width} bytes")
                    logger.info(f"  Frame rate: {frame_rate} Hz")
                    logger.info(f"  Frames: {n_frames}")
                    
                    # Calculate chunk duration
                    frames_per_chunk = self.chunk_size // (channels * sample_width)
                    chunk_duration = frames_per_chunk / frame_rate  # seconds
                    
                    # Read and send chunks
                    bytes_sent = 0
                    start_time = time.time()
                    
                    while True:
                        # Read chunk
                        chunk = wav_file.readframes(frames_per_chunk)
                        if not chunk:
                            break
                            
                        # Send chunk
                        await self.send_audio_data(chunk)
                        bytes_sent += len(chunk)
                        
                        # Sleep to simulate real-time streaming if requested
                        if real_time:
                            elapsed = time.time() - start_time
                            expected = bytes_sent / (channels * sample_width * frame_rate)
                            if elapsed < expected:
                                await asyncio.sleep(expected - elapsed)
                    
                    logger.info(f"Finished streaming WAV file: {bytes_sent} bytes sent")
            
            # For other audio formats, stream the raw file data
            else:
                # Set mimetype based on file extension
                mime_type_map = {
                    ".mp3": "audio/mpeg",
                    ".ogg": "audio/ogg",
                    ".oga": "audio/ogg",
                    ".flac": "audio/flac",
                    ".webm": "audio/webm",
                    ".m4a": "audio/mp4",
                    ".aac": "audio/aac",
                    ".pcm": "audio/pcm",
                    ".raw": "audio/raw",
                }
                
                # Update audio format
                self.audio_format["mimetype"] = mime_type_map.get(file_ext, "application/octet-stream")
                
                logger.info(f"Streaming audio file: {file_path} (format: {self.audio_format['mimetype']})")
                
                # Read the full file and send it
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                    
                # Send in chunks
                total_bytes = len(file_data)
                bytes_sent = 0
                start_time = time.time()
                
                while bytes_sent < total_bytes:
                    # Get next chunk
                    end_pos = min(bytes_sent + self.chunk_size, total_bytes)
                    chunk = file_data[bytes_sent:end_pos]
                    
                    # Send chunk
                    await self.send_audio_data(chunk)
                    
                    # Update position
                    chunk_size = len(chunk)
                    bytes_sent += chunk_size
                    
                    # Sleep if real-time streaming is requested
                    # This is approximate as we don't know actual duration without decoding
                    if real_time:
                        # Estimate duration based on content size (very approximate)
                        # For MP3, ~1MB is about 1 minute of audio at 128kbps
                        duration_estimate = chunk_size / (total_bytes / 60) if total_bytes > 0 else 0.1
                        await asyncio.sleep(duration_estimate)
                
                logger.info(f"Finished streaming audio file: {bytes_sent} bytes sent")
                
        except Exception as e:
            logger.error(f"Error streaming audio file: {e}")
            raise
    
    async def _send_audio(self) -> None:
        """Send audio data from the queue to the server."""
        try:
            while self._running:
                # Get audio data from the queue
                try:
                    audio_data = await asyncio.wait_for(self.audio_queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    # No data available, continue waiting
                    continue
                    
                # Send to server
                if self._websocket and audio_data:
                    await self._websocket.send_bytes(audio_data)
                    logger.debug(f"Sent {len(audio_data)} bytes of audio data")
                    self.audio_queue.task_done()
                    
        except asyncio.CancelledError:
            # This is expected when stopping
            pass
        except Exception as e:
            logger.error(f"Error sending audio data: {e}")
            self._running = False
            raise
    
    async def _receive_transcripts(self) -> None:
        """Receive and process transcripts from the server."""
        try:
            while self._running and self._websocket:
                # Receive message from server
                try:
                    msg = await asyncio.wait_for(self._websocket.receive(), timeout=0.5)
                except asyncio.TimeoutError:
                    # No message available, continue waiting
                    continue
                    
                # Process the message based on its type
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        
                        # Check if this is a transcript
                        if "transcript" in data:
                            # Create transcript object
                            transcript = Transcript(
                                text=data["transcript"],
                                confidence=data["confidence"],
                                is_final=data["is_final"],
                                start_time=data.get("metadata", {}).get("start_time", 0),
                                end_time=data.get("metadata", {}).get("end_time", 0)
                            )
                            
                            # Store the transcript
                            self.transcripts.append(transcript)
                            
                            # Call registered callbacks
                            for callback in self.transcript_callbacks:
                                try:
                                    callback(transcript)
                                except Exception as e:
                                    logger.error(f"Error in transcript callback: {e}")
                        elif "error" in data:
                            logger.error(f"Error from server: {data['error']}")
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Received invalid JSON: {msg.data}")
                    except Exception as e:
                        logger.error(f"Error processing transcript message: {e}")
                        
                elif msg.type == aiohttp.WSMsgType.BINARY:
                    logger.warning(f"Received unexpected binary message: {len(msg.data)} bytes")
                    
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {msg.data}")
                    self._running = False
                    
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.info("WebSocket connection closed by server")
                    self._running = False
                    
        except asyncio.CancelledError:
            # This is expected when stopping
            pass
        except Exception as e:
            logger.error(f"Error receiving transcripts: {e}")
            self._running = False
            raise


async def upload_file(server_url: str, file_path: str) -> List[Dict[str, Any]]:
    """Upload an audio file to the server for transcription.
    
    Args:
        server_url: URL of the server's file upload endpoint
        file_path: Path to the audio file to upload
        
    Returns:
        List[Dict[str, Any]]: List of transcription results
        
    Raises:
        Exception: If upload or transcription fails
    """
    try:
        async with aiohttp.ClientSession() as session:
            with open(file_path, "rb") as f:
                # Determine content type based on file extension
                file_ext = os.path.splitext(file_path.lower())[1]
                
                # Map file extensions to MIME types
                content_type_map = {
                    ".wav": "audio/wav",
                    ".mp3": "audio/mpeg",
                    ".ogg": "audio/ogg",
                    ".oga": "audio/ogg",
                    ".flac": "audio/flac",
                    ".webm": "audio/webm",
                    ".m4a": "audio/mp4",
                    ".aac": "audio/aac",
                    ".pcm": "audio/pcm",
                    ".raw": "audio/raw",
                }
                
                # Get content type from map or use default
                content_type = content_type_map.get(file_ext, "application/octet-stream")
                
                # Create form data with the file
                form_data = aiohttp.FormData()
                form_data.add_field(
                    "file", 
                    f.read(),
                    filename=os.path.basename(file_path),
                    content_type=content_type
                )
                
                # Upload the file
                logger.info(f"Uploading file {file_path} to {server_url}")
                logger.debug(f"Content type: {content_type}")
                
                async with session.post(server_url, data=form_data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Upload failed: {response.status} - {error_text}")
                    
                    # Parse the response
                    results = await response.json()
                    logger.info(f"File uploaded successfully. Received {len(results)} transcription results")
                    return results
                    
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise 