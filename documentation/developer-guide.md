# Developer Guide

This guide provides information for developers who want to contribute to the Truth Checker project or extend its functionality.

## Development Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/truth-checker.git
cd Truth-Checker
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env to add your API keys
```

## Project Structure

The project follows a hexagonal architecture:

```
truth_checker/
├── domain/           # Core business logic and models
│   ├── models.py     # Domain entities
│   └── ports.py      # Service interfaces
├── application/      # Use cases and application services
│   └── transcription_service.py  # Transcription orchestration
├── infrastructure/   # External services adapters
│   ├── services/     # External service implementations
│   └── repositories/ # Data persistence implementations
├── interfaces/       # User interfaces
│   ├── api/          # REST API and WebSockets
│   ├── audio/        # Audio capture and processing
│   └── clients/      # API client implementations
├── __main__.py       # Entry point
└── config.py         # Configuration management
```

## Architecture Guidelines

1. **Dependency Rule**: Dependencies must always point inward toward the domain
2. **Ports and Adapters**: External systems are integrated via adapters implementing domain ports
3. **Domain Purity**: The domain layer should have no dependencies on external frameworks
4. **Interface Segregation**: Keep interfaces focused and cohesive
5. **Testing**: All components should be testable in isolation

## Adding a New Feature

When adding a new feature, follow these steps:

1. **Domain Modeling**: 
   - Update or add domain entities and interfaces in the domain layer
   - Keep them focused on the core business logic

2. **Application Services**:
   - Implement use cases that orchestrate domain objects
   - Handle all application-specific concerns

3. **Infrastructure Adapters**:
   - Implement adapters for external services
   - Ensure they conform to domain port interfaces

4. **Interface Components**:
   - Add API endpoints or CLI commands
   - Connect them to application services

### Example: Adding a New Transcription Provider

1. **Domain Changes**: None (TranscriptionService port already exists)

2. **Infrastructure Layer**:
   - Create a new adapter implementing TranscriptionService
   - Implement the required methods

```python
# truth_checker/infrastructure/services/new_provider_service.py
from truth_checker.domain.ports import TranscriptionService
from truth_checker.domain.models import Transcript

class NewProviderTranscriptionService(TranscriptionService):
    """Transcription service using the new provider."""
    
    # Implement the required methods
    async def start_transcription(self, **kwargs):
        # Implementation...
        
    async def stop_transcription(self):
        # Implementation...
        
    # ... other methods
```

3. **Register the Service**:
   - Add factory method in the application layer
   - Update configuration to include the new provider

## Testing

### Running Tests

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=truth_checker
```

### Test Structure

Tests are organized by component type:
- `tests/domain/`: Domain model tests
- `tests/application/`: Application service tests
- `tests/infrastructure/`: Adapter implementation tests
- `tests/interfaces/`: Interface component tests

### Writing Tests

Example test for a domain entity:

```python
# tests/domain/test_models.py
from truth_checker.domain.models import Transcript

def test_transcript_creation():
    transcript = Transcript(
        text="Test transcript",
        confidence=0.95,
        is_final=True,
        start_time=1.0,
        end_time=2.0
    )
    
    assert transcript.text == "Test transcript"
    assert transcript.confidence == 0.95
    assert transcript.is_final is True
    assert transcript.start_time == 1.0
    assert transcript.end_time == 2.0
```

## Code Style and Quality

- Follow PEP 8 conventions
- Use type annotations throughout the codebase
- Document all public modules, classes, and functions
- Use descriptive names and keep functions small and focused

### Linting and Formatting

Format code with Black:
```bash
black truth_checker/
```

Check typing with MyPy:
```bash
mypy truth_checker/
```

Run linters:
```bash
flake8 truth_checker/
pylint truth_checker/
```

## Continuous Integration

The project uses GitHub Actions for CI:
- Runs tests on every push and pull request
- Enforces code quality with linters
- Checks typing with MyPy
- Generates test coverage reports

## Documentation

- Document all public interfaces
- Update README.md when adding major features
- Maintain API documentation when endpoints change
- Add examples for new features

## Deployment

### Building a Package

Create a distributable package:
```bash
python setup.py sdist bdist_wheel
```

### Docker Deployment

Build the Docker image:
```bash
docker build -t truth-checker .
```

Run the container:
```bash
docker run -p 8000:8000 -e DEEPGRAM_API_KEY=your_key truth-checker
```

## Contribution Process

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Ensure all tests pass and linting is clean
5. Submit a pull request with a clear description
6. Address review feedback
7. Your contribution will be merged once approved 