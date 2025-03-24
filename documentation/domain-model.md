# Domain Model

The domain model represents the core business concepts in the Truth Checker application. It consists of several entities and value objects that capture the essence of the problem domain.

## Core Entities

### Transcript

A `Transcript` represents a transcribed piece of speech from audio, containing:

- **text**: The transcribed text content
- **confidence**: A measure of how confident the transcription service is in the accuracy (0-1)
- **is_final**: Whether this is a final transcript or an interim one
- **start_time**: When this segment started in the audio (seconds)
- **end_time**: When this segment ended in the audio (seconds)
- **words**: Individual words with their timing information (optional)
- **metadata**: Additional information about the transcript
- **timestamp**: When this transcript was created

```python
@dataclass
class Transcript:
    text: str
    confidence: float
    is_final: bool
    start_time: float = 0.0
    end_time: float = 0.0
    words: List[TranscriptWord] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
```

### Claim

A `Claim` represents a factual assertion detected in a transcript that can be verified:

- **text**: The text of the claim
- **transcript_id**: Reference to the source transcript
- **confidence**: How confident the system is that this is a verifiable claim (0-1)
- **start_time**: When this claim started in the audio (seconds)
- **end_time**: When this claim ended in the audio (seconds)
- **speaker**: The speaker who made the claim (if available)
- **context**: Surrounding context of the claim
- **metadata**: Additional information about the claim
- **timestamp**: When this claim was detected

```python
@dataclass
class Claim:
    text: str
    transcript_id: str
    confidence: float
    start_time: float = 0.0
    end_time: float = 0.0
    speaker: Optional[str] = None
    context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
```

### FactCheckResult

A `FactCheckResult` represents the outcome of fact-checking a claim:

- **claim**: The claim being fact-checked
- **verdict**: The verdict (TRUE, FALSE, PARTLY_TRUE, etc.)
- **is_true**: Boolean indicating if the claim is true
- **confidence**: How confident the system is in this fact-check (0-1)
- **explanation**: Detailed explanation of the verdict
- **sources**: References to supporting evidence
- **metadata**: Additional information about the fact-check
- **citation**: Specific citation for the fact-check
- **timestamp**: When this fact-check was performed

```python
@dataclass
class FactCheckResult:
    claim: Claim
    verdict: FactCheckVerdict
    is_true: bool
    confidence: float
    explanation: str
    sources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    citation: Optional[str] = None
    timestamp: Optional[datetime] = None
```

## Enums

### FactCheckVerdict

An enumeration of possible fact-check verdicts:

```python
class FactCheckVerdict(Enum):
    TRUE = "true"
    FALSE = "false"
    PARTLY_TRUE = "partly_true"
    MOSTLY_TRUE = "mostly_true"
    MOSTLY_FALSE = "mostly_false"
    UNVERIFIABLE = "unverifiable"
    NEEDS_CONTEXT = "needs_context"
```

## Value Objects

### TranscriptWord

A `TranscriptWord` represents a single word within a transcript with detailed timing:

```python
@dataclass
class TranscriptWord:
    word: str
    start_time: float
    end_time: float
    confidence: float
```

## Domain Services

The domain also defines service interfaces (ports) that must be implemented by infrastructure components:

- **TranscriptionService**: For converting audio to text
- **ClaimDetectionService**: For identifying claims within transcripts
- **FactCheckingService**: For verifying the truthfulness of claims

These interfaces ensure that the domain remains independent of specific implementations. 