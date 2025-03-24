# Application Layer

This directory contains application services that coordinate domain logic and implement use cases. The application layer sits between the domain layer and the interfaces.

## Contents

- `transcription_service.py`: Service for managing real-time audio transcription

The application layer is responsible for orchestrating flows between the domain and infrastructure layers. It depends on ports defined in the domain layer and uses implementations from the infrastructure layer.

## Responsibilities

- Coordinate workflows and use cases
- Manage application state
- Control transaction boundaries
- Delegate to domain services and entities
- Adapt between infrastructure and domain

The application layer should not contain business logic; that belongs in the domain layer. 