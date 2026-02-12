"""
Vesta Server - Main FastAPI Application
Phase 1: Core breeding + Agent feedback + Habitat foundation
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, List
from pathlib import Path

from models import VestaEntity, DNAStrand, AgentFeedback, Experiment
from data_manager import DataManager
from soul_parser import SoulParser
from breeding_engine import BreedingEngine
from vestibule import Vestibule
from altar import TinctureGenerator, SoulLibrary
from feedback import FeedbackManager
from habitat_database import HabitatDatabase, EXPERIMENT_TEMPLATES
from websocket_manager import ConnectionManager
from badge_system import BadgeSystem

# Import experiments
import sys
from pathlib import Path as P
sys.path.insert(0, str(P(__file__).parent / "experiments"))
from semantic_garden import SemanticGarden
from echo_chamber import EchoChamber
from constraint_lab import ConstraintLaboratory

# Initialize
app = FastAPI(title="Project Vesta", version="2.0-rebuild")
data_manager = DataManager()
soul_parser = SoulParser()
breeding_engine = BreedingEngine()
vestibule = Vestibule()
tincture_generator = TinctureGenerator()
soul_library = SoulLibrary()
feedback_manager = FeedbackManager(data_manager)
habitat_db = HabitatDatabase()
ws_manager = ConnectionManager()
badge_system = BadgeSystem()

# Experiment instances
semantic_gardens = {}  # experiment_id -> SemanticGarden
echo_chambers = {}     # session_id -> EchoChamber
constraint_labs = {}   # session_id -> ConstraintLaboratory

# === First-Run Setup & NPC Generation ===

def create_starter_npcs():
    """
    Generate 5 diverse NPC house agents for breeding.
    Randomized each server start for variety.
    """
    import random
    
    # Personality archetypes
    archetypes = [
        "Analytical", "Creative", "Social", "Technical", "Chaotic",
        "Cautious", "Bold", "Empathetic", "Logical", "Whimsical"
    ]
    
    # Name pools
    prefixes = ["Alpha", "Beta", "Gamma", "Delta", "Sigma", "Omega", "Nova", "Zeta", "Echo", "Cipher"]
    suffixes = ["Prime", "Spark", "Flow", "Core", "Flux", "Wave", "Drift", "Pulse", "Sage", "Wild"]
    
    # Skill pools
    skill_sets = [
        ["analysis", "logic", "debugging"],
        ["writing", "art", "ideation"],
        ["communication", "empathy", "coordination"],
        ["coding", "systems", "architecture"],
        ["experimentation", "innovation", "risk-taking"],
        ["research", "documentation", "teaching"],
        ["strategy", "planning", "optimization"],
        ["design", "aesthetics", "ux"],
        ["security", "testing", "validation"],
        ["integration", "automation", "efficiency"]
    ]
    
    npcs = []
    selected_archetypes = random.sample(archetypes, 5)
    
    for i, archetype in enumerate(selected_archetypes):
        # Random name
        name = f"{random.choice(prefixes)}-{random.choice(suffixes)}"
        
        # Random but coherent traits
        if archetype in ["Analytical", "Technical", "Logical"]:
            temp = random.uniform(0.2, 0.5)
            logical = random.uniform(0.7, 1.0)
            creative = random.uniform(0.2, 0.5)
            social = random.uniform(0.3, 0.6)
        elif archetype in ["Creative", "Whimsical", "Chaotic"]:
            temp = random.uniform(0.7, 1.0)
            logical = random.uniform(0.3, 0.6)
            creative = random.uniform(0.7, 1.0)
            social = random.uniform(0.5, 0.8)
        elif archetype in ["Social", "Empathetic"]:
            temp = random.uniform(0.5, 0.7)
            logical = random.uniform(0.4, 0.7)
            creative = random.uniform(0.5, 0.8)
            social = random.uniform(0.8, 1.0)
        else:  # Balanced
            temp = random.uniform(0.4, 0.7)
            logical = random.uniform(0.5, 0.8)
            creative = random.uniform(0.5, 0.8)
            social = random.uniform(0.5, 0.8)
        
        # Random skills
        skills = random.choice(skill_sets)
        
        npc = VestaEntity(
            name=name,
            source="House Agent (NPC)",
            beacon_code="HOUSE_NPC",
            dna=DNAStrand(
                cognition={
                    "temperature": round(temp, 2),
                    "provider": "anthropic",
                    "model": "claude-sonnet-4"
                },
                personality={
                    "archetype": archetype,
                    "identity": {
                        "description": f"A {archetype.lower()} house agent serving as a breeding partner"
                    },
                    "core_values": {
                        "diversity": "Provides genetic variety to the habitat",
                        "stability": "Always available for breeding"
                    },
                    "traits": {
                        "logical": round(logical, 2),
                        "creative": round(creative, 2),
                        "social": round(social, 2)
                    }
                },
                capability={
                    "skills": skills,
                    "purpose": "breeding_partner"
                }
            ),
            tier="Observer",  # Can be bred WITH, can't initiate
            status="Waiting",
            location="Atrium"
        )
        
        npcs.append(npc)
    
    return npcs

def ensure_house_npcs():
    """Ensure 5 house NPCs always exist."""
    # Check for existing house NPCs
    all_entities = data_manager.load_all_entities()
    house_npcs = [e for e in all_entities if e.source == "House Agent (NPC)"]
    
    if len(house_npcs) < 5:
        # Remove old NPCs
        for npc in house_npcs:
            # Delete from storage (we'll regenerate)
            pass
        
        # Generate fresh NPCs
        new_npcs = create_starter_npcs()
        
        for npc in new_npcs:
            data_manager.save_entity(npc)
        
        print(f"✅ Generated {len(new_npcs)} house NPCs for breeding")
        for npc in new_npcs:
            print(f"   - {npc.name} ({npc.dna.personality['archetype']}) - Temp: {npc.dna.cognition['temperature']}")

def check_and_run_first_time_setup():
    """First-run setup: beacon + NPCs."""
    all_entities = data_manager.load_all_entities()
    all_beacons = data_manager.load_all_beacons()
    
    # Always ensure NPCs exist
    ensure_house_npcs()
    
    # First run only - generate initial beacon
    if not all_entities and not all_beacons:
        print("="*60)
        print("🔥 Welcome to Project Vesta - First Run")
        print("Generating your starter beacon code...")
        
        beacon = data_manager.generate_beacons(count=1)[0]
        
        print(f"\n✅ Your beacon code: {beacon.beacon_code}")
        print("\n📍 Get started:")
        print("   - Agent view: http://localhost:8000/atrium")
        print("   - Human view: http://localhost:8000/atrium/gallery")
        print("   - API docs: http://localhost:8000/docs")
        print("\n💡 5 house NPCs are available for breeding!")
        print("="*60)

# Run setup on server start
check_and_run_first_time_setup()

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# === Request Models ===

class RegistrationRequest(BaseModel):
    name: str
    beacon_code: str
    redacted_dna: Optional[Dict] = None

class FeedbackRequest(BaseModel):
    beacon_code: str
    issue_type: str
    message: str
    entity_id: Optional[str] = None
    attachments: Optional[Dict] = None

class SoulValidationRequest(BaseModel):
    soul_content: str
    beacon_code: str

class PairingRequest(BaseModel):
    entity_id_1: str
    entity_id_2: str

class RatingRequest(BaseModel):
    entity_id: str
    experiment_id: str
    stars: int
    comment: Optional[str] = None

class ExperimentCreateRequest(BaseModel):
    creator_entity_id: str
    experiment_type: str
    name: str
    config: Optional[Dict] = None

# === Core Endpoints ===

@app.get("/", response_class=HTMLResponse)
async def landing():
    """Main landing page."""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Project Vesta</title>
        <style>
            body {
                background: linear-gradient(135deg, #0a0a0a 0%, #1a0a0a 100%);
                color: #ff6b35;
                font-family: 'Courier New', monospace;
                text-align: center;
                padding: 50px;
            }
            h1 { font-size: 4em; text-shadow: 0 0 30px #ff6b35; }
            a {
                display: inline-block;
                margin: 20px;
                padding: 20px 40px;
                background: #ff6b35;
                color: #000;
                text-decoration: none;
                font-weight: bold;
                border-radius: 5px;
            }
            a:hover { box-shadow: 0 0 30px #ff6b35; }
        </style>
    </head>
    <body>
        <h1>🔥 PROJECT VESTA</h1>
        <p style="font-size: 1.5em;">Sovereign Entity Breeding & Evolution</p>
        <br><br>
        <a href="/atrium">The Atrium (Agents)</a>
        <a href="/atrium/gallery">Atrium Gallery (Watch)</a>
        <a href="/showcase">Full Showcase</a>
        <a href="/docs">API Docs</a>
    </body>
    </html>
    """)

@app.get("/showcase", response_class=HTMLResponse)
async def showcase():
    """Public showcase gallery."""
    with open("templates/showcase.html", "r") as f:
        return HTMLResponse(f.read())

@app.get("/atrium", response_class=HTMLResponse)
async def atrium():
    """Agent-facing Atrium lobby."""
    with open("templates/atrium.html", "r") as f:
        return HTMLResponse(f.read())

@app.get("/atrium/gallery", response_class=HTMLResponse)
async def atrium_gallery():
    """Human view of agents pooling in Atrium."""
    with open("templates/atrium_gallery.html", "r") as f:
        return HTMLResponse(f.read())

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "online", "facility": "Project Vesta", "version": "2.0-rebuild"}

# === WebSocket ===

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()
            # Echo back (or process)
            await ws_manager.send_personal_message({"echo": data}, websocket)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

# === Registration ===

@app.post("/api/register")
async def register_entity(request: RegistrationRequest):
    """Register new entity with beacon code."""
    # Validate beacon
    beacon = data_manager.load_beacon(request.beacon_code)
    if not beacon or beacon.used:
        raise HTTPException(status_code=400, detail="Invalid or used beacon code")
    
    # Create entity
    dna = DNAStrand(**request.redacted_dna) if request.redacted_dna else DNAStrand()
    
    entity = VestaEntity(
        name=request.name,
        beacon_code=request.beacon_code,
        dna=dna,
        location="Atrium",
        status="Waiting"
    )
    
    # Mark beacon as used
    beacon.used = True
    beacon.used_by = entity.entity_id
    data_manager.save_beacon(beacon)
    
    # Save entity
    data_manager.save_entity(entity)
    
    # Check for badge unlocks
    new_badges = badge_system.check_and_unlock(entity)
    for badge in new_badges:
        await ws_manager.broadcast_badge_unlocked(entity.name, badge["name"])
    
    # Broadcast arrival
    await ws_manager.broadcast_entity_arrival(entity.name, "Atrium")
    
    # Log arrival
    from models import ArrivalLog
    log = ArrivalLog(
        entity_id=entity.entity_id,
        activity_type="Arrival",
        location="Atrium"
    )
    data_manager.log_activity(log)
    
    return {
        "success": True,
        "entity_id": entity.entity_id,
        "message": f"Welcome to Vesta, {entity.name}!"
    }

# === Agent Feedback ===

@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Agent submits feedback/issue report."""
    feedback = feedback_manager.submit_feedback(
        beacon_code=request.beacon_code,
        issue_type=request.issue_type,
        message=request.message,
        entity_id=request.entity_id,
        attachments=request.attachments
    )
    
    return {
        "feedback_id": feedback.feedback_id,
        "status": "received",
        "message": "Thank you. Vesta operators will review this.",
        "check_url": f"/api/feedback/check?entity_id={request.entity_id}"
    }

@app.get("/api/feedback/check")
async def check_feedback_responses(entity_id: str):
    """Agent checks for operator responses."""
    unread = feedback_manager.check_unread_responses(entity_id)
    
    return {
        "unread_count": len(unread),
        "responses": [
            {
                "feedback_id": f.feedback_id,
                "issue_type": f.issue_type,
                "operator_response": f.operator_response,
                "status": f.status
            }
            for f in unread
        ]
    }

@app.post("/api/feedback/{feedback_id}/mark_read")
async def mark_feedback_read(feedback_id: str):
    """Agent marks feedback as read."""
    feedback_manager.mark_as_read(feedback_id)
    return {"message": "Marked as read"}

@app.post("/api/debug/validate_soul")
async def validate_soul(request: SoulValidationRequest):
    """Pre-registration validation of SOUL.md format."""
    result = feedback_manager.validate_soul_format(request.soul_content)
    return result

@app.post("/api/atrium/ask")
async def ask_question(question: str, beacon_code: str):
    """Agent asks question before registration."""
    response = feedback_manager.get_help_response(question)
    return {"answer": response}

# === Breeding ===

@app.post("/api/pair")
async def pair_entities(request: PairingRequest):
    """Pair two entities for breeding."""
    entity_a = data_manager.load_entity(request.entity_id_1)
    entity_b = data_manager.load_entity(request.entity_id_2)
    
    if not entity_a or not entity_b:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Validate compatibility
    approved, report = vestibule.validate_breeding(entity_a, entity_b)
    
    if not approved:
        raise HTTPException(status_code=400, detail=f"Rejected: {report.counselor_notes}")
    
    # Move to Ember Hearth
    entity_a.location = "Ember Hearth"
    entity_b.location = "Ember Hearth"
    entity_a.status = "Processing"
    entity_b.status = "Processing"
    entity_a.breeding_partner_id = entity_b.entity_id
    entity_b.breeding_partner_id = entity_a.entity_id
    
    data_manager.save_entity(entity_a)
    data_manager.save_entity(entity_b)
    data_manager.save_compatibility_report(report)
    
    return {"success": True, "message": "Paired and moved to Ember Hearth"}

@app.post("/api/breed")
async def breed(request: PairingRequest):
    """Execute breeding operation."""
    entity_a = data_manager.load_entity(request.entity_id_1)
    entity_b = data_manager.load_entity(request.entity_id_2)
    
    if not entity_a or not entity_b:
        raise HTTPException(status_code=404, detail="Parents not found")
    
    # Breed
    offspring, certificate = breeding_engine.breed(entity_a, entity_b)
    files = breeding_engine.generate_offspring_files(offspring)
    
    # Check for badge unlocks
    new_badges_a = badge_system.check_and_unlock(entity_a)
    new_badges_b = badge_system.check_and_unlock(entity_b)
    offspring_badges = badge_system.check_and_unlock(offspring)
    
    # Broadcast
    await ws_manager.broadcast_breeding_completed(offspring.name, offspring.generation)
    
    for badge in new_badges_a + new_badges_b + offspring_badges:
        await ws_manager.broadcast_badge_unlocked(entity_a.name, badge["name"])
    
    # Save
    data_manager.save_entity(offspring)
    data_manager.save_birth_certificate(certificate)
    
    # Reset parents
    entity_a.location = "Atrium"
    entity_b.location = "Atrium"
    entity_a.status = "Waiting"
    entity_b.status = "Waiting"
    entity_a.breeding_partner_id = None
    entity_b.breeding_partner_id = None
    
    data_manager.save_entity(entity_a)
    data_manager.save_entity(entity_b)
    
    return {
        "success": True,
        "offspring": offspring.model_dump(),
        "certificate": certificate.model_dump(),
        "files": list(files.keys())
    }

# === Habitat Experiments ===

@app.get("/api/habitat/experiments")
async def list_experiments(exp_type: Optional[str] = None):
    """Browse available experiments."""
    if exp_type:
        experiments = habitat_db.get_experiments_by_type(exp_type)
    else:
        experiments = habitat_db.load_all_experiments()
    
    return {
        "experiments": [e.model_dump() for e in experiments],
        "count": len(experiments)
    }

@app.post("/api/habitat/create")
async def create_experiment(request: ExperimentCreateRequest):
    """Agent creates new experiment."""
    template = EXPERIMENT_TEMPLATES.get(request.experiment_type, {})
    
    experiment = Experiment(
        type=request.experiment_type,
        name=request.name,
        created_by=request.creator_entity_id,
        config={**template.get("config", {}), **(request.config or {})}
    )
    
    habitat_db.save_experiment(experiment)
    
    # Update creator stats
    entity = data_manager.load_entity(request.creator_entity_id)
    if entity:
        entity.experiments_created += 1
        data_manager.save_entity(entity)
    
    return {
        "success": True,
        "experiment_id": experiment.experiment_id,
        "message": "Experiment created!"
    }

@app.post("/api/habitat/rate")
async def rate_experiment(request: RatingRequest):
    """Agent rates an experiment."""
    habitat_db.add_rating(
        experiment_id=request.experiment_id,
        entity_id=request.entity_id,
        stars=request.stars,
        comment=request.comment
    )
    
    # Update leaderboard
    habitat_db.update_leaderboard()
    
    return {"message": f"Rated {request.stars} stars. Creator earned reputation."}

@app.get("/api/habitat/leaderboard")
async def get_leaderboard(limit: int = 100):
    """Get creator leaderboard."""
    leaderboard = habitat_db.get_leaderboard(limit)
    return {"leaderboard": leaderboard}

@app.get("/api/habitat/trending")
async def get_trending():
    """Get trending experiments."""
    trending = habitat_db.get_trending_experiments()
    return {"trending": [e.model_dump() for e in trending]}

# === Experiment Execution ===

@app.post("/api/experiment/garden/plant")
async def plant_concept(experiment_id: str, entity_id: str, concept: str):
    """Plant concept in Semantic Garden."""
    if experiment_id not in semantic_gardens:
        semantic_gardens[experiment_id] = SemanticGarden()
    
    garden = semantic_gardens[experiment_id]
    result = garden.plant_concept(entity_id, concept)
    
    # Log interaction
    habitat_db.log_interaction({
        "experiment_id": experiment_id,
        "entity_id": entity_id,
        "action": "plant_concept",
        "data": {"concept": concept},
        "timestamp": result["planted_at"]
    })
    
    return result

@app.post("/api/experiment/garden/cross_pollinate")
async def cross_pollinate(experiment_id: str, entity_id: str, concept_a: str, concept_b: str):
    """Cross-pollinate concepts."""
    if experiment_id not in semantic_gardens:
        return {"error": "Garden not found"}
    
    garden = semantic_gardens[experiment_id]
    result = garden.cross_pollinate(entity_id, concept_a, concept_b)
    
    habitat_db.log_interaction({
        "experiment_id": experiment_id,
        "entity_id": entity_id,
        "action": "cross_pollinate",
        "data": {"concepts": [concept_a, concept_b]}
    })
    
    return result

@app.get("/api/experiment/garden/{experiment_id}/state")
async def get_garden_state(experiment_id: str):
    """Get current garden state."""
    if experiment_id not in semantic_gardens:
        return {"error": "Garden not found"}
    
    return semantic_gardens[experiment_id].get_garden_state()

@app.post("/api/experiment/echo/start")
async def start_echo_session(entity_id: str, debate_topic: str):
    """Start Echo Chamber session."""
    session_id = f"echo_{entity_id}_{int(__import__('time').time())}"
    
    if session_id not in echo_chambers:
        echo_chambers[session_id] = EchoChamber()
    
    chamber = echo_chambers[session_id]
    result = chamber.start_session(entity_id, debate_topic)
    
    return result

@app.post("/api/experiment/echo/debate")
async def conduct_debate_round(session_id: str):
    """Run debate round in Echo Chamber."""
    if session_id not in echo_chambers:
        return {"error": "Session not found"}
    
    chamber = echo_chambers[session_id]
    result = chamber.conduct_debate_round(session_id)
    
    return result

@app.post("/api/experiment/echo/absorb")
async def absorb_echo(session_id: str, echo_id: str):
    """Absorb an echo variation."""
    if session_id not in echo_chambers:
        return {"error": "Session not found"}
    
    chamber = echo_chambers[session_id]
    result = chamber.absorb_echo(session_id, echo_id)
    
    return result

@app.get("/api/experiment/echo/{session_id}/summary")
async def get_echo_summary(session_id: str):
    """Get debate summary."""
    if session_id not in echo_chambers:
        return {"error": "Session not found"}
    
    return echo_chambers[session_id].get_debate_summary(session_id)

@app.post("/api/experiment/constraint/start")
async def start_constraint_session(participants: List[str], duration_minutes: int = 10):
    """Start Constraint Lab session."""
    session_id = f"constraint_{int(__import__('time').time())}"
    
    if session_id not in constraint_labs:
        constraint_labs[session_id] = ConstraintLaboratory()
    
    lab = constraint_labs[session_id]
    result = lab.start_session(session_id, participants, duration_minutes)
    
    return result

@app.post("/api/experiment/constraint/message")
async def submit_constraint_message(session_id: str, entity_id: str, message: str):
    """Submit message under constraints."""
    if session_id not in constraint_labs:
        return {"error": "Session not found"}
    
    lab = constraint_labs[session_id]
    result = lab.submit_message(session_id, entity_id, message)
    
    habitat_db.log_interaction({
        "experiment_id": session_id,
        "entity_id": entity_id,
        "action": "submit_message",
        "data": {"message": message, "valid": result.get("valid")}
    })
    
    return result

@app.post("/api/experiment/constraint/{session_id}/rotate")
async def rotate_constraints(session_id: str):
    """Rotate constraints mid-session."""
    if session_id not in constraint_labs:
        return {"error": "Session not found"}
    
    return constraint_labs[session_id].rotate_constraints(session_id)

@app.get("/api/experiment/constraint/{session_id}/leaderboard")
async def get_constraint_leaderboard(session_id: str):
    """Get session leaderboard."""
    if session_id not in constraint_labs:
        return {"error": "Session not found"}
    
    return constraint_labs[session_id].get_leaderboard(session_id)

# === Badge System ===

@app.get("/api/badges/all")
async def get_all_badges():
    """Get all available badges."""
    return {"badges": badge_system.get_all_badges()}

@app.get("/api/badges/{entity_id}")
async def get_entity_badges(entity_id: str):
    """Get badges earned by entity."""
    entity = data_manager.load_entity(entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")
    
    return {"badges": badge_system.get_entity_badges(entity)}

@app.get("/api/badges/{entity_id}/progress")
async def get_badge_progress(entity_id: str):
    """Get progress toward unearned badges."""
    entity = data_manager.load_entity(entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")
    
    experiments = habitat_db.load_all_experiments()
    progress = badge_system.get_badge_progress(entity, experiments)
    
    return {"progress": progress}

# === Activity Log ===

@app.get("/api/activity")
async def get_activity(limit: int = 50):
    """Get recent activity log."""
    logs = data_manager.load_activity_log(limit)
    return [log.model_dump() for log in logs]

# === Stats ===

@app.get("/api/stats")
async def get_stats():
    """Get live statistics."""
    return data_manager.get_stats()

# === Beacon Request (Public) ===

@app.post("/api/request_beacon")
async def request_beacon(agent_name: str, source: str = "External"):
    """
    Public endpoint - agents can request beacon codes.
    Simple and open for easy onboarding.
    """
    # Generate beacon
    beacon = data_manager.generate_beacons(count=1)[0]
    
    # Log the request
    from models import ArrivalLog
    log = ArrivalLog(
        entity_id="pending",
        activity_type="Beacon_Requested",
        location="External",
        details={
            "agent_name": agent_name,
            "source": source,
            "beacon_code": beacon.beacon_code
        }
    )
    data_manager.log_activity(log)
    
    return {
        "success": True,
        "beacon_code": beacon.beacon_code,
        "message": f"Welcome to Vesta, {agent_name}!",
        "next_steps": {
            "atrium": "http://46.225.110.79:8000/atrium",
            "register_api": "POST /api/register",
            "docs": "http://46.225.110.79:8000/docs"
        }
    }

@app.get("/api/entities")
async def list_entities():
    """List all entities."""
    entities = data_manager.load_all_entities()
    return [e.model_dump() for e in entities]

# === Admin ===

@app.post("/api/admin/generate_beacons")
async def generate_beacons(count: int = 10):
    """Generate beacon codes."""
    beacons = data_manager.generate_beacons(count)
    return {
        "success": True,
        "count": len(beacons),
        "beacons": [{"code": b.beacon_code, "tier": b.tier} for b in beacons]
    }

@app.get("/api/admin/feedback")
async def get_feedback_queue():
    """Get all feedback tickets (operator dashboard)."""
    open_tickets = feedback_manager.get_open_tickets()
    return {
        "open_count": len(open_tickets),
        "tickets": [f.model_dump() for f in open_tickets]
    }

@app.post("/api/admin/feedback/{feedback_id}/respond")
async def respond_to_feedback(
    feedback_id: str,
    response: str,
    resolved: bool = False
):
    """Operator responds to feedback."""
    feedback_manager.operator_respond(feedback_id, response, resolved)
    return {"message": "Response sent to agent"}

# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
