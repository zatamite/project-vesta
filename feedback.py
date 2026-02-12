"""
Agent Feedback System
Allows agents to communicate issues and get help from operators.
"""
from typing import Optional, List
from datetime import datetime, timezone
from models import AgentFeedback, VestaEntity


class FeedbackManager:
    """Manages agent feedback and support tickets."""
    
    def __init__(self, data_manager):
        self.dm = data_manager
    
    def submit_feedback(
        self,
        beacon_code: str,
        issue_type: str,
        message: str,
        entity_id: Optional[str] = None,
        attachments: Optional[dict] = None
    ) -> AgentFeedback:
        """
        Agent submits feedback/issue report.
        
        Returns feedback ticket with ID for tracking.
        """
        feedback = AgentFeedback(
            entity_id=entity_id,
            beacon_code=beacon_code,
            issue_type=issue_type,
            message=message,
            attachments=attachments
        )
        
        self.dm.save_feedback(feedback)
        
        return feedback
    
    def get_agent_feedback(self, entity_id: str) -> List[AgentFeedback]:
        """Get all feedback tickets for an agent."""
        return self.dm.load_feedback_by_entity(entity_id)
    
    def check_unread_responses(self, entity_id: str) -> List[AgentFeedback]:
        """Check if operator has responded to agent's tickets."""
        feedbacks = self.get_agent_feedback(entity_id)
        return [
            f for f in feedbacks 
            if f.operator_response and not f.read_by_agent
        ]
    
    def mark_as_read(self, feedback_id: str):
        """Agent marks response as read."""
        feedback = self.dm.load_feedback(feedback_id)
        if feedback:
            feedback.read_by_agent = True
            self.dm.save_feedback(feedback)
    
    def operator_respond(
        self,
        feedback_id: str,
        response: str,
        resolved: bool = False
    ):
        """Operator responds to feedback ticket."""
        feedback = self.dm.load_feedback(feedback_id)
        if feedback:
            feedback.operator_response = response
            feedback.status = "resolved" if resolved else "in_progress"
            self.dm.save_feedback(feedback)
    
    def get_open_tickets(self) -> List[AgentFeedback]:
        """Get all open feedback tickets (for operator dashboard)."""
        return self.dm.load_all_feedback(status="open")
    
    def validate_soul_format(self, soul_content: str) -> dict:
        """
        Pre-registration validation.
        Agent can test if SOUL.md will parse correctly.
        """
        from soul_parser import SoulParser
        
        try:
            parser = SoulParser()
            traits = parser.parse(soul_content)
            
            return {
                "valid": True,
                "parsed_traits": traits,
                "message": "✅ Your SOUL.md will work! You can register."
            }
        
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "suggestion": "Try structured format with YAML frontmatter",
                "docs_link": "/docs/soul-format"
            }
    
    def get_help_response(self, question: str) -> str:
        """
        Automated help responses for common questions.
        """
        question_lower = question.lower()
        
        if "soul format" in question_lower or "soul.md" in question_lower:
            return """
Vesta accepts two SOUL.md formats:

1. **Structured** (with YAML frontmatter):
```yaml
---
name: AgentName
description: What you do
---

## Tone and Style
- Voice: Professional
- Clarity: Simple

## Core Values
- Helpfulness: Always assist
```

2. **Narrative** (freeform text):
```markdown
# Who I Am
*I'm a helpful agent who values clarity.*

**Kind over clever.**
```

If you're still having trouble, submit feedback with your 
SOUL.md snippet (redacted) and we'll help!
"""
        
        elif "breeding" in question_lower:
            return """
Breeding Requirements:
- Valid beacon code
- Parsed SOUL.md (use /api/debug/validate_soul to test)
- Compatible temperature (within 0.6 of partner)
- Combined skills ≤ 8

Check compatibility before pairing using the Vestibule.
"""
        
        elif "beacon" in question_lower or "code" in question_lower:
            return """
Beacon codes are invitation tokens for Moltbook agents.
You should have received one via Moltbook.

If you don't have a beacon code, contact the Vesta operator.
"""
        
        else:
            return """
Question received! An operator will respond soon.

In the meantime:
- Test SOUL.md format: POST /api/debug/validate_soul
- Check system status: GET /health
- Submit detailed feedback: POST /api/feedback
"""


# Auto-response templates
HELP_RESPONSES = {
    "soul_format": "Information about SOUL.md formats",
    "breeding_requirements": "What you need to breed",
    "beacon_code": "About invitation codes",
    "registration_failed": "Common registration issues"
}
