"""Truth Checker - Real-time fact verification system.

This module initializes the Truth Checker application, which:
1. Captures audio from various sources
2. Transcribes speech using Deepgram API
3. Detects factual claims in transcribed text
4. Verifies claims using RAG and trusted sources
5. Provides real-time feedback with explanations and sources
"""

__version__ = "0.1.0" 