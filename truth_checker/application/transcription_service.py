"""Application service for managing transcription."""

import asyncio
import inspect
import logging
import functools
import os
from typing import AsyncIterator, Callable, Optional, List, Dict, Any, Union, Awaitable

from truth_checker.domain.models import Transcript
from truth_checker.domain.ports import TranscriptionService

logger = logging.getLogger(__name__)


class TranscriptionApplicationService:
    """Application service for managing transcriptions."""

    def __init__(self, transcription_service: TranscriptionService):
        """Initialize the transcription application service.

        Args:
            transcription_service: Service for handling audio transcription
        """
        self.transcription_service = transcription_service
        self.transcript_callbacks = []
        self._transcripts = []
        
        # Register a callback to store transcripts
        def store_transcript(transcript: Transcript) -> None:
            self._transcripts.append(transcript)
            
        self.transcription_service.register_transcript_handler(store_transcript)

    async def start_transcription(
        self, 
        mimetype: str = "audio/raw", 
        encoding: Optional[str] = None,
        sample_rate: Optional[int] = None,
        channels: Optional[int] = None,
        **kwargs
    ) -> None:
        """Start the transcription service.
        
        Args:
            mimetype: MIME type of the audio data
            encoding: Audio encoding (e.g., 'linear16', 'opus', 'mulaw')
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels
            **kwargs: Additional parameters to pass to the transcription service
        """
        # Build parameters dictionary
        params = {"mimetype": mimetype}
        
        # Add optional parameters if provided
        if encoding:
            params["encoding"] = encoding
        if sample_rate:
            params["sample_rate"] = sample_rate
        if channels:
            params["channels"] = channels
            
        # Check if we're in testing/mock mode
        mock_mode = kwargs.get("mock_mode", False) or os.environ.get("MOCK_TRANSCRIPTION", "").lower() in ("true", "1", "yes")
        
        # Remove mock_mode from kwargs so it doesn't get passed to the transcription service
        if "mock_mode" in kwargs:
            del kwargs["mock_mode"]
            
        # Add any other parameters
        params.update(kwargs)
        
        if mock_mode:
            logger.info("Using mock mode for transcription service - not starting real service")
            # Don't start the actual service, just record that we're in mock mode
            self._mock_mode = True
            return
            
        # Start the transcription service
        logger.info(f"Starting transcription with parameters: {params}")
        await self.transcription_service.start_transcription(**params)

    async def stop_transcription(self) -> None:
        """Stop the transcription service."""
        # If we're in mock mode, just return
        if hasattr(self, '_mock_mode') and self._mock_mode:
            logger.info("Mock mode - not stopping real transcription service")
            return
            
        await self.transcription_service.stop_transcription()

    async def process_audio_data(self, audio_data: bytes) -> None:
        """Process audio data and send it to the transcription service.
        
        Args:
            audio_data: Audio data in bytes
        """
        # If we're in mock mode, just return
        if hasattr(self, '_mock_mode') and self._mock_mode:
            logger.debug("Mock mode - not processing audio data")
            return
            
        await self.transcription_service.send_audio(audio_data)

    def add_transcript_callback(self, callback: Union[Callable[[Transcript], None], Callable[[Transcript], Awaitable[None]]]) -> None:
        """Add a callback function to be called for each transcript.
        
        Args:
            callback: Function to call with each transcript, can be sync or async
        """
        # Store both sync and async callbacks
        self.transcript_callbacks.append(callback)
        
        # Define a handler to call all callbacks
        # Using a better approach for async callbacks in sync contexts
        def call_callbacks(transcript: Transcript) -> None:
            # Process synchronous callbacks directly
            for callback_func in self.transcript_callbacks:
                try:
                    # Check if callback is async (coroutine function)
                    if inspect.iscoroutinefunction(callback_func):
                        # For async callbacks, we need to handle them differently
                        # If we're in an event loop already, we can use it
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                # Schedule the coroutine to run soon
                                asyncio.run_coroutine_threadsafe(callback_func(transcript), loop)
                            else:
                                # If loop exists but isn't running, just log this info
                                logger.debug("Event loop exists but not running for async callback")
                        except RuntimeError:
                            # No event loop, just log this case
                            logger.debug("No running event loop for async callback")
                    else:
                        # Regular synchronous callback
                        callback_func(transcript)
                except Exception as e:
                    logger.error(f"Error in transcript callback: {e}")
                    
        # Register with the service
        self.transcription_service.register_transcript_handler(call_callbacks)

    def get_transcripts(self) -> List[Transcript]:
        """Get all recorded transcripts.
        
        Returns:
            List of transcript objects
        """
        return self._transcripts

    async def get_transcripts_stream(self) -> AsyncIterator[Transcript]:
        """Get a stream of transcripts from the service.

        Yields:
            Transcript objects as they become available
        """
        async for transcript in self.transcription_service.get_transcripts():
            yield transcript
            
    async def transcribe_file(self, file_path: str, options: Optional[Dict[str, Any]] = None) -> List[Transcript]:
        """Transcribe an audio file.
        
        Args:
            file_path: Path to the audio file
            options: Additional options for transcription
            
        Returns:
            List of transcripts
        """
        transcripts = await self.transcription_service.transcribe_file(file_path, options)
        return transcripts 