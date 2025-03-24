# Truth Checker Project Development Handbook

## Project Overview

We are developing an AI agent that can listen to audio in real-time, transcribe it using the Deepgram API, and check the factual accuracy of claims against reliable databases, scientific sources, and trusted fact-checkers. The system will display results on screen, indicating whether statements are true or false, along with explanations and sources.

This document tracks our development progress, tasks, and implementation details.

## Project Goals

1. Build a real-time audio fact-checking system
2. Implement Retrieval Augmented Generation (RAG) architecture
3. Follow hexagonal architecture principles for maintainability
4. Create a modular system with separate backend and client components
5. Deliver accurate fact-checking with minimal latency

## Development Roadmap

### Phase 1: Backend Infrastructure

#### 1.1 Deepgram STT Integration (✅ Completed)

- ✅ Set up Python environment and dependencies
- ✅ Implement real-time audio streaming to Deepgram API
- ✅ Process and parse transcription responses
- ✅ Handle connection events (open, close, transcript, metadata, error)
- ✅ Test with sample audio streams

**Technical Notes:**
- Successfully integrated the Deepgram Python SDK for audio streaming
- Implemented robust error handling for network issues and API key validation
- Added support for multiple audio formats (MP3, WAV, WebM, OGG, FLAC, PCM)
- Implemented a mock mode for development without consuming API credits
- Used HTTP endpoint for file upload and WebSocket for real-time streaming
- Created queuing system for handling transcripts across threads
- Implemented proper cleanup of resources when connections close

**Implementation Approach:**
```
✅ Installed Deepgram SDK and dependencies
✅ Created connection to Deepgram API using API key from environment variables
✅ Set up streaming connection with parameters (model=nova-2, language=en-US, smart_format=true)
✅ Implemented event handlers for the streaming connection
✅ Processed audio input and sent to Deepgram
✅ Parsed and processed transcription responses
```

#### 1.2 Claim Detection System (Not Started)

- Develop algorithm to identify verifiable claims in transcribed text
- Separate opinions from factual statements
- Implement context tracking to understand related statements
- Create prioritization mechanism for claim verification

#### 1.3 RAG Architecture Implementation (Not Started)

- Set up vector database (ChromaDB) for knowledge storage
- Implement document retrieval system
- Create embedding pipeline for knowledge base
- Implement query routing system (Adaptive RAG)
- Build fallback mechanisms (Corrective RAG)
- Develop hallucination detection (Self-RAG)

### Phase 2: Fact-Checking Core

#### 2.1 Knowledge Base Integration (Not Started)

- Integrate external fact-checking databases
- Implement web search capabilities
- Set up scientific database connections
- Design source reliability scoring system
- Create knowledge retrieval API

#### 2.2 Fact Verification Engine (Not Started)

- Develop claim matching algorithm
- Implement confidence scoring system
- Create explanation generation mechanism
- Design source attribution system
- Build response formatting system

### Phase 3: Client Development

#### 3.1 API Layer (Partially Completed)

- ✅ Design RESTful API endpoints
- ✅ Implement WebSocket for real-time updates
- Create authentication system
- Develop rate limiting and caching
- Build error handling middleware

#### 3.2 Client Application (Not Started)

- Design user interface for displaying results
- Implement audio capture functionality
- Create visualization for fact-checking results
- Develop user settings and preferences
- Build export and sharing capabilities

## Current Progress

- ✅ Completed project analysis and architecture design
- ✅ Implemented Deepgram as our STT solution with real-time transcription
- ✅ Created HTTP and WebSocket endpoints for audio processing
- ✅ Developed mock mode for testing without API credits
- ✅ Integrated audio file processing for various formats
- 🔄 Working on claim detection algorithm
- 🔄 Planning RAG architecture implementation

## Next Steps

1. ✅ Set up development environment
2. ✅ Implement basic Deepgram integration
3. ✅ Test audio streaming capabilities
4. Begin building claim detection algorithm
5. Design initial database schema for knowledge base

## Technical Decisions

### Speech-to-Text: Deepgram

We selected Deepgram for STT because:
- ✅ Excellent real-time transcription capabilities
- ✅ Support for streaming audio with WebSocket
- ✅ High accuracy with the Nova-2 model
- ✅ Robust SDK support for Python
- ✅ Smart formatting features for improved readability

**Implementation Insights:**
- API key should be stored in a `.env` file at the project root
- WebSocket connection requires proper event handling for transcripts
- Error handling needs to account for network issues and API limits
- Mock mode is essential for development without consuming API credits

### RAG Implementation: LangChain + LangGraph

We'll use LangChain and LangGraph because:
- LangChain provides excellent tools for building RAG systems
- LangGraph enables cyclical computational capabilities
- Both integrate well with vector databases
- Support for advanced RAG techniques (Adaptive, Corrective, Self-RAG)
- Active community and ongoing development

### Database: ChromaDB

ChromaDB was selected because:
- Open-source vector database
- Good performance for semantic search
- Easy integration with Python
- Supports embeddings from various models
- Lightweight deployment options

## Resources

- [Deepgram Live Streaming Documentation](https://developers.deepgram.com/docs/live-streaming-audio)
- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [ChromaDB Documentation](https://docs.trychroma.com/)

## Team

- Backend Development: [Team Members]
- AI/ML Integration: [Team Members]
- Client Development: [Team Members]
- Project Management: [Team Members]

## Project Status: Phase 1 - Backend Infrastructure