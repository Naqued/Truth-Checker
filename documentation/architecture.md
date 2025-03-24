# Architecture Overview

The Truth Checker application follows a hexagonal architecture (also known as ports and adapters) to ensure clean separation of concerns and maintainability.

## Hexagonal Architecture

The hexagonal architecture organizes the system into loosely coupled components that can be developed, tested, and maintained independently. The core principle is to isolate the domain logic from external concerns.

![Hexagonal Architecture](https://user-images.githubusercontent.com/123456789/placeholder-for-hexagonal-image.png)

The architecture consists of:

1. **Domain Layer** (center) - Core business logic and entity models
2. **Application Layer** - Orchestrates the domain to fulfill use cases
3. **Infrastructure Layer** - Implements adapters for external systems
4. **Interface Layer** - Provides ways for users to interact with the system

## Components

### Domain Layer

The domain layer contains:
- **Models**: Core business entities like `Transcript`, `Claim`, and `FactCheckResult`
- **Ports**: Interfaces that define what external adapters must implement

The domain has no dependencies on external systems and defines what the system does.

### Application Layer

The application layer contains:
- **Services**: Orchestrate domain objects to fulfill use cases
- **DTOs**: Data transfer objects for communicating with external systems

Application services use domain objects via their interfaces (ports).

### Infrastructure Layer

The infrastructure layer contains:
- **Services**: Implementations of domain ports, like `DeepgramTranscriptionService`
- **Repositories**: Data persistence implementations
- **External API clients**: Connectors to third-party services

### Interface Layer

The interface layer contains:
- **API**: HTTP and WebSocket endpoints
- **CLI**: Command-line interface
- **Audio I/O**: Audio capture and processing

## Data Flow

1. User request enters through an interface (API, CLI)
2. Interface layer passes request to application services
3. Application services orchestrate domain objects
4. Domain logic is executed
5. Results flow back through the layers in reverse order

## Dependency Rule

The most important rule is that dependencies always point inward:
- Interfaces depend on application
- Application depends on domain
- Domain depends on nothing external

This ensures that the domain remains pure and isolated from external concerns, making the system more maintainable and testable. 