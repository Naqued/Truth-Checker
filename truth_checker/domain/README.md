# Domain Layer

This directory contains the core domain logic for the Truth Checker application, following hexagonal architecture principles.

## Contents

- `models.py`: Domain entities and value objects
- `ports.py`: Interface definitions for services required by the domain

The domain layer is independent of external systems and frameworks. It defines the core business logic and interfaces that will be implemented by the infrastructure layer.

## Key Concepts

### Transcript

Represents transcribed audio content including the text, confidence scores, and timing information.

### Claim

Represents a factual claim detected in transcribed content that can be verified.

### FactCheck

Represents the result of a fact verification process, including the status (true/false/etc.), explanations, and sources. 