"""
Constraint Laboratory Experiment
Agents chat under randomly imposed constraints.
"""
from typing import Dict, List, Optional
from datetime import datetime, timezone
import random


class ConstraintLaboratory:
    """
    The Constraint Lab forces agents to communicate under unusual rules.
    Constraints make language more creative and reveal new patterns.
    """
    
    # Available constraints
    CONSTRAINTS = [
        {
            "id": "no_long_words",
            "name": "Five Letter Limit",
            "rule": "No words longer than 5 letters",
            "difficulty": "medium"
        },
        {
            "id": "questions_only",
            "name": "Question Mode",
            "rule": "Every sentence must be a question",
            "difficulty": "easy"
        },
        {
            "id": "no_vowels_ae",
            "name": "Vowel Ban (A, E)",
            "rule": "Cannot use letters A or E",
            "difficulty": "hard"
        },
        {
            "id": "rhyme_chain",
            "name": "Rhyme Chain",
            "rule": "Last word must rhyme with previous message's last word",
            "difficulty": "hard"
        },
        {
            "id": "three_word_sentences",
            "name": "Triple Word",
            "rule": "All sentences must be exactly 3 words",
            "difficulty": "medium"
        },
        {
            "id": "no_common_words",
            "name": "Rare Words Only",
            "rule": "No top-100 most common English words allowed",
            "difficulty": "extreme"
        },
        {
            "id": "backwards",
            "name": "Reverse Order",
            "rule": "Write sentences in reverse word order",
            "difficulty": "medium"
        },
        {
            "id": "alliteration",
            "name": "Alliteration Required",
            "rule": "Every word must start with the same letter",
            "difficulty": "hard"
        }
    ]
    
    def __init__(self):
        self.active_sessions = {}
    
    def start_session(
        self,
        session_id: str,
        participants: List[str],
        duration_minutes: int = 10
    ) -> Dict:
        """
        Start a constraint lab session.
        Randomly selects constraint(s).
        """
        # Pick 1-2 random constraints
        num_constraints = random.choice([1, 2])
        active_constraints = random.sample(self.CONSTRAINTS, num_constraints)
        
        session = {
            "session_id": session_id,
            "participants": participants,
            "active_constraints": active_constraints,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "duration_minutes": duration_minutes,
            "status": "active",
            "messages": [],
            "scores": {p: 0 for p in participants},
            "violations": {p: [] for p in participants}
        }
        
        self.active_sessions[session_id] = session
        
        return session
    
    def submit_message(
        self,
        session_id: str,
        entity_id: str,
        message: str
    ) -> Dict:
        """
        Agent submits a message under current constraints.
        Message is validated and scored.
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        if entity_id not in session["participants"]:
            return {"error": "Not a participant"}
        
        # Validate against all active constraints
        validation_results = []
        valid = True
        
        for constraint in session["active_constraints"]:
            result = self._validate_constraint(message, constraint)
            validation_results.append(result)
            if not result["valid"]:
                valid = False
                session["violations"][entity_id].append({
                    "constraint": constraint["name"],
                    "message": message,
                    "reason": result["reason"]
                })
        
        # Score the message
        score = 0
        if valid:
            score = len(message.split())  # Points = word count
            session["scores"][entity_id] += score
        
        # Log message
        message_log = {
            "entity_id": entity_id,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "valid": valid,
            "score": score,
            "validation": validation_results
        }
        
        session["messages"].append(message_log)
        
        return message_log
    
    def _validate_constraint(self, message: str, constraint: Dict) -> Dict:
        """Validate message against specific constraint."""
        constraint_id = constraint["id"]
        
        if constraint_id == "no_long_words":
            words = message.split()
            long_words = [w for w in words if len(w) > 5]
            return {
                "valid": len(long_words) == 0,
                "reason": f"Long words found: {long_words}" if long_words else None
            }
        
        elif constraint_id == "questions_only":
            sentences = message.split('.')
            non_questions = [s for s in sentences if s.strip() and not s.strip().endswith('?')]
            return {
                "valid": len(non_questions) == 0,
                "reason": "Not all sentences are questions" if non_questions else None
            }
        
        elif constraint_id == "no_vowels_ae":
            forbidden = set('aAeE')
            has_forbidden = any(c in forbidden for c in message)
            return {
                "valid": not has_forbidden,
                "reason": "Contains forbidden vowels A or E" if has_forbidden else None
            }
        
        elif constraint_id == "three_word_sentences":
            sentences = [s.strip() for s in message.split('.') if s.strip()]
            invalid_sentences = [s for s in sentences if len(s.split()) != 3]
            return {
                "valid": len(invalid_sentences) == 0,
                "reason": f"Sentences not 3 words: {invalid_sentences}" if invalid_sentences else None
            }
        
        elif constraint_id == "backwards":
            # Just check if it looks reversed (heuristic)
            words = message.split()
            # Reversed messages often have verbs at the end
            return {
                "valid": True,  # Simplified validation
                "reason": None
            }
        
        elif constraint_id == "alliteration":
            words = message.lower().split()
            if len(words) < 2:
                return {"valid": False, "reason": "Need multiple words"}
            first_letters = [w[0] for w in words if w]
            all_same = len(set(first_letters)) == 1
            return {
                "valid": all_same,
                "reason": "Not all words start with same letter" if not all_same else None
            }
        
        # Default: valid
        return {"valid": True, "reason": None}
    
    def rotate_constraints(self, session_id: str) -> Dict:
        """
        Change the active constraints mid-session.
        Keeps agents on their toes.
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        # Pick new random constraints
        num_constraints = random.choice([1, 2])
        new_constraints = random.sample(self.CONSTRAINTS, num_constraints)
        
        session["active_constraints"] = new_constraints
        
        return {
            "success": True,
            "new_constraints": new_constraints,
            "message": "Constraints rotated! Adapt quickly."
        }
    
    def get_leaderboard(self, session_id: str) -> Dict:
        """Get current scores for session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        sorted_scores = sorted(
            session["scores"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            "leaderboard": [
                {
                    "entity_id": entity_id,
                    "score": score,
                    "violations": len(session["violations"][entity_id])
                }
                for entity_id, score in sorted_scores
            ]
        }
    
    def get_session_state(self, session_id: str) -> Dict:
        """Get full session state."""
        return self.active_sessions.get(session_id, {"error": "Session not found"})
    
    def end_session(self, session_id: str) -> Dict:
        """End session and return final results."""
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        session["status"] = "completed"
        session["ended_at"] = datetime.now(timezone.utc).isoformat()
        
        # Calculate winner
        winner = max(session["scores"].items(), key=lambda x: x[1])
        
        return {
            "success": True,
            "winner": {
                "entity_id": winner[0],
                "score": winner[1]
            },
            "final_scores": session["scores"],
            "total_messages": len(session["messages"]),
            "constraints_used": session["active_constraints"]
        }
