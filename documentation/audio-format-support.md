# Audio Format Support

The Truth Checker application supports a variety of audio formats for transcription. This document provides details on the supported formats and how to configure them.

## Supported Formats

### Common Audio Formats

| Format | MIME Type(s) | Description |
|--------|--------------|-------------|
| WAV | `audio/wav`, `audio/x-wav` | Waveform Audio File Format, uncompressed audio |
| MP3 | `audio/mpeg`, `audio/mp3` | MPEG-1/2 Audio Layer III, compressed audio |
| WebM | `audio/webm` | WebM audio container format |
| OGG | `audio/ogg`, `audio/vorbis` | Ogg Vorbis audio format |
| FLAC | `audio/flac` | Free Lossless Audio Codec |
| AAC | `audio/aac`, `audio/mp4`, `audio/m4a` | Advanced Audio Coding |
| PCM | `audio/pcm`, `audio/l16`, `audio/raw` | Raw audio data |

### Raw PCM Audio Parameters

When working with raw PCM audio, you need to specify additional parameters:

| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| `encoding` | Audio encoding format | `linear16` (16-bit PCM) |
| `sample_rate` | Sample rate in Hz | `16000` (16kHz) |
| `channels` | Number of audio channels | `1` (mono) |

## HTTP API Usage

When uploading files via the HTTP API, the system will attempt to detect the audio format based on:

1. The Content-Type header
2. File extension
3. Audio content analysis

Example using cURL:

```bash
# Upload an MP3 file
curl -X POST http://localhost:8000/api/transcribe \
  -F "file=@audio.mp3"

# Upload a raw PCM file with parameters
curl -X POST http://localhost:8000/api/transcribe \
  -F "file=@audio.pcm" \
  -F "encoding=linear16" \
  -F "sample_rate=16000" \
  -F "channels=1"
```

## WebSocket API Usage

When streaming audio via WebSocket, you must specify the audio format when starting the transcription:

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/api/stream');

// Start transcription with MP3 format
ws.send(JSON.stringify({
  command: 'start',
  audio_format: {
    mimetype: 'audio/mpeg'
  }
}));

// Start transcription with raw PCM format
ws.send(JSON.stringify({
  command: 'start',
  audio_format: {
    mimetype: 'audio/pcm',
    encoding: 'linear16',
    sample_rate: 16000,
    channels: 1
  }
}));
```

## Deepgram Support

The Truth Checker uses Deepgram for transcription, which supports the following formats:

- WAV (PCM)
- MP3
- OGG
- FLAC
- AAC
- WebM
- AIFF
- AMR
- CAF

For detailed information about Deepgram's audio format support, visit the [Deepgram Documentation](https://developers.deepgram.com/docs/audio-formats).

## Best Practices

### Format Selection

- Use **MP3** for general-purpose audio files (good balance of quality and size)
- Use **WAV** for highest quality recordings (uncompressed)
- Use **PCM** for real-time streaming or when you need precise control over audio parameters

### Converting Audio Formats

You can convert between audio formats using FFmpeg:

```bash
# Convert to MP3
ffmpeg -i input.wav -codec:a libmp3lame -qscale:a 2 output.mp3

# Convert to WAV
ffmpeg -i input.mp3 output.wav

# Convert to PCM
ffmpeg -i input.mp3 -f s16le -acodec pcm_s16le -ar 16000 -ac 1 output.pcm
```

### Troubleshooting Audio Issues

If you're experiencing issues with audio transcription:

1. **Check format compatibility**: Ensure your audio format is supported
2. **Inspect audio quality**: Low-quality audio may result in poor transcription
3. **Set correct parameters for PCM**: If using raw audio, ensure encoding, sample rate, and channels are set correctly
4. **Convert to a standard format**: When in doubt, convert to WAV or MP3

## Example Code

### Python: Processing Different Audio Formats

```python
from truth_checker.application.transcription_service import TranscriptionApplicationService
from truth_checker.infrastructure.services.deepgram_service import DeepgramTranscriptionService

async def process_different_formats():
    transcription_service = TranscriptionApplicationService(
        transcription_service=DeepgramTranscriptionService()
    )
    
    # Process MP3
    mp3_transcripts = await transcription_service.transcribe_file(
        "audio.mp3"
    )
    
    # Process WAV
    wav_transcripts = await transcription_service.transcribe_file(
        "audio.wav"
    )
    
    # Process PCM with parameters
    pcm_transcripts = await transcription_service.transcribe_file(
        "audio.pcm",
        options={
            "encoding": "linear16",
            "sample_rate": 16000,
            "channels": 1
        }
    )
```

For more examples, see the [examples](../examples/) directory. 