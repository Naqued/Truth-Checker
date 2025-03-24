# Interfaces Layer

This directory contains components that interact with the outside world, such as API endpoints, UI components, and audio input/output handlers.

## Contents

- `api/`: API endpoints and controllers
- `audio/`: Audio capture and processing interfaces
  - `audio_interface.py`: Interface for capturing audio from different sources

The interfaces layer is responsible for converting external data formats to internal domain models and vice versa.

## Responsibilities

- Present data to users or external systems
- Accept input from users or external systems
- Convert between external formats and domain models
- Handle HTTP requests/responses, WebSockets, etc.
- Manage audio input and output

The interfaces layer depends on the application layer to execute use cases based on external input. 