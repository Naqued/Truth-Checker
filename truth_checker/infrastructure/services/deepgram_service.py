"""Deepgram implementation of the transcription service."""

import asyncio
import json
import logging
import os
import time
from typing import AsyncIterator, Callable, Dict, List, Optional, Any, Union

from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
    PrerecordedOptions,
)

from truth_checker.config import config
from truth_checker.domain.models import Transcript, TranscriptWord
from truth_checker.domain.ports import TranscriptionService

logger = logging.getLogger(__name__)


class DeepgramTranscriptionService(TranscriptionService):
    """Transcription service using Deepgram API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Deepgram transcription service.
        
        Args:
            api_key: Deepgram API key (default: from environment variable)
        """
        # Get API key from environment if not provided
        self.api_key = api_key or os.environ.get("DEEPGRAM_API_KEY")
        if not self.api_key:
            logger.warning("No Deepgram API key provided, will use mock implementation")
            
        # Initialize client if we have an API key
        if self.api_key and self.api_key != "your_deepgram_api_key_here":
            self.client = DeepgramClient(self.api_key)
        else:
            self.client = None
            
        # Initialize state
        self.connection = None
        self.transcript_handlers: List[Callable[[Transcript], None]] = []
        self.running = False
        
        # Default options
        self.default_options = {
            "language": "en-US", 
            "model": "nova-2",
            "smart_format": True,
            "diarize": True,
            "punctuate": True
        }
        
    async def start_transcription(
        self, 
        mimetype: str = "audio/raw",
        encoding: Optional[str] = None,
        sample_rate: Optional[int] = None,
        channels: Optional[int] = None,
        **kwargs
    ) -> None:
        """Start real-time transcription."""
        if self.running:
            logger.warning("Transcription already running")
            return
            
        # If no API key, use mock implementation
        if not self.client:
            logger.warning("No valid Deepgram API key, using mock implementation")
            self.running = True
            return
            
        try:
            logger.info(f"Starting transcription with parameters: {{'mimetype': '{mimetype}'"
                    + (f", 'encoding': '{encoding}'" if encoding else "")
                    + (f", 'sample_rate': {sample_rate}" if sample_rate else "")
                    + (f", 'channels': {channels}" if channels else "")
                    + "}")
            
            # Build options for Deepgram
            options_dict = self.default_options.copy()
            
            # Add encoding parameters for raw/PCM audio
            if mimetype in {"audio/raw", "audio/pcm", "audio/l16"} or encoding:
                options_dict["encoding"] = encoding or "linear16"
                options_dict["sample_rate"] = sample_rate or 16000
                options_dict["channels"] = channels or 1
                
                logger.info(f"Using audio parameters: encoding={options_dict['encoding']}, "
                           f"sample_rate={options_dict['sample_rate']}, channels={options_dict['channels']}")
            
            # Add additional parameters if provided
            for key, value in kwargs.items():
                options_dict[key] = value
            
            # Create options object
            options = LiveOptions(**options_dict)
            
            # Create live transcription connection
            self.connection = self.client.listen.live.v("1")
            
            # Define event handlers with detailed logging
            def handle_open(connection, message):
                logger.info("Deepgram connection opened")
                logger.debug(f"Open message: {message}")
                self.running = True
                
            def handle_transcript(connection, transcript=None, result=None):
                # Process transcript data
                try:
                    # Determine which parameter to use (transcript or result)
                    data = transcript or result
                    
                    if not data:
                        logger.warning("No transcript data received")
                        return
                    
                    # Log the received data for debugging
                    logger.debug(f"Received transcript data: {data}")
                    
                    # Check if the transcript has any alternatives
                    transcripts_found = False
                    transcript_text = ""
                    
                    # Extract transcript data
                    if hasattr(data, 'channel') and hasattr(data.channel, 'alternatives'):
                        alternatives = data.channel.alternatives
                        is_final = getattr(data, 'is_final', False)
                        logger.debug(f"Found {len(alternatives) if alternatives else 0} alternatives in data.channel")
                        transcripts_found = True
                    elif hasattr(data, 'result') and hasattr(data.result, 'channel') and hasattr(data.result.channel, 'alternatives'):
                        alternatives = data.result.channel.alternatives
                        is_final = getattr(data.result, 'is_final', False)
                        logger.debug(f"Found {len(alternatives) if alternatives else 0} alternatives in data.result.channel")
                        transcripts_found = True
                    # Try parsing channels array if no alternatives found
                    elif hasattr(data, 'channels') and len(data.channels) > 0:
                        # Use the first channel's alternatives
                        alternatives = data.channels[0].alternatives
                        is_final = getattr(data, 'is_final', False)
                        logger.debug(f"Found {len(alternatives) if alternatives else 0} alternatives in data.channels[0]")
                        transcripts_found = True
                    else:
                        # Try common patterns for the Deepgram response
                        logger.warning(f"Common transcript patterns not found. Trying to debug the data structure...")
                        logger.debug(f"Data attributes: {dir(data)}")
                        
                        # Try to dump as JSON
                        try:
                            if hasattr(data, 'to_dict'):
                                data_dict = data.to_dict()
                                logger.debug(f"Data as dict: {data_dict}")
                                
                                # Try to parse from the dict directly
                                if 'channel' in data_dict and 'alternatives' in data_dict['channel']:
                                    alternatives = data_dict['channel']['alternatives']
                                    is_final = data_dict.get('is_final', False)
                                    transcripts_found = True
                                elif 'result' in data_dict and 'channel' in data_dict['result'] and 'alternatives' in data_dict['result']['channel']:
                                    alternatives = data_dict['result']['channel']['alternatives']
                                    is_final = data_dict['result'].get('is_final', False)
                                    transcripts_found = True
                                else:
                                    logger.warning(f"Could not find alternatives in data_dict")
                        except Exception as dict_err:
                            logger.error(f"Error parsing data dict: {dict_err}")
                        
                        if not transcripts_found:
                            # Create a mock transcript as a fallback
                            logger.warning("Creating mock transcript as fallback")
                            mock_transcript = Transcript(
                                text="[Transcription temporarily unavailable]",
                                confidence=0.5,
                                is_final=True,
                                start_time=time.time(),
                                end_time=time.time()
                            )
                            
                            # Call handlers with our mock transcript
                            for handler in self.transcript_handlers:
                                try:
                                    logger.debug(f"Calling handler with mock transcript: {handler}")
                                    handler(mock_transcript)
                                except Exception as e:
                                    logger.error(f"Error in transcript handler with mock: {e}")
                            
                            return
                    
                    # Process alternatives if found
                    if transcripts_found and alternatives and len(alternatives) > 0:
                        first_alt = alternatives[0]
                        text = ""
                        confidence = 0.0
                        
                        # Get transcript text and confidence
                        if hasattr(first_alt, 'transcript'):
                            text = first_alt.transcript or ""
                        # Try alternative attribute names
                        elif hasattr(first_alt, 'text'):
                            text = first_alt.text or ""
                        
                        # Get confidence
                        if hasattr(first_alt, 'confidence'):
                            confidence = getattr(first_alt, 'confidence', 0.95)
                        
                        logger.info(f"Transcription received: '{text}' (confidence: {confidence}, final: {is_final})")
                        
                        # Create transcript object
                        transcript_obj = Transcript(
                            text=text,
                            confidence=confidence,
                            is_final=is_final,
                            start_time=time.time(),
                            end_time=time.time()
                        )
                        
                        # Call handlers
                        for handler in self.transcript_handlers:
                            try:
                                logger.debug(f"Calling transcript handler: {handler}")
                                handler(transcript_obj)
                            except Exception as e:
                                logger.error(f"Error in transcript handler: {e}")
                    else:
                        logger.warning("No transcript alternatives found.")
                        
                except Exception as e:
                    logger.error(f"Error processing transcript: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    
            def handle_metadata(connection, metadata):
                logger.debug(f"Received metadata: {metadata}")
                
            def handle_speech_started(connection, speech_started):
                logger.debug(f"Speech started: {speech_started}")
                
            def handle_utterance_end(connection, utterance_end):
                logger.debug(f"Utterance end: {utterance_end}")
                
            def handle_error(connection, error):
                logger.error(f"Deepgram error: {error}")
                
            def handle_close(connection, message):
                logger.info("Deepgram connection closed")
                logger.debug(f"Close message: {message}")
                self.running = False
            
            # Register all event handlers to catch any events Deepgram might send
            logger.debug("Registering Deepgram event handlers")
            
            self.connection.on(LiveTranscriptionEvents.Open, handle_open)
            self.connection.on(LiveTranscriptionEvents.Transcript, handle_transcript)
            self.connection.on(LiveTranscriptionEvents.Metadata, handle_metadata)
            self.connection.on(LiveTranscriptionEvents.SpeechStarted, handle_speech_started)
            self.connection.on(LiveTranscriptionEvents.UtteranceEnd, handle_utterance_end)
            self.connection.on(LiveTranscriptionEvents.Error, handle_error)
            self.connection.on(LiveTranscriptionEvents.Close, handle_close)
            
            # Start the connection - FIXED: Don't await the result since it's a boolean
            # The method starts the connection asynchronously and returns a boolean indicating success
            success = self.connection.start(options)
            if not success:
                logger.error("Failed to start Deepgram connection")
                raise Exception("Failed to start Deepgram connection")
                
            # Mark as running even though the open event hasn't fired yet
            # The open event will be fired asynchronously
            self.running = True
            logger.info("Deepgram transcription started")
            
        except Exception as e:
            logger.error(f"Error starting transcription: {e}")
            self.running = False
            raise
            
    async def stop_transcription(self) -> None:
        """Stop real-time transcription."""
        if not self.running:
            logger.warning("Transcription not running")
            return
            
        try:
            if self.connection:
                # Safely close the connection
                try:
                    # FIXED: Don't await the finish method since it doesn't return a coroutine
                    self.connection.finish()
                except Exception as e:
                    logger.warning(f"Error closing Deepgram connection: {e}")
                    
                self.connection = None
                
            self.running = False
            logger.info("Deepgram transcription stopped")
            
        except Exception as e:
            logger.error(f"Error stopping transcription: {e}")
            raise
            
    async def send_audio(self, audio_data: bytes) -> None:
        """Send audio data to the transcription service.
        
        Args:
            audio_data: Audio data in bytes
        """
        if not self.running:
            logger.warning("Transcription not running, can't send audio data")
            return
            
        # If mock implementation, send mock transcript after a short delay
        if not self.connection:
            await asyncio.sleep(0.5)
            
            # Create mock transcript
            transcript = Transcript(
                text="This is a mock transcript.",
                confidence=0.95,
                is_final=True,
                start_time=time.time(),
                end_time=time.time(),
                words=[]
            )
            
            # Call handlers with the mock transcript
            for handler in self.transcript_handlers:
                try:
                    handler(transcript)
                except Exception as e:
                    logger.error(f"Error in transcript handler: {e}")
            
            return
            
        # Send audio data to Deepgram
        try:
            if not self.connection:
                logger.error("No active Deepgram connection")
                return
                
            # FIXED: Handle non-coroutine result from send method
            # The send method may not return a coroutine in some versions
            try:
                # Send the audio data to Deepgram
                result = self.connection.send(audio_data)
                
                # If it's a coroutine, await it
                if asyncio.iscoroutine(result):
                    await result
                # Otherwise, it's likely just a boolean success indicator
                
            except Exception as e:
                logger.error(f"Error sending audio data to Deepgram: {e}")
                
        except Exception as e:
            logger.error(f"Error sending audio data: {e}")
            
    def register_transcript_handler(self, handler: Callable[[Transcript], None]) -> None:
        """Register a handler for transcript events.
        
        Args:
            handler: Function to call with each transcript
        """
        self.transcript_handlers.append(handler)
        
    async def get_transcripts(self) -> AsyncIterator[Transcript]:
        """Get transcripts from the service.
        
        Not implemented for real-time transcription.
        """
        yield Transcript(text="Not implemented for real-time transcription", confidence=0.0, is_final=True)
        
    async def transcribe_file(self, file_path: str, options: Optional[Dict[str, Any]] = None) -> List[Transcript]:
        """Transcribe an audio file using Deepgram.
        
        Args:
            file_path: Path to the audio file
            options: Additional options for transcription
            
        Returns:
            List of transcripts
        """
        # If no API key or invalid API key, use mock implementation
        if not self.client:
            logger.warning("No valid Deepgram API key, using mock implementation for file transcription")
            # Return mock transcripts
            mock_transcripts = [
                Transcript(
                    text="When you look at the map, a map of the Middle East, Israel is a tiny little spot compared to these giant land masses.",
                    confidence=0.99,
                    is_final=True,
                    start_time=0,
                    end_time=5,
                ),
                Transcript(
                    text="It's really a tiny spot. I actually said, is there any way of getting more?",
                    confidence=0.98,
                    is_final=True,
                    start_time=5,
                    end_time=10,
                ),
                Transcript(
                    text="It's so tiny.",
                    confidence=0.98,
                    is_final=True,
                    start_time=10,
                    end_time=15,
                )
            ]
            return mock_transcripts
            
        try:
            # Prepare options
            options_dict = self.default_options.copy()
            if options:
                options_dict.update(options)
                
            # Create options object
            dgram_options = PrerecordedOptions(**options_dict)
            
            # Read the file
            with open(file_path, "rb") as audio:
                audio_data = audio.read()
                
            # Check file size
            if len(audio_data) < 44:  # Minimum size for a WAV header
                logger.error(f"Audio file too small: {len(audio_data)} bytes")
                raise ValueError(f"Audio file too small to be valid: {len(audio_data)} bytes")
                
            # Validate WAV file if it appears to be one
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.wav' or audio_data[:4] == b'RIFF':
                logger.info("Validating WAV file headers")
                try:
                    # Check WAV header
                    if audio_data[:4] != b'RIFF':
                        logger.error("Missing RIFF header in WAV file")
                        raise ValueError("Invalid WAV file: missing RIFF header")
                        
                    if audio_data[8:12] != b'WAVE':
                        logger.error("Missing WAVE format marker in WAV file")
                        raise ValueError("Invalid WAV file: missing WAVE format marker")
                        
                    if audio_data[12:16] != b'fmt ':
                        logger.error("Missing fmt chunk in WAV file")
                        raise ValueError("Invalid WAV file: missing fmt chunk")
                        
                    # Check for data chunk
                    data_chunk_found = False
                    for i in range(36, min(len(audio_data) - 4, 100)):  # Search within first 100 bytes
                        if audio_data[i:i+4] == b'data':
                            data_chunk_found = True
                            break
                            
                    if not data_chunk_found:
                        logger.error("Missing data chunk in WAV file")
                        raise ValueError("Invalid WAV file: missing data chunk")
                        
                    # Check audio format
                    import struct
                    format_code = struct.unpack('<H', audio_data[20:22])[0]
                    if format_code != 1:  # 1 is PCM
                        logger.warning(f"WAV format is not PCM (code: {format_code})")
                        
                    # Check channels and sample rate for debugging
                    channels = struct.unpack('<H', audio_data[22:24])[0]
                    sample_rate = struct.unpack('<I', audio_data[24:28])[0]
                    logger.info(f"WAV file info: channels={channels}, sample_rate={sample_rate}")
                    
                    # Quick-check for common issues
                    if channels == 0 or sample_rate == 0:
                        logger.error(f"Invalid WAV parameters: channels={channels}, sample_rate={sample_rate}")
                        raise ValueError("Invalid WAV file: bad format parameters")
                        
                except Exception as e:
                    logger.error(f"Error validating WAV file: {e}")
                    # We'll still try to send it, but log the issue
                    
            # Create source
            source = {"buffer": audio_data}
            
            # Transcribe - FIXED: Don't await the result as it's not a coroutine
            response = self.client.listen.prerecorded.v("1").transcribe_file(source, dgram_options)
            
            # Process the response
            transcripts = []
            
            # Check for results
            if hasattr(response, 'results'):
                # Extract utterances if available
                if hasattr(response.results, 'utterances') and response.results.utterances:
                    for utterance in response.results.utterances:
                        transcript = Transcript(
                            text=utterance.transcript,
                            confidence=utterance.confidence,
                            is_final=True,
                            start_time=utterance.start,
                            end_time=utterance.end,
                        )
                        transcripts.append(transcript)
                # Otherwise use alternatives
                elif hasattr(response.results, 'channels') and response.results.channels:
                    for channel in response.results.channels:
                        for alternative in channel.alternatives:
                            transcript = Transcript(
                                text=alternative.transcript,
                                confidence=alternative.confidence,
                                is_final=True,
                                start_time=0,
                                end_time=0,
                            )
                            transcripts.append(transcript)
                            # Only use the first alternative
                            break
                            
            return transcripts
            
        except Exception as e:
            logger.error(f"Error transcribing file: {e}")
            raise 