# Truth Checker

A system for transcribing audio, detecting claims, and fact-checking them in real-time.

## Features

- **Audio Transcription**: Transcribe audio files using Deepgram's API
- **Multiple Audio Formats**: Support for MP3, WAV, WebM, PCM and other formats
- **API Server**: HTTP endpoints for transcribing files and WebSocket for real-time streaming
- **Claim Detection**: AI-powered identification of factual claims in transcripts
- **Fact Checking**: Verification of claims using a RAG architecture with LangChain and LangGraph
- **Knowledge Repository**: Vector database for storing and retrieving factual information
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
# If using the fact checking features, add LLM provider API keys
echo "ANTHROPIC_API_KEY=your_anthropic_api_key_here" >> .env
# Or use OpenAI
echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env
```

## Usage

### Running the Fact Checking Demo

To test the fact checking capabilities without audio transcription:

```bash
python examples/fact_checking_demo.py
```

You can also provide your own text to analyze:

```bash
python examples/fact_checking_demo.py --text "The Earth is 6000 years old. Climate change is primarily caused by human activities."
```

Or specify an LLM provider:

```bash
python examples/fact_checking_demo.py --llm openai
```

### Running in Local Mode

Process an audio file directly:

```bash
python -m truth_checker --local --file path/to/audio.mp3
```

### Running the API Server

Start the API server to accept HTTP requests and WebSocket connections:

```bash
python -m truth_checker --server
```

#### API Endpoints

- **Transcription**:
  - `POST /api/transcribe`: Transcribe an uploaded audio file
  - `WebSocket /api/stream`: Stream audio for real-time transcription

- **Fact Checking**:
  - `POST /api/fact-check/claims`: Detect claims in a text transcript
  - `POST /api/fact-check/verify`: Verify a single claim
  - `POST /api/fact-check/analyze`: Analyze a transcript for claims and verify each one

### Mock Mode

For development without consuming API credits, you can use mock mode:

```bash
# Set the API key to a placeholder value
export DEEPGRAM_API_KEY=mock_api_key
```

This is useful for development and testing without consuming Deepgram API credits.

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
- ✅ Claim detection with LLM-based classification
- ✅ Fact-checking with RAG architecture (LangChain + LangGraph)
- ✅ Knowledge base vectorization with ChromaDB
- 🔄 Web-based knowledge retrieval (in progress)
- 🔄 Fact checking UI (planned)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Deepgram](https://deepgram.com/) for speech-to-text capabilities
- [FastAPI](https://fastapi.tiangolo.com/) for the API server
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) for audio processing
- [LangChain](https://python.langchain.com/) for RAG architecture
- [LangGraph](https://langchain-ai.github.io/langgraph/) for workflow orchestration
- [ChromaDB](https://docs.trychroma.com/) for vector storage