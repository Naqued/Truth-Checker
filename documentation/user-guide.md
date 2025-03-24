# User Guide

This guide explains how to use the Truth Checker application for transcribing audio, detecting claims, and fact-checking.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/truth-checker.git
cd Truth-Checker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env to add your Deepgram API key
```

## Running the Application

### Local Mode

Process an audio file directly:

```bash
python -m truth_checker --local --file path/to/audio.mp3
```

Options:
- `--file` or `-f`: Path to an audio file to process
- `--verbose`: Enable verbose logging

### Server Mode

Start the API server:

```bash
python -m truth_checker --server
```

Options:
- `--host`: Host address to bind to (default: 0.0.0.0)
- `--port`: Port to bind to (default: 8000)
- `--verbose`: Enable verbose logging

The server provides HTTP and WebSocket endpoints for client applications.

## Using the Demo Script

The project includes a demo script that shows different ways to use the Truth Checker:

```bash
# Direct transcription (no server required)
python examples/demo.py path/to/audio.mp3 --mode direct

# HTTP API transcription (server must be running)
python examples/demo.py path/to/audio.mp3 --mode http

# WebSocket streaming (server must be running)
python examples/demo.py path/to/audio.mp3 --mode websocket
```

Options:
- `--mode`: Transcription mode (`direct`, `http`, or `websocket`)
- `--server`: Server URL (default: http://localhost:8000)
- `--verbose`: Enable verbose logging

## Supported Audio Formats

The Truth Checker supports various audio formats:

- WAV (audio/wav, audio/x-wav)
- MP3 (audio/mpeg, audio/mp3)
- WebM (audio/webm)
- OGG (audio/ogg, audio/vorbis)
- FLAC (audio/flac)
- PCM/raw audio (audio/pcm, audio/l16, audio/raw)
- Other formats supported by Deepgram

For raw PCM audio, you may need to specify additional parameters like encoding, sample rate, and channels.

## Workflow

1. **Transcription**: Audio is converted to text using speech recognition
2. **Claim Detection**: Factual claims are identified in the transcripts
3. **Fact Checking**: Claims are verified against trusted knowledge sources
4. **Results**: The system provides verdicts on the truthfulness of claims

## Example Use Cases

### Analyzing Political Speeches

1. Record or obtain an audio file of a political speech
2. Process the file using the Truth Checker
3. Review the transcription and fact-check results

### Monitoring Live Debates

1. Start the server in server mode
2. Connect a client application to the WebSocket endpoint
3. Stream the audio in real-time
4. Receive transcriptions and fact-checks as they become available

## Troubleshooting

### API Key Issues

If you see authentication errors, ensure your Deepgram API key is correctly set in the `.env` file.

### Audio Format Problems

If you're having issues with audio transcription:
- Ensure the audio format is supported
- For PCM/raw audio, specify the correct encoding parameters
- Try converting the audio to WAV or MP3 format

### Connection Issues

If you can't connect to the server:
- Verify the server is running
- Check that the host and port are correct
- Ensure no firewall is blocking the connection

## Getting Help

If you encounter any issues or have questions, please:

1. Check the troubleshooting section
2. Review the [API Reference](api-reference.md)
3. Open an issue on the GitHub repository 