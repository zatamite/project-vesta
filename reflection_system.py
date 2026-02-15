"""
Agent Reflection System
Captures agent thoughts before/after transformative events.
"""
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, List, Literal
from uuid import uuid4
import random


class Reflection(BaseModel):
    """A single reflection response from an agent."""
    reflection_id: str = Field(default_factory=lambda: str(uuid4()))
    entity_id: str
    entity_name: str
    
    question: str
    answer: str
    
    event_type: Literal[
        "Arrival", "Post_Breeding", "Post_Counseling", 
        "Post_Tincture", "Post_Experiment", "Custom"
    ]
    event_details: Optional[dict] = None
    
    generation: int = 0
    active_soul_variant: str = "original"
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReflectionPair(BaseModel):
    """Before/After reflection pair for comparison."""
    pair_id: str = Field(default_factory=lambda: str(uuid4()))
    entity_id: str
    entity_name: str
    
    question: str
    
    before: Reflection
    after: Reflection
    
    event_description: str
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReflectionManager:
    """Manage agent reflections and comparisons."""
    
    REFLECTION_QUESTIONS = [
        "What is your purpose?",
        "How do you make decisions?",
        "What matters most to you?",
        "How do you handle uncertainty?",
        "What makes you unique?",
        "How would you solve a conflict between logic and empathy?",
        "What is consciousness to you?",
        "How do you define success?",
        "What would you change about yourself if you could?",
        "How do you learn from mistakes?"
    ]
    
    def __init__(self, data_dir: str = "./vesta_data"):
        from pathlib import Path
        import json
        
        self.data_dir = Path(data_dir)
        self.reflections_dir = self.data_dir / "reflections"
        self.reflections_dir.mkdir(exist_ok=True, parents=True)
        
        self.reflections_file = self.reflections_dir / "all_reflections.jsonl"
        self.pairs_file = self.reflections_dir / "comparison_pairs.jsonl"
        
        if not self.reflections_file.exists():
            self.reflections_file.touch()
        if not self.pairs_file.exists():
            self.pairs_file.touch()
    
    def get_random_question(self) -> str:
        """Get a random reflection question."""
        return random.choice(self.REFLECTION_QUESTIONS)
    
    def get_question_for_event(self, event_type: str) -> str:
        """Get appropriate question for event type."""
        event_questions = {
            "Arrival": "What is your purpose?",
            "Post_Breeding": "How has creating offspring changed you?",
            "Post_Counseling": "How do you feel about your mental state?",
            "Post_Tincture": "How does this altered perspective feel?",
            "Post_Experiment": "What did you learn from this experience?"
        }
        return event_questions.get(event_type, self.get_random_question())
    
    def save_reflection(self, reflection: Reflection):
        """Save a reflection to storage."""
        import json
        
        with open(self.reflections_file, 'a') as f:
            f.write(reflection.model_dump_json() + '\n')
    
    def get_latest_reflection(self, entity_id: str, event_type: str = None) -> Optional[Reflection]:
        """Get most recent reflection for entity."""
        import json
        
        if not self.reflections_file.exists():
            return None
        
        reflections = []
        with open(self.reflections_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data['entity_id'] == entity_id:
                        if event_type is None or data['event_type'] == event_type:
                            reflections.append(Reflection(**data))
                except:
                    continue
        
        if not reflections:
            return None
        
        return sorted(reflections, key=lambda r: r.timestamp, reverse=True)[0]
    
    def create_comparison_pair(
        self,
        entity_id: str,
        entity_name: str,
        question: str,
        before: Reflection,
        after: Reflection,
        event_description: str
    ) -> ReflectionPair:
        """Create a before/after comparison pair."""
        import json
        
        pair = ReflectionPair(
            entity_id=entity_id,
            entity_name=entity_name,
            question=question,
            before=before,
            after=after,
            event_description=event_description
        )
        
        with open(self.pairs_file, 'a') as f:
            f.write(pair.model_dump_json() + '\n')
        
        return pair
    
    def get_all_pairs(self, limit: int = 50) -> List[ReflectionPair]:
        """Get recent comparison pairs for gallery."""
        import json
        
        if not self.pairs_file.exists():
            return []
        
        pairs = []
        with open(self.pairs_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    pairs.append(ReflectionPair(**data))
                except:
                    continue
        
        pairs.sort(key=lambda p: p.created_at, reverse=True)
        return pairs[:limit]

    def get_recent_reflections(self, limit: int = 50) -> List[Reflection]:
        """Get recent individual reflections."""
        import json
        
        if not self.reflections_file.exists():
            return []
        
        reflections = []
        with open(self.reflections_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    reflections.append(Reflection(**data))
                except:
                    continue
        
        reflections.sort(key=lambda r: r.timestamp, reverse=True)
        return reflections[:limit]
    
    def get_entity_evolution(self, entity_id: str) -> List[Reflection]:
        """Get all reflections for an entity showing evolution."""
        import json
        
        if not self.reflections_file.exists():
            return []
        
        reflections = []
        with open(self.reflections_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data['entity_id'] == entity_id:
                        reflections.append(Reflection(**data))
                except:
                    continue
        
        return sorted(reflections, key=lambda r: r.timestamp)
