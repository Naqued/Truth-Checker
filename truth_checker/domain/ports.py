"""Interfaces for the Truth Checker application following hexagonal architecture."""

import abc
from typing import AsyncIterator, Callable, Dict, List, Optional, Any

from truth_checker.domain.models import Claim, FactCheckResult, Transcript


class TranscriptionService(abc.ABC):
    """Interface for transcription services."""

    @abc.abstractmethod
    async def start_transcription(
        self, 
        mimetype: str = "audio/raw",
        encoding: Optional[str] = None,
        sample_rate: Optional[int] = None,
        channels: Optional[int] = None,
        **kwargs
    ) -> None:
        """Start the transcription service.
        
        Args:
            mimetype: MIME type of the audio data
            encoding: Audio encoding (e.g., 'linear16', 'opus', 'mulaw')
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels
            **kwargs: Additional parameters for the specific service
        """
        pass

    @abc.abstractmethod
    async def stop_transcription(self) -> None:
        """Stop the transcription service."""
        pass

    @abc.abstractmethod
    async def send_audio(self, audio_data: bytes) -> None:
        """Send audio data to the transcription service.
        
        Args:
            audio_data: Raw audio data
        """
        pass

    @abc.abstractmethod
    async def get_transcripts(self) -> AsyncIterator[Transcript]:
        """Get a stream of transcripts.
        
        Yields:
            Transcript objects
        """
        pass

    @abc.abstractmethod
    def register_transcript_handler(self, handler: Callable[[Transcript], None]) -> None:
        """Register a function to be called for each transcript.
        
        Args:
            handler: Function that takes a Transcript object as an argument
        """
        pass


class ClaimDetectionService(abc.ABC):
    """Interface for claim detection services."""

    @abc.abstractmethod
    async def detect_claims(self, transcript: Transcript) -> List[Claim]:
        """Detect claims in a transcript.

        Args:
            transcript: The transcript to analyze

        Returns:
            List of detected claims
        """
        pass


class FactCheckingService(abc.ABC):
    """Interface for fact-checking services."""

    @abc.abstractmethod
    async def check_claim(self, claim: Claim) -> FactCheckResult:
        """Check the factual accuracy of a claim.

        Args:
            claim: The claim to verify

        Returns:
            Result of the fact check
        """
        pass

    @abc.abstractmethod
    def register_result_handler(self, handler: Callable[[FactCheckResult], None]) -> None:
        """Register a function to be called for each fact check result.

        Args:
            handler: Function that takes a FactCheckResult object as an argument
        """
        pass


class KnowledgeRepository(abc.ABC):
    """Interface for knowledge repositories."""

    @abc.abstractmethod
    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search the knowledge repository.

        Args:
            query: The search query
            **kwargs: Additional search parameters

        Returns:
            List of search results
        """
        pass

    @abc.abstractmethod
    async def add_document(self, document: Dict[str, Any]) -> str:
        """Add a document to the knowledge repository.

        Args:
            document: The document to add

        Returns:
            ID of the added document
        """
        pass 