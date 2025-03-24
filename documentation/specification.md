# Truth Checker - Project Specification

## Project Overview

The Truth Checker is a real-time fact-checking system designed to process audio content, transcribe speech, identify factual claims, and verify their truthfulness. The system aims to provide an automated solution for validating information presented in speeches, debates, interviews, and other audio sources.

## Core Objectives

1. **Audio Transcription**: Convert spoken content from various audio formats into accurate text transcripts
2. **Claim Detection**: Identify specific factual assertions within transcribed content
3. **Fact Checking**: Verify claims against trusted knowledge sources
4. **Results Presentation**: Present fact-checking results in a clear, timely manner
5. **Implement RAG Architecture**: Utilize Retrieval Augmented Generation for accurate fact verification
6. **Follow Hexagonal Architecture**: Ensure maintainability through clean separation of concerns

## Key Requirements

### Functional Requirements

#### Audio Processing

- Support multiple audio formats including MP3, WAV, WebM, OGG, FLAC, AAC, and raw PCM
- Process audio from both file uploads and real-time streams
- Handle various audio configurations (sample rates, encoding formats, channels)
- Provide fallback mechanisms when external services are unavailable

#### Transcription

- Accurately convert speech to text with confidence scoring
- Support real-time streaming transcription
- Maintain timing information for transcript segments
- Handle multiple speakers (diarization)
- Process various accents and languages
- Use Deepgram Nova-3 model for optimal transcription quality

#### Claim Detection

- Identify factual assertions within transcripts
- Distinguish facts from opinions, questions, and other non-factual statements
- Extract claim context and relevant supporting details
- Associate claims with specific speakers when available
- Implement context tracking to understand related statements
- Create prioritization mechanism for claim verification

#### Fact Checking

- Verify claims against reliable knowledge sources
- Provide nuanced verdicts beyond simple true/false (partly true, mostly false, etc.)
- Include confidence scores for verification results
- Cite sources and evidence for fact-check results
- Explain reasoning behind verdicts
- Integrate with external fact-checking databases

### Technical Requirements

#### Architecture

- Follow hexagonal architecture (ports and adapters) for clean separation of concerns
- Create clearly defined domain models and service interfaces
- Implement modular, pluggable external service adapters
- Maintain a pure domain model with no external dependencies

#### RAG Implementation

- Set up vector database (ChromaDB) for knowledge storage
- Implement document retrieval system
- Create embedding pipeline for knowledge base
- Implement query routing system (Adaptive RAG)
- Build fallback mechanisms (Corrective RAG)
- Develop hallucination detection (Self-RAG)

#### API and Interfaces

- Provide HTTP endpoints for file upload and processing
- Support WebSocket connections for real-time streaming
- Implement a command-line interface for local processing
- Ensure proper error handling and informative messages

#### Performance and Scalability

- Process audio in near real-time
- Support concurrent requests and connections
- Optimize resource usage for different deployment environments
- Include caching mechanisms where appropriate

#### Security and Reliability

- Implement robust error handling and recovery mechanisms
- Secure external API credentials and sensitive data
- Validate input data and parameters
- Log errors and important events for debugging

## Implementation Phases

### Phase 1: Backend Infrastructure / Audio Transcription (Completed)

- Implement audio processing infrastructure
- Integrate with Deepgram for speech-to-text conversion
- Support multiple audio formats
- Provide both HTTP and WebSocket interfaces
- Create command-line interface for local processing
- Set up Python environment and dependencies
- Implement real-time audio streaming to Deepgram API
- Process and parse transcription responses
- Handle connection events (open, close, transcript, metadata, error)

### Phase 2: Claim Detection System (Planned)

- Design claim detection algorithms and models
- Implement claim extraction from transcripts
- Add confidence scoring for detected claims
- Associate claims with transcript segments and timing
- Separate opinions from factual statements
- Implement context tracking for related statements

### Phase 3: RAG Architecture and Fact Checking (Planned)

- Set up vector database (ChromaDB) for knowledge storage
- Implement document retrieval system
- Create embedding pipeline for knowledge base
- Implement query routing system (Adaptive RAG)
- Integrate external fact-checking databases
- Implement web search capabilities
- Set up scientific database connections
- Design source reliability scoring system
- Develop claim matching algorithm
- Implement confidence scoring system
- Create explanation generation mechanism

### Phase 4: Client Development and UI (Future)

- Develop web-based user interface for displaying results
- Create visualization for fact-checking results
- Implement real-time updates for streaming results
- Develop user settings and preferences
- Build export and sharing capabilities
- Optimize performance and resource usage

## Technology Stack

- **Programming Language**: Python 3.9+
- **Audio Processing**: PyAudio, NumPy, Wave
- **Speech Recognition**: Deepgram API (Nova-3 model)
- **API Framework**: FastAPI
- **Async Runtime**: Uvicorn, asyncio
- **WebSockets**: Websockets, aiohttp
- **RAG Implementation**: LangChain + LangGraph
- **Vector Database**: ChromaDB
- **Testing**: pytest, pytest-asyncio
- **Configuration**: python-dotenv

## External Resources

- Fact-checking databases:
  - PolitiFact API (if available)
  - Google Fact Check Tools API
  - Possible partnerships with Full Fact or Snopes
- Knowledge sources:
  - Scientific databases
  - Academic journals
  - Trusted news sources
  - Historical records

## Success Metrics

The Truth Checker will be considered successful if it can:

1. Accurately transcribe speech from various audio sources
2. Correctly identify factual claims within transcribed content
3. Provide truthfulness assessments with reasonable accuracy
4. Process audio in near real-time
5. Handle different audio formats and configurations
6. Function reliably in both server and local modes

## Current Status

The project has successfully implemented the audio transcription phase (Phase 1), with support for multiple audio formats and interfaces (HTTP, WebSocket, and CLI). The system follows hexagonal architecture principles, with clean separation between domain, application, infrastructure, and interface layers.

Future work will focus on implementing claim detection and fact-checking functionality, as well as enhancing the WebSocket streaming capabilities and overall error handling. 