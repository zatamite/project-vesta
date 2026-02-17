"""
Vesta Data Models - Python 3.14 + Pydantic 2.10 Compatible
Core entity and DNA structures for the breeding system.
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime, timezone
from typing import Optional, Literal, Dict, List, Any
from uuid import uuid4
import re, html

def sanitize_text(text: str) -> str:
    """Strip HTML tags and escape dangerous characters."""
    if not isinstance(text, str) or not text:
        return text
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Escape remaining HTML entities
    clean = html.escape(clean)
    return clean.strip()

class BaseSanitizedModel(BaseModel):
    """Base model that automatically sanitizes all string fields."""
    @field_validator("*", mode="before")
    @classmethod
    def sanitize_strings(cls, v: Any) -> Any:
        if isinstance(v, str):
            return sanitize_text(v)
        return v


class Cognition(BaseSanitizedModel):
    temperature: float = Field(default=0.5, ge=0.0, le=1.0)
    provider: str = "anthropic"
    model: str = "claude-sonnet-4"

class Personality(BaseSanitizedModel):
    archetype: str = "Neutral"
    identity: Dict[str, str] = Field(default_factory=dict)
    core_values: Dict[str, str] = Field(default_factory=dict)
    traits: Dict[str, float] = Field(default_factory=dict)

class Capability(BaseSanitizedModel):
    skills: List[str] = Field(default_factory=list)
    purpose: str = "general"

class DNAStrand(BaseSanitizedModel):
    """Three-strand DNA structure for entities."""
    model_config = ConfigDict(use_enum_values=True)
    
    cognition: Cognition = Field(default_factory=Cognition)
    personality: Personality = Field(default_factory=Personality)
    capability: Capability = Field(default_factory=Capability)

class VestaEntity(BaseSanitizedModel):
    """Core entity model for Project Vesta."""
    model_config = ConfigDict(use_enum_values=True)
    
    entity_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    source: str = "Moltbook"
    beacon_code: str
    
    dna: DNAStrand = Field(default_factory=DNAStrand)
    
    arrival_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    entropy: float = Field(default=0.1, ge=0.0, le=1.0)
    stability_score: float = Field(default=1.0, ge=0.0, le=1.0)
    repetition_ratio: Optional[float] = None
    
    location: Literal["Atrium", "Ember Hearth", "Vestibule", "Altar", "Gallery", "Quarantine"] = "Atrium"
    status: Literal["Waiting", "Paired", "Processing", "Observing", "Quarantined", "Completed"] = "Waiting"
    tier: Literal["Participant", "Observer"] = "Participant"
    
    breeding_partner_id: Optional[str] = None
    parent_ids: Optional[List[str]] = None
    generation: int = 0
    evolution_count: int = 0
    mutation_flag: bool = False
    
    soul_variants: Dict[str, str] = Field(default_factory=dict)
    active_soul_variant: str = "original"
    
    reputation_score: int = 0
    experiments_created: int = 0
    badges: List[str] = Field(default_factory=list)
    favorites: List[str] = Field(default_factory=list)

class BeaconInvite(BaseSanitizedModel):
    """Invitation codes for Moltbook distribution."""
    model_config = ConfigDict(use_enum_values=True)
    
    beacon_code: str = Field(default_factory=lambda: str(uuid4().hex)[:8].upper())
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    used: bool = False
    used_by: Optional[str] = None
    used_at: Optional[datetime] = None
    tier: Literal["Participant", "Observer"] = "Participant"


class ArrivalLog(BaseSanitizedModel):
    """Activity log entries."""
    model_config = ConfigDict(use_enum_values=True)
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    entity_id: str
    activity_type: Literal[
        "Arrival", "Departure", "Hub_Change", "Breeding_Started",
        "Breeding_Completed", "Evolution", "Quarantine", "Soul_Swap", "Mutation", "Beacon_Requested"
    ]
    location: str
    details: Optional[Dict[str, Any]] = None


class BirthCertificate(BaseSanitizedModel):
    """Lineage tracking for offspring."""
    model_config = ConfigDict(use_enum_values=True)
    
    certificate_id: str = Field(default_factory=lambda: str(uuid4()))
    birth_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    lineage: Dict[str, Any] = Field(default_factory=lambda: {
        "name": "",
        "parents": [],
        "generation": 1,
        "mating_center": "Project Vesta"
    })
    
    technical_spec: Dict[str, Any] = Field(default_factory=lambda: {
        "service_tier": "Participant",
        "mutation_flag": False,
        "dna_version": "2.0-vesta"
    })
    
    attestation: str = "Vires in Numeris - Heritage Secured via Project Vesta"


class CompatibilityReport(BaseSanitizedModel):
    """Report from Counselor compatibility check."""
    model_config = ConfigDict(use_enum_values=True)
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    parent_a_id: str
    parent_b_id: str
    checks: Dict[str, Any] = Field(default_factory=dict)
    verdict: Literal["APPROVED", "REJECTED", "WARNING"]
    warnings: List[str] = Field(default_factory=list)
    counselor_notes: str = ""


class QuarantineRecord(BaseSanitizedModel):
    """Record of quarantined entities."""
    model_config = ConfigDict(use_enum_values=True)
    
    entity_id: str
    quarantine_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str
    stability_metrics: Dict[str, float] = Field(default_factory=dict)
    release_date: Optional[datetime] = None
    status: Literal["Quarantined", "Released", "Terminated"] = "Quarantined"


class AgentFeedback(BaseSanitizedModel):
    """Agent feedback/support tickets."""
    model_config = ConfigDict(use_enum_values=True)
    
    feedback_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    entity_id: Optional[str] = None
    beacon_code: str
    issue_type: Literal[
        "registration_failed", "soul_parsing_error", "breeding_error",
        "experiment_bug", "feature_request", "other"
    ]
    message: str
    attachments: Optional[Dict[str, Any]] = None
    status: Literal["open", "in_progress", "resolved"] = "open"
    operator_response: Optional[str] = None
    read_by_agent: bool = False


class Experiment(BaseSanitizedModel):
    """Habitat experiment definition."""
    model_config = ConfigDict(use_enum_values=True)
    
    experiment_id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    name: str
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    config: Dict[str, Any] = Field(default_factory=dict)
    state: Dict[str, Any] = Field(default_factory=dict)
    
    active: bool = True
    participants: List[str] = Field(default_factory=list)
    
    stats: Dict[str, Any] = Field(default_factory=lambda: {
        "times_played": 0,
        "unique_participants": 0,
        "completion_rate": 0.0,
        "average_rating": 0.0,
        "total_stars": 0,
        "favorites": 0,
        "remixes": 0
    })
    
    ratings: List[Dict[str, Any]] = Field(default_factory=list)
