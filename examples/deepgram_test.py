#!/usr/bin/env python3
"""Test Deepgram API key and transcription."""

import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
from deepgram import DeepgramClient, PrerecordedOptions

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

async def test_deepgram_transcription():
    """Test Deepgram API key by transcribing a sample audio file."""
    # Get API key from environment
    api_key = os.environ.get("DEEPGRAM_API_KEY")
    if not api_key:
        logger.error("No Deepgram API key found in environment variables")
        return False
        
    logger.info(f"Using Deepgram API key: {api_key[:5]}...{api_key[-5:]}")
    
    # Find test audio file
    test_file = Path("truth_checker/assets/test-audio-trump.mp3")
    if not test_file.exists():
        logger.error(f"Test audio file not found: {test_file}")
        return False
        
    logger.info(f"Found test audio file: {test_file}")
    
    try:
        # Initialize Deepgram client
        client = DeepgramClient(api_key)
        logger.info("Initialized Deepgram client")
        
        # Set transcription options
        options = PrerecordedOptions(
            language="en-US",
            model="nova-2",
            smart_format=True,
            diarize=True,
            punctuate=True
        )
        
        # Read the audio file
        with open(test_file, "rb") as audio:
            audio_data = audio.read()
            
        # Create source
        source = {"buffer": audio_data}
        
        # Transcribe
        logger.info("Sending transcription request to Deepgram...")
        response = client.listen.prerecorded.v("1").transcribe_file(source, options)
        
        # Check if response is valid
        if not response or not hasattr(response, 'results'):
            logger.error("No valid response received from Deepgram")
            return False
            
        # Extract transcript
        if hasattr(response.results, 'channels') and response.results.channels:
            transcript = response.results.channels[0].alternatives[0].transcript
            confidence = response.results.channels[0].alternatives[0].confidence
            logger.info(f"Transcription successful! Confidence: {confidence}")
            logger.info(f"Transcript: {transcript}")
            return True
        else:
            logger.error("No transcription results found in response")
            return False
            
    except Exception as e:
        logger.error(f"Error testing Deepgram transcription: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
        
if __name__ == "__main__":
    # Run the test
    result = asyncio.run(test_deepgram_transcription())
    
    if result:
        logger.info("✅ Deepgram API key is working correctly!")
    else:
        logger.error("❌ Deepgram API key test failed. Check the logs for details.") 