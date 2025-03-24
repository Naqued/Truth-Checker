# Truth Checker Documentation

This directory contains comprehensive documentation for the Truth Checker project.

## Contents

- [Specification](raw-Specification-UseCase.md) - Project goals, requirements and implementation phases (Updated)
- [Project Analysis](first-Analyze-Project-Truth-Checker.md) - Current state and future development areas (Updated)
- [Architecture Overview](architecture.md) - Overall system architecture and design patterns
- [Domain Model](domain-model.md) - Core domain entities and value objects
- [API Reference](api-reference.md) - API endpoints and response formats
- [User Guide](user-guide.md) - Guide for end-users of the system
- [Developer Guide](developer-guide.md) - Guide for developers contributing to the project
- [Audio Format Support](audio-format-support.md) - Details on supported audio formats

## Recent Updates

- **March 2025**: Updated project specification and analysis documents to reflect the completed Deepgram STT integration
- **March 2025**: Added implementation details for the WebSocket streaming functionality
- **March 2025**: Documented mock mode for development without API credentials

## Project Structure

The Truth Checker project follows a hexagonal architecture (ports and adapters) with the following high-level structure:

```
truth_checker/
├── domain/           # Core business logic and entity models
├── application/      # Use cases and application services
├── infrastructure/   # External services and adapters
├── interfaces/       # User interfaces and API endpoints
```

## Current Project Status

- ✅ **Phase 1 (Backend Infrastructure)**: 
  - Completed Deepgram STT integration
  - Implemented HTTP and WebSocket endpoints
  - Added support for multiple audio formats
  - Created mock mode for development
  
- 🔄 **In Progress**:
  - Claim detection algorithm development
  - RAG architecture planning
  - Knowledge base design

See the [Specification](raw-Specification-UseCase.md) and [Project Analysis](first-Analyze-Project-Truth-Checker.md) documents for more details on the current status and next steps. 