# Infrastructure Layer

This directory contains implementations of ports defined in the domain layer, providing concrete adapters to external systems and libraries.

## Contents

- `services/`: External service implementations
  - `deepgram_service.py`: Implementation of the TranscriptionService using Deepgram
- `repositories/`: Data storage implementations

The infrastructure layer adapts external systems to the domain interfaces, isolating the domain from external concerns like APIs, databases, etc.

## Responsibilities

- Implement domain ports with concrete adapters
- Manage connections to external systems
- Handle data persistence and retrieval
- Implement technical capabilities required by the application

The infrastructure layer depends on the domain layer but not vice versa, following the dependency inversion principle. 