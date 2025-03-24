"""Main module for the Truth Checker application."""

import argparse
import asyncio
import logging
import os
import sys
from typing import Optional

from dotenv import load_dotenv

from truth_checker.infrastructure.services.deepgram_service import DeepgramTranscriptionService
from truth_checker.interfaces.audio.audio_interface import AudioInterface, FileSource, MicrophoneSource
from truth_checker.interfaces.api.server import start_server


async def process_audio(
    api_key: str,
    audio_file: Optional[str] = None,
    verbose: bool = False
):
    """Process audio from a file or microphone.
    
    Args:
        api_key: Deepgram API key
        audio_file: Path to an audio file, or None to use microphone
        verbose: Whether to enable verbose logging
    """
    # Set up logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    
    try:
        # Create services
        logger.info("Initializing services...")
        transcription_service = DeepgramTranscriptionService(api_key=api_key)
        
        # Set up transcript callback
        def print_transcript(transcript):
            if transcript.is_final:
                print(f"\nFinal: {transcript.text}")
            else:
                # Print without newline to allow updates
                print(f"\rInterim: {transcript.text}", end="", flush=True)
        
        # Register the callback
        transcription_service.register_transcript_handler(print_transcript)
        
        if audio_file:
            logger.info(f"Using audio file: {audio_file}")
            # For files, use the prerecorded API
            transcripts = await transcription_service.transcribe_file(audio_file)
            for transcript in transcripts:
                print_transcript(transcript)
        else:
            # For microphone input, use live transcription
            await transcription_service.start_transcription()
            logger.info("Transcription service started")
            
            # Set up audio source
            logger.info("Using microphone input")
            audio_source = MicrophoneSource()
                
            # Create audio interface
            audio_interface = AudioInterface()
            audio_interface.set_audio_source(audio_source)
            
            # Define audio callback to send data to Deepgram
            async def on_audio(data):
                await transcription_service.send_audio(data)
                
            # Register the callback
            audio_interface.register_audio_handler(on_audio)
            
            # Start audio processing
            await audio_interface.start()
            logger.info("Audio interface started")
            
            try:
                # For microphone, run until interrupted
                print("Listening... Press Ctrl+C to stop.")
                while True:
                    await asyncio.sleep(0.1)
            except KeyboardInterrupt:
                print("\nStopping...")
            finally:
                # Stop services
                await audio_interface.stop()
                await transcription_service.stop_transcription()
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
        
    return 0


def main():
    """Main entry point for the Truth Checker application."""
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Truth Checker Application")
    
    # Mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--server",
        action="store_true",
        help="Run as API server (receives audio via HTTP/WebSocket)"
    )
    mode_group.add_argument(
        "--local",
        action="store_true",
        help="Run in local mode (process audio file or microphone)"
    )
    
    # Common arguments
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    # Local mode arguments
    parser.add_argument(
        "-f", "--file",
        help="Path to audio file (WAV, MP3, etc.) to process (local mode only)"
    )
    
    # Server mode arguments
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to (server mode only)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (server mode only)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    
    # Check for Deepgram API key
    api_key = os.environ.get("DEEPGRAM_API_KEY")
    if not api_key:
        logger.error("Deepgram API key not found. Set the DEEPGRAM_API_KEY environment variable.")
        return 1
    
    # Run in the selected mode
    try:
        if args.server:
            # Run as API server
            logger.info(f"Starting API server on {args.host}:{args.port}")
            asyncio.run(start_server(host=args.host, port=args.port))
        else:
            # Run in local mode
            if args.file and not os.path.exists(args.file):
                logger.error(f"Audio file not found: {args.file}")
                return 1
                
            # Process audio
            logger.info("Running in local mode")
            return asyncio.run(process_audio(api_key, args.file, args.verbose))
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main()) 