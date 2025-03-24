"""Audio interface for capturing audio from microphone or file."""

import abc
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AudioSource(abc.ABC):
    """Base class for audio sources."""
    
    @abc.abstractmethod
    async def start(self) -> None:
        """Start capturing audio."""
        pass
    
    @abc.abstractmethod
    async def stop(self) -> None:
        """Stop capturing audio."""
        pass
    
    @abc.abstractproperty
    def is_running(self) -> bool:
        """Check if the audio source is running."""
        pass


class AudioInterface:
    """Interface for managing audio sources and processing."""
    
    def __init__(self):
        """Initialize the audio interface."""
        self.audio_source: Optional[AudioSource] = None
        self.audio_handlers = []
        self._processing_task = None
    
    def set_audio_source(self, audio_source: AudioSource) -> None:
        """Set the audio source to use.
        
        Args:
            audio_source: The audio source to use
        """
        if self.audio_source and self.audio_source.is_running:
            raise RuntimeError("Cannot change audio source while it's running")
        
        self.audio_source = audio_source
        logger.info(f"Set audio source to {audio_source.__class__.__name__}")
    
    async def start(self) -> None:
        """Start capturing and processing audio."""
        if not self.audio_source:
            raise RuntimeError("No audio source set")
        
        await self.audio_source.start()
        logger.info("Started audio capture")
    
    async def stop(self) -> None:
        """Stop capturing and processing audio."""
        if not self.audio_source:
            return
        
        await self.audio_source.stop()
        logger.info("Stopped audio capture")
    
    def register_audio_handler(self, handler) -> None:
        """Register a function to be called for each audio chunk.
        
        Args:
            handler: Function that takes audio data as its argument
        """
        self.audio_handlers.append(handler)
        logger.debug(f"Registered audio handler: {handler.__name__}")
        
    @property
    def is_active(self) -> bool:
        """Check if the audio interface is active."""
        return self.audio_source is not None and self.audio_source.is_running


class MicrophoneSource(AudioSource):
    """Audio source that captures from the microphone."""
    
    def __init__(self, sample_rate=16000, channels=1, chunk_size=1024):
        """Initialize the microphone source.
        
        Args:
            sample_rate: Sample rate in Hz
            channels: Number of audio channels
            chunk_size: Size of audio chunks in frames
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self._running = False
        self.stream = None
        self.audio_handlers = []
    
    async def start(self) -> None:
        """Start capturing audio from the microphone."""
        if self._running:
            logger.warning("Microphone is already capturing")
            return
        
        try:
            # Note: This is a placeholder - in a real implementation, we would use
            # a library like PyAudio or similar to capture audio from the microphone
            # For now, we'll just log that we would be capturing
            logger.info(
                f"Starting microphone capture (sample_rate={self.sample_rate}, "
                f"channels={self.channels}, chunk_size={self.chunk_size})"
            )
            self._running = True
            
            # In a real implementation, we would create a task that reads from the microphone
            # and calls the audio handlers with the captured audio
            # For now, we'll just simulate this with a dummy task
            self._processing_task = asyncio.create_task(self._simulate_capture())
            
        except Exception as e:
            logger.error(f"Failed to start microphone capture: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop capturing audio from the microphone."""
        if not self._running:
            logger.warning("Microphone is not capturing")
            return
        
        try:
            # Cancel the dummy processing task
            if self._processing_task and not self._processing_task.done():
                self._processing_task.cancel()
                try:
                    await self._processing_task
                except asyncio.CancelledError:
                    pass
            
            # In a real implementation, we would close the microphone stream
            logger.info("Stopped microphone capture")
            self._running = False
            
        except Exception as e:
            logger.error(f"Failed to stop microphone capture: {e}")
            raise
    
    @property
    def is_running(self) -> bool:
        """Check if the microphone source is running."""
        return self._running
    
    def register_audio_handler(self, handler) -> None:
        """Register a function to be called for each audio chunk.
        
        Args:
            handler: Function that takes audio data as its argument
        """
        self.audio_handlers.append(handler)
    
    async def _simulate_capture(self) -> None:
        """Simulate capturing audio from the microphone.
        
        This is a placeholder for actual microphone capture logic.
        In a real implementation, this would read from the microphone
        and call the audio handlers with the captured audio.
        """
        try:
            # Simulate capturing audio in a loop
            while self._running:
                # Simulate a 100ms audio chunk
                await asyncio.sleep(0.1)
                
                # In a real implementation, we would read audio data from the microphone
                # For now, just generate some dummy data
                dummy_audio_data = bytes([0] * self.chunk_size)
                
                # Call the audio handlers with the dummy data
                for handler in self.audio_handlers:
                    try:
                        await handler(dummy_audio_data)
                    except Exception as e:
                        logger.error(f"Error in audio handler {handler.__name__}: {e}")
                
        except asyncio.CancelledError:
            # This is expected when stopping
            pass
        except Exception as e:
            logger.error(f"Error in microphone capture: {e}")
            self._running = False
            raise


class FileSource(AudioSource):
    """Audio source that reads from a file."""
    
    def __init__(self, file_path, chunk_size=1024, playback_speed=1.0):
        """Initialize the file source.
        
        Args:
            file_path: Path to the audio file
            chunk_size: Size of audio chunks in bytes
            playback_speed: Speed multiplier for playback (1.0 = real-time)
        """
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.playback_speed = playback_speed
        self._running = False
        self._processing_task = None
        self.audio_handlers = []
    
    async def start(self) -> None:
        """Start reading audio from the file."""
        if self._running:
            logger.warning("File source is already playing")
            return
        
        try:
            logger.info(
                f"Starting file playback (file={self.file_path}, "
                f"chunk_size={self.chunk_size}, playback_speed={self.playback_speed})"
            )
            self._running = True
            
            # Start processing in the background
            self._processing_task = asyncio.create_task(self._process_file())
            
        except Exception as e:
            logger.error(f"Failed to start file playback: {e}")
            self._running = False
            raise
    
    async def stop(self) -> None:
        """Stop reading audio from the file."""
        if not self._running:
            logger.warning("File source is not playing")
            return
        
        try:
            # Cancel the processing task
            if self._processing_task and not self._processing_task.done():
                self._processing_task.cancel()
                try:
                    await self._processing_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Stopped file playback")
            self._running = False
            
        except Exception as e:
            logger.error(f"Failed to stop file playback: {e}")
            raise
    
    @property
    def is_running(self) -> bool:
        """Check if the file source is running."""
        return self._running
    
    def register_audio_handler(self, handler) -> None:
        """Register a function to be called for each audio chunk.
        
        Args:
            handler: Function that takes audio data as its argument
        """
        self.audio_handlers.append(handler)
    
    async def _process_file(self) -> None:
        """Process the audio file and send chunks to handlers."""
        try:
            with open(self.file_path, 'rb') as f:
                while self._running:
                    # Read a chunk of audio data
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        # End of file
                        break
                    
                    # Call the audio handlers with the chunk
                    for handler in self.audio_handlers:
                        try:
                            await handler(chunk)
                        except Exception as e:
                            logger.error(f"Error in audio handler {handler.__name__}: {e}")
                    
                    # Simulate real-time playback
                    if self.playback_speed > 0:
                        # Calculate delay based on chunk size and playback speed
                        # Assuming 16-bit samples at 16kHz
                        delay = (self.chunk_size / 32000) / self.playback_speed
                        await asyncio.sleep(delay)
            
            # File processing complete
            self._running = False
            
        except asyncio.CancelledError:
            # This is expected when stopping
            pass
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            self._running = False
            raise 