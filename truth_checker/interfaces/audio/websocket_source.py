"""WebSocket client for streaming audio to the API server."""

import asyncio
import json
import logging
import time
from typing import Callable, Optional

import websockets

from truth_checker.interfaces.audio.audio_interface import AudioSource

logger = logging.getLogger(__name__)


class WebSocketAudioClient(AudioSource):
    """Client for streaming audio to a WebSocket server and receiving transcriptions."""
    
    def __init__(self, server_url: str = "ws://localhost:8000/api/stream", chunk_size: int = 1024):
        """Initialize the WebSocket client.
        
        Args:
            server_url: URL of the WebSocket server
            chunk_size: Size of audio chunks to read at once
        """
        self.server_url = server_url
        self.chunk_size = chunk_size
        self._running = False
        self._websocket = None
        self._send_task = None
        self._receive_task = None
        self.audio_queue = asyncio.Queue()
        self.transcript_handlers = []
    
    async def connect(self) -> None:
        """Connect to the WebSocket server."""
        if self._websocket:
            logger.warning("Already connected to WebSocket server")
            return
            
        try:
            self._websocket = await websockets.connect(self.server_url)
            logger.info(f"Connected to WebSocket server at {self.server_url}")
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from the WebSocket server."""
        if not self._websocket:
            logger.warning("Not connected to WebSocket server")
            return
            
        try:
            await self._websocket.close()
            self._websocket = None
            logger.info("Disconnected from WebSocket server")
        except Exception as e:
            logger.error(f"Error disconnecting from WebSocket server: {e}")
            self._websocket = None
    
    async def start(self) -> None:
        """Start streaming audio to the server and receiving transcriptions."""
        if self._running:
            logger.warning("WebSocket client is already running")
            return
            
        try:
            # Connect if not already connected
            if not self._websocket:
                await self.connect()
                
            self._running = True
            
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
    
    @property
    def is_running(self) -> bool:
        """Check if the WebSocket client is running."""
        return self._running
    
    def register_transcript_handler(self, handler: Callable[[dict], None]) -> None:
        """Register a function to be called for each transcript received.
        
        Args:
            handler: Function that takes a transcript object as its argument
        """
        self.transcript_handlers.append(handler)
        logger.debug(f"Registered transcript handler: {handler.__name__}")
    
    async def send_audio_data(self, audio_data: bytes) -> None:
        """Send audio data to the server.
        
        Args:
            audio_data: Raw audio bytes to send
        """
        if not self._running:
            logger.warning("Cannot send audio - WebSocket client is not running")
            return
            
        await self.audio_queue.put(audio_data)
    
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
                    await self._websocket.send(audio_data)
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
                    message = await asyncio.wait_for(self._websocket.recv(), timeout=0.5)
                except asyncio.TimeoutError:
                    # No message available, continue waiting
                    continue
                    
                # Parse and process the message
                try:
                    if isinstance(message, str):
                        transcript = json.loads(message)
                    else:
                        # Assuming binary message is JSON
                        transcript = json.loads(message.decode("utf-8"))
                        
                    logger.debug(f"Received transcript: {transcript}")
                    
                    # Call handlers
                    for handler in self.transcript_handlers:
                        try:
                            handler(transcript)
                        except Exception as e:
                            logger.error(f"Error in transcript handler {handler.__name__}: {e}")
                            
                except json.JSONDecodeError:
                    logger.warning(f"Received non-JSON message: {message}")
                except Exception as e:
                    logger.error(f"Error processing transcript message: {e}")
                    
        except asyncio.CancelledError:
            # This is expected when stopping
            pass
        except Exception as e:
            logger.error(f"Error receiving transcripts: {e}")
            self._running = False
            raise 