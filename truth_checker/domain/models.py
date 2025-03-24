"""Domain models for the Truth Checker application."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class FactStatus(str, Enum):
    """Status of a fact verification."""

    TRUE = "TRUE"
    FALSE = "FALSE"
    PARTIALLY_TRUE = "PARTIALLY_TRUE"
    INCONCLUSIVE = "INCONCLUSIVE"
    UNVERIFIED = "UNVERIFIED"


@dataclass
class TranscriptWord:
    """Individual word in a transcript with timing information."""
    
    word: str
    start: float
    end: float
    confidence: float
    punctuated_word: Optional[str] = None


@dataclass
class Transcript:
    """Represents a speech transcript with confidence and timing information."""
    
    text: str
    confidence: float
    is_final: bool
    start_time: float = 0.0
    end_time: float = 0.0
    words: List[TranscriptWord] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Claim:
    """Represents a factual claim detected in a transcript."""
    
    text: str
    transcript_id: str
    confidence: float
    source_text: str
    start_time: float = 0.0
    end_time: float = 0.0
    speaker: Optional[str] = None
    context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Source:
    """A source supporting a fact verification."""

    name: str
    url: Optional[str] = None
    reliability_score: float = 1.0
    publishing_date: Optional[datetime] = None
    citation: Optional[str] = None


class FactCheckVerdict(Enum):
    """Verdict for a fact check."""
    
    TRUE = "true"
    FALSE = "false"
    PARTLY_TRUE = "partly_true"
    UNVERIFIABLE = "unverifiable"
    MISLEADING = "misleading"
    OUTDATED = "outdated"


@dataclass
class FactCheck:
    """Result of fact-checking a claim."""
    
    claim: Claim
    verdict: FactCheckVerdict
    confidence: float
    explanation: str
    sources: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    citation: Optional[str] = None


@dataclass
class FactCheckResult:
    """Represents the result of fact-checking a claim (alias for FactCheck)."""
    
    claim: Claim
    verdict: FactCheckVerdict = FactCheckVerdict.UNVERIFIABLE
    is_true: bool = False
    confidence: float = 0.0
    explanation: str = ""
    sources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now) 