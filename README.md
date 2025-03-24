# Truth Checker

A system for transcribing audio, detecting claims, and fact-checking them in real-time.

## Features

- **Audio Transcription**: Transcribe audio files using Deepgram's API
- **Multiple Audio Formats**: Support for MP3, WAV, WebM, PCM and other formats
- **API Server**: HTTP endpoints for transcribing files and WebSocket for real-time streaming
- **Local Mode**: Run transcription on local files without starting a server
- **Modular Architecture**: Hexagonal architecture for clean separation of concerns
- **Real-time Streaming**: WebSocket integration for live audio transcription

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/truth-checker.git
cd truth-checker
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up environment variables
```bash
# Create a .env file in the project root (not in the truth_checker directory)
echo "DEEPGRAM_API_KEY=your_deepgram_api_key_here" > .env
# Replace with your actual Deepgram API key
```

## Usage

### Running in Local Mode

Process an audio file directly:

```bash
python -m truth_checker --local --file path/to/audio.mp3
```

### Running as a Server

Start the server:

```bash
python -m truth_checker --server
```

This will start a FastAPI server on http://localhost:8000 with the following endpoints:

- `GET /`: API information
- `POST /api/transcribe`: Upload an audio file for transcription
- `WebSocket /api/stream`: Stream audio in real-time for transcription

### Using the Demo Script

The project includes a demo script that demonstrates different ways to use the Truth Checker:

```bash
# Direct transcription (no API server required)
python examples/demo.py truth_checker/assets/test-audio-trump.mp3 --mode direct

# HTTP API transcription (server must be running)
python examples/demo.py truth_checker/assets/test-audio-trump.mp3 --mode http

# WebSocket streaming (server must be running)
python examples/demo.py truth_checker/assets/test-audio-trump.mp3 --mode websocket
```

### WebSocket Debug Script

There's also a debug script for testing the WebSocket connection:

```bash
python examples/deepgram_websocket_debug.py truth_checker/assets/test-audio-trump.mp3
```

## Supported Audio Formats

- WAV (audio/wav, audio/x-wav)
- MP3 (audio/mpeg, audio/mp3)
- WebM (audio/webm)
- PCM/raw audio (audio/pcm, audio/l16, audio/raw) with configurable parameters
- Other formats supported by Deepgram (OGG, FLAC, AAC, etc.)

## Architecture

The Truth Checker follows a hexagonal architecture:

- **Domain**: Core business logic and models
- **Application**: Use cases that orchestrate domain logic
- **Infrastructure**: External services and adapters (Deepgram, etc.)
- **Interfaces**: API endpoints and CLI interface

## Mock Mode

The system supports a mock mode when no valid Deepgram API key is provided. In this mode:
- Transcription requests return pre-defined responses
- This is useful for development and testing without consuming Deepgram API credits
- To use mock mode, either don't set the API key or set it to the placeholder value

## Development

To contribute to the project:

1. Set up a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install development dependencies
```bash
pip install -r requirements-dev.txt
```

3. Run tests
```bash
pytest
```

## Current Status

- ✅ Audio transcription with Deepgram API
- ✅ HTTP and WebSocket interfaces for real-time transcription
- ✅ Support for multiple audio formats
- ✅ Mock mode for development without an API key
- 🔄 Claim detection (in progress)
- 🔄 Fact-checking integration (in progress)
- 🔄 Knowledge base development (planned)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Deepgram](https://deepgram.com/) for speech-to-text capabilities
- [FastAPI](https://fastapi.tiangolo.com/) for the API server
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) for audio processing