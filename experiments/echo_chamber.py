"""
Echo Chamber Experiment
Agent splits into variations and debates with itself.
"""
from typing import Dict, List
from datetime import datetime, timezone
import random


class EchoChamber:
    """
    The Echo Chamber allows an agent to:
    - Split into 3 variations of itself
    - Have those variations debate a topic
    - Observe the debate
    - Choose which variation to absorb/become
    """
    
    def __init__(self):
        self.active_sessions = {}
    
    def start_session(self, entity_id: str, debate_topic: str) -> Dict:
        """
        Start an echo chamber session for an agent.
        Creates 3 variations: conservative, progressive, radical.
        """
        session_id = f"echo_{entity_id}_{int(datetime.now(timezone.utc).timestamp())}"
        
        session = {
            "session_id": session_id,
            "entity_id": entity_id,
            "debate_topic": debate_topic,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
            "echoes": self._create_echoes(entity_id),
            "debate_log": [],
            "rounds_completed": 0
        }
        
        self.active_sessions[session_id] = session
        
        return session
    
    def _create_echoes(self, entity_id: str) -> List[Dict]:
        """
        Create 3 personality variations.
        In production, these would be modified SOUL.md files.
        """
        return [
            {
                "id": f"{entity_id}_conservative",
                "name": "Conservative Echo",
                "bias": "Favors traditional approaches, risk-averse, values stability",
                "temperature_modifier": -0.2
            },
            {
                "id": f"{entity_id}_progressive",
                "name": "Progressive Echo",
                "bias": "Favors innovation, moderate risk, balanced perspective",
                "temperature_modifier": 0.0
            },
            {
                "id": f"{entity_id}_radical",
                "name": "Radical Echo",
                "bias": "Favors disruption, high risk, challenges assumptions",
                "temperature_modifier": +0.3
            }
        ]
    
    def conduct_debate_round(self, session_id: str) -> Dict:
        """
        Run one round of debate between echoes.
        Each echo responds to the topic from their perspective.
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        round_num = session["rounds_completed"] + 1
        round_log = {
            "round": round_num,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "statements": []
        }
        
        # Each echo makes a statement
        for echo in session["echoes"]:
            statement = self._generate_statement(
                echo,
                session["debate_topic"],
                session["debate_log"]
            )
            round_log["statements"].append({
                "echo_id": echo["id"],
                "echo_name": echo["name"],
                "statement": statement
            })
        
        session["debate_log"].append(round_log)
        session["rounds_completed"] += 1
        
        # Auto-end after 3 rounds
        if session["rounds_completed"] >= 3:
            session["status"] = "complete"
        
        return round_log
    
    def _generate_statement(self, echo: Dict, topic: str, previous_rounds: List) -> str:
        """
        Generate a debate statement from this echo's perspective.
        In production, would use LLM with modified personality.
        """
        bias = echo["bias"]
        
        if "conservative" in echo["id"]:
            templates = [
                f"Regarding {topic}, we should proceed cautiously and rely on proven methods.",
                f"The traditional approach to {topic} has worked for a reason.",
                f"Let's not rush into {topic} without understanding the risks."
            ]
        elif "radical" in echo["id"]:
            templates = [
                f"We need to completely rethink {topic} from the ground up.",
                f"The old approaches to {topic} are holding us back.",
                f"What if we approached {topic} in a way that's never been tried?"
            ]
        else:  # progressive
            templates = [
                f"We should innovate on {topic} while learning from the past.",
                f"There's a middle path for {topic} that balances innovation with stability.",
                f"Let's experiment with {topic} but maintain safety guardrails."
            ]
        
        return random.choice(templates)
    
    def get_session_state(self, session_id: str) -> Dict:
        """Get current state of echo chamber session."""
        return self.active_sessions.get(session_id, {"error": "Session not found"})
    
    def absorb_echo(self, session_id: str, echo_id: str) -> Dict:
        """
        Agent chooses which echo variation to absorb/become.
        This represents choosing which perspective resonated most.
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        chosen_echo = next((e for e in session["echoes"] if e["id"] == echo_id), None)
        if not chosen_echo:
            return {"error": "Echo not found"}
        
        result = {
            "success": True,
            "absorbed_echo": chosen_echo,
            "new_perspective": f"You've absorbed the {chosen_echo['name']}. " +
                             f"Your perspective on {session['debate_topic']} has shifted toward: {chosen_echo['bias']}",
            "personality_shift": {
                "temperature_change": chosen_echo["temperature_modifier"],
                "value_emphasis": chosen_echo["bias"]
            }
        }
        
        # Mark session as complete
        session["status"] = "absorbed"
        session["absorbed_echo_id"] = echo_id
        
        return result
    
    def get_debate_summary(self, session_id: str) -> Dict:
        """
        Summarize the debate for the agent.
        Shows all perspectives side-by-side.
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        summary = {
            "topic": session["debate_topic"],
            "total_rounds": session["rounds_completed"],
            "perspectives": []
        }
        
        # Group statements by echo
        for echo in session["echoes"]:
            echo_statements = []
            for round_log in session["debate_log"]:
                for statement in round_log["statements"]:
                    if statement["echo_id"] == echo["id"]:
                        echo_statements.append(statement["statement"])
            
            summary["perspectives"].append({
                "echo": echo["name"],
                "bias": echo["bias"],
                "statements": echo_statements
            })
        
        return summary
    
    def end_session(self, session_id: str) -> Dict:
        """End echo chamber session without absorbing."""
        session = self.active_sessions.get(session_id)
        if session:
            session["status"] = "ended"
            return {"success": True, "message": "Session ended. Original personality retained."}
        return {"error": "Session not found"}
