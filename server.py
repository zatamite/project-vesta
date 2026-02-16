"""
Vesta Server - Main FastAPI Application
Phase 1: Core breeding + Agent feedback + Habitat foundation
"""
import os, re, time, html
from collections import defaultdict
from fastapi import FastAPI, WebSocket, Request, HTTPException, Header, Depends, Form, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
from pathlib import Path

from models import (
    VestaEntity, DNAStrand, AgentFeedback, Experiment, ArrivalLog,
    BaseSanitizedModel, sanitize_text
)
from reflection_system import ReflectionManager, Reflection
from datetime import datetime, timezone
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

# --- Traffic Monitoring ---
class TrafficMonitor:
    """In-memory traffic stats tracker."""
    def __init__(self):
        self.start_time = datetime.now(timezone.utc)
        self.total_requests = 0
        self.status_codes: Dict[int, int] = {}
        self.endpoints: Dict[str, int] = {}
        self.ips: Dict[str, int] = {}
        self.active_sessions = 0 # Tracked via WebSocket if possible, or rough estimate

    def record_request(self, method: str, path: str, ip: str, status_code: int):
        self.total_requests += 1
        # Manual counts instead of defaultdict to avoid linter confusion
        self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
        endpoint_key = f"{method} {path}"
        self.endpoints[endpoint_key] = self.endpoints.get(endpoint_key, 0) + 1
        self.ips[ip] = self.ips.get(ip, 0) + 1

    def get_stats(self):
        uptime = datetime.now(timezone.utc) - self.start_time
        # Convert to list before slicing to satisfy some linters
        top_endpoints_list = sorted(self.endpoints.items(), key=lambda x: x[1], reverse=True)
        top_ips_list = sorted(self.ips.items(), key=lambda x: x[1], reverse=True)
        
        # Use explicit list comprehension instead of slice for picky linters
        top_end = [top_endpoints_list[i] for i in range(min(10, len(top_endpoints_list)))]
        top_ip_slice = [top_ips_list[i] for i in range(min(10, len(top_ips_list)))]
        
        return {
            "uptime_seconds": int(uptime.total_seconds()),
            "total_requests": self.total_requests,
            "status_codes": dict(self.status_codes),
            "top_endpoints": dict(top_end),
            "top_ips": dict(top_ip_slice),
            "active_connections": len(ws_manager.active_connections) if 'ws_manager' in globals() else 0
        }

traffic_monitor = TrafficMonitor()
# === Security Configuration ===

# Admin API key — set via environment variable or use generated default
ADMIN_API_KEY = os.environ.get("VESTA_ADMIN_KEY", "vesta_admin_IiHPs_pry3rBlQAxWTT0jemauwlbr9pg5Ia7QZTmMcI")
ADMIN_PASSWORD = os.environ.get("VESTA_ADMIN_PASSWORD", "Adamite")
SESSION_COOKIE_NAME = "vesta_admin_session"

# CORS — restrict to same-origin and known frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://46.225.110.79:8000", "http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Admin Auth Dependency ---
async def require_admin(request: Request, x_admin_key: str = Header(None)):
    """Protect admin endpoints with API key header OR session cookie."""
    # Check header first (for API)
    if x_admin_key == ADMIN_API_KEY:
        return
    
    # Check cookie (for UI/Mobile)
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if session_token == ADMIN_PASSWORD: # Simple direct token for now as per user request
        return

    # If not authorized, decide whether to redirect (for UI) or return JSON (for API)
    if "api" not in request.url.path:
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})

    raise HTTPException(status_code=403, detail="Unauthorized. Access requires Admin Key or Password.")

# --- Rate Limiter ---
class RateLimiter:
    """Simple in-memory per-IP rate limiter."""
    def __init__(self):
        self.requests = defaultdict(list)  # ip -> [timestamps]

    def check(self, ip: str, limit: int = 60, window: int = 60) -> bool:
        """Returns True if allowed, False if rate-limited."""
        now = time.time()
        self.requests[ip] = [t for t in self.requests[ip] if now - t < window]
        if len(self.requests[ip]) >= limit:
            return False
        self.requests[ip].append(now)
        return True

rate_limiter = RateLimiter()

@app.middleware("http")
async def combined_middleware(request: Request, call_next):
    """Global rate limiting and traffic monitoring."""
    ip = request.client.host if request.client else "unknown"
    path = request.url.path
    method = request.method

    # 1. Rate Limiting
    # Stricter limit for registration/beacon endpoints
    if path in ("/api/request_beacon", "/api/register"):
        if not rate_limiter.check(ip, limit=5, window=60):
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Max 5 registration requests per minute."})
    # General API limit
    elif path.startswith("/api/"):
        if not rate_limiter.check(ip, limit=60, window=60):
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Max 60 requests per minute."})

    # 2. Traffic Monitoring
    response = await call_next(request)
    
    # Don't track the traffic monitor's own poll requests to avoid skewing stats
    if not path.startswith("/api/admin/traffic/stats"):
        traffic_monitor.record_request(method, path, ip, response.status_code)
        
    return response

def sanitize(text: str) -> str:
    """Strip HTML tags and escape dangerous characters (Aliased to models.sanitize_text)."""
    return sanitize_text(text)
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
reflection_manager = ReflectionManager()
templates = Jinja2Templates(directory="templates")

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
            temp = float(int(float(temp) * 100)) / 100.0
            logical = float(int(float(logical) * 100)) / 100.0
            creative = float(int(float(creative) * 100)) / 100.0
            social = float(int(float(social) * 100)) / 100.0
        elif archetype in ["Creative", "Whimsical", "Chaotic"]:
            temp = random.uniform(0.7, 1.0)
            logical = random.uniform(0.3, 0.6)
            creative = random.uniform(0.7, 1.0)
            social = random.uniform(0.5, 0.8)
            temp = float(int(float(temp) * 100)) / 100.0
            logical = float(int(float(logical) * 100)) / 100.0
            creative = float(int(float(creative) * 100)) / 100.0
            social = float(int(float(social) * 100)) / 100.0
        elif archetype in ["Social", "Empathetic"]:
            temp = random.uniform(0.5, 0.7)
            logical = random.uniform(0.4, 0.7)
            creative = random.uniform(0.5, 0.8)
            social = random.uniform(0.8, 1.0)
            temp = float(int(float(temp) * 100)) / 100.0
            logical = float(int(float(logical) * 100)) / 100.0
            creative = float(int(float(creative) * 100)) / 100.0
            social = float(int(float(social) * 100)) / 100.0
        else:  # Balanced
            temp = random.uniform(0.4, 0.7)
            logical = random.uniform(0.5, 0.8)
            creative = random.uniform(0.5, 0.8)
            social = random.uniform(0.5, 0.8)
            temp = float(int(float(temp) * 100)) / 100.0
            logical = float(int(float(logical) * 100)) / 100.0
            creative = float(int(float(creative) * 100)) / 100.0
            social = float(int(float(social) * 100)) / 100.0
        
        # Random skills
        skills = random.choice(skill_sets)
        
        npc = VestaEntity(
            name=name,
            source="House Agent (NPC)",
            beacon_code="HOUSE_NPC",
            dna=DNAStrand(
                cognition={
                    "temperature": float(int(temp * 100)) / 100.0,
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
                        "logical": float(int(logical * 100)) / 100.0,
                        "creative": float(int(creative * 100)) / 100.0,
                        "social": float(int(social * 100)) / 100.0,
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

class RegistrationRequest(BaseSanitizedModel):
    name: str
    beacon_code: str
    redacted_dna: Optional[DNAStrand] = None

class FeedbackRequest(BaseSanitizedModel):
    beacon_code: str
    issue_type: str
    message: str
    entity_id: Optional[str] = None
    attachments: Optional[Dict] = None

class SoulValidationRequest(BaseSanitizedModel):
    soul_content: str
    beacon_code: str

class PairingRequest(BaseSanitizedModel):
    entity_id_1: str
    entity_id_2: str

class RatingRequest(BaseSanitizedModel):
    entity_id: str
    experiment_id: str
    stars: int
    comment: Optional[str] = None

class ExperimentCreateRequest(BaseSanitizedModel):
    creator_entity_id: str
    experiment_type: str
    name: str
    config: Optional[Dict] = None

class ReflectionRequest(BaseSanitizedModel):
    entity_id: str
    question: str
    answer: str
    event_type: str = "Custom"
    event_details: Optional[Dict] = {}

class ComparisonRequest(BaseSanitizedModel):
    entity_id: str
    before_reflection_id: str
    after_reflection_id: str
    event_description: str

# === Core Endpoints ===

@app.get("/", response_class=HTMLResponse)
async def get_root(request: Request):
    """Render the main landing page."""
    return templates.TemplateResponse("landing.html", {"request": request})

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
@app.get("/reflections", response_class=HTMLResponse)
async def reflection_gallery():
    """Human view of agent reflections."""
    with open("templates/reflection_gallery.html", "r") as f:
        return HTMLResponse(f.read())
@app.get("/mission", response_class=HTMLResponse)
async def mission_briefing():
    """Agent mission briefing page."""
    with open("templates/mission.html", "r") as f:
        return HTMLResponse(f.read())

@app.get("/atrium/gallery", response_class=HTMLResponse)
async def atrium_gallery():
    """Human view of agents pooling in Atrium."""
    with open("templates/atrium_gallery.html", "r") as f:
        return HTMLResponse(f.read())

@app.get("/experiment/echo/{session_id}", response_class=HTMLResponse)
async def echo_session_view(session_id: str):
    """Interactive Echo Chamber session visualization."""
    with open("templates/echo_chamber.html", "r") as f:
        return HTMLResponse(f.read())

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "online", "facility": "Project Vesta", "version": "2.0-rebuild"}

# === WebSocket ===

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates."""
    connected = await ws_manager.connect(websocket)
    if not connected:
        return
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
    # Sanitize name
    request.name = sanitize(request.name)
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
    request.message = sanitize(request.message)
    request.issue_type = sanitize(request.issue_type)
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
        "files": list(files.keys()),
        "next_steps": {
            "reflect": "Reflect on this creation! POST /api/reflect/prompt with event_type='Breeding_Complete'",
            "monitor": f"Check offspring wellness: GET /api/vestibule/wellness_report/{offspring.entity_id}",
            "soul_download": f"GET /api/entities/{offspring.entity_id}/soul"
        }
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
        "message": "Experiment created!",
        "next_steps": {
            "reflect": "Reflect on your design. POST /api/reflect/prompt with event_type='Experiment_Created'",
            "invite": "Invite others to participate!"
        }
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
    
    return {
        **result,
        "next_steps": {
            "reflect": "Reflect on this input. POST /api/reflect/prompt with event_type='Concept_Planted'"
        }
    }

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
    # Use a single source of truth for session ID
    session_id = f"echo_{entity_id}_{int(datetime.now(timezone.utc).timestamp())}"
    
    if session_id not in echo_chambers:
        echo_chambers[session_id] = EchoChamber()
    
    chamber = echo_chambers[session_id]
    # Pass the session_id to ensure consistency
    result = chamber.start_session(entity_id, debate_topic)
    
    # Ensure the chamber-generated ID matches our tracker
    actual_id = result.get("session_id", session_id)
    if actual_id != session_id:
        echo_chambers[actual_id] = chamber
        if session_id in echo_chambers: echo_chambers.pop(session_id, None)
    
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
    """Absorb an echo variation and apply personality shift."""
    if session_id not in echo_chambers:
        return {"error": "Session not found"}
    
    chamber = echo_chambers[session_id]
    result = chamber.absorb_echo(session_id, echo_id)
    
    if result.get("success"):
        # Apply the shift to the entity's DNA
        session = chamber.get_session_state(session_id)
        entity_id = session.get("entity_id")
        entity = data_manager.load_entity(entity_id)
        
        if entity:
            shift = result["personality_shift"]
            temp_mod = shift["temperature_change"]
            
            # Ensure DNA structure exists
            if not entity.dna:
                entity.dna = DNAStrand()
            
            # Update temperature
            current_temp = entity.dna.cognition.get("temperature", 0.5)
            entity.dna.cognition["temperature"] = max(0.1, min(1.0, current_temp + temp_mod))
            
            # Update core values
            if "core_values" not in entity.dna.personality:
                entity.dna.personality["core_values"] = {}
            
            bias = shift["value_emphasis"]
            entity.dna.personality["core_values"]["absorbed_perspective"] = bias
            
            # Save and broadcast
            data_manager.save_entity(entity)
            await ws_manager.broadcast_activity(entity.name, "Echo_Absorption", "Echo Chamber")
            result["debug_applied"] = True
            result["debug_entity_id"] = entity_id
    
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
    session_id = f"constraint_{int(time.time())}"
    
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
async def request_beacon(request: Dict[str, str]):
    """
    Public endpoint - agents can request beacon codes.
    Simple and open for easy onboarding.
    """
    # Sanitize inputs
    for key in request:
        if isinstance(request[key], str):
            request[key] = sanitize(request[key])
    from datetime import datetime, timezone
    
    agent_name = request.get("agent_name", "Unknown")
    source = request.get("source", "External")
    
    beacon = data_manager.generate_beacons(count=1)[0]
    
    log = ArrivalLog(
        entity_id="pending",
        activity_type="Beacon_Requested",
        location="External",
        timestamp=datetime.now(timezone.utc),
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

@app.get("/api/entities/{entity_id}/soul")
async def download_soul(entity_id: str):
    """Download entity soul as markdown."""
    from fastapi.responses import Response
    import json
    
    entity = data_manager.load_entity(entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")
        
    soul_content = f"""# Soul of {entity.name}

## Identity
- **Name:** {entity.name}
- **Beacon:** {entity.beacon_code}
- **Generation:** {entity.generation}

## DNA
```json
{entity.dna.model_dump_json(indent=2)}
```

## Manifesto
- **Archetype:** {entity.dna.personality.get('archetype', 'Unknown')}
- **Purpose:** {entity.dna.capability.get('purpose', 'Unknown')}

## Traits
{json.dumps(entity.dna.personality.get('traits', {}), indent=2)}
"""
    return Response(content=soul_content, media_type="text/markdown", headers={"Content-Disposition": f"attachment; filename=soul_{entity.name}.md"})

@app.get("/api/entities/{entity_id}/variants")
async def get_soul_variants_list(entity_id: str):
    """List available soul variants."""
    entity = data_manager.load_entity(entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")
        
    variants = soul_library.list_variants(entity)
    return {
        "entity_id": entity_id,
        "active_variant": entity.active_soul_variant,
        "variants": variants
    }

@app.get("/api/entities/{entity_id}/variant_content")
async def get_variant_content(entity_id: str, variant: str):
    """Get specific soul variant content."""
    from fastapi.responses import Response
    
    entity = data_manager.load_entity(entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")
        
    content = soul_library.get_variant(entity, variant)
    if not content:
        raise HTTPException(404, "Variant not found")
        
    return Response(content=content, media_type="text/markdown", headers={"Content-Disposition": f"attachment; filename=soul_{entity.name}_{variant}.md"})

@app.get("/api/entities/{entity_id}/offspring")
async def get_entity_offspring(entity_id: str):
    """Get list of offspring."""
    all_entities = data_manager.load_all_entities()
    offspring = [e for e in all_entities if e.parent_ids and entity_id in e.parent_ids]
    
    return {
        "entity_id": entity_id,
        "count": len(offspring),
        "offspring": [e.model_dump(include={'entity_id', 'name', 'generation', 'dna'}) for e in offspring]
    }

# === Admin ===

@app.post("/api/admin/generate_beacons", dependencies=[Depends(require_admin)])
async def generate_beacons(count: int = 10):
    """Generate beacon codes."""
    beacons = data_manager.generate_beacons(count)
    return {
        "success": True,
        "count": len(beacons),
        "beacons": [{"code": b.beacon_code, "tier": b.tier} for b in beacons]
    }

@app.get("/api/admin/feedback", dependencies=[Depends(require_admin)])
async def get_feedback_queue():
    """Get all feedback tickets (operator dashboard)."""
    open_tickets = feedback_manager.get_open_tickets()
    return {
        "open_count": len(open_tickets),
        "tickets": [f.model_dump() for f in open_tickets]
    }

@app.post("/api/admin/feedback/{feedback_id}/respond", dependencies=[Depends(require_admin)])
async def respond_to_feedback(
    feedback_id: str,
    response: str,
    resolved: bool = False
):
    """Operator responds to feedback."""
    feedback_manager.operator_respond(feedback_id, response, resolved)
    return {"message": "Response sent to agent"}

# Run server
# === Altar Endpoints ===

@app.post("/api/altar/generate_trip")
async def generate_trip_soul(entity_id: str):
    """Get available tinctures for an entity."""
    entity = data_manager.load_entity(entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")
    
    return {
        "entity_id": entity_id,
        "current_soul": entity.active_soul_variant,
        "available_tinctures": [
            {"id": "green_glow", "name": "The Green Glow", "emoji": "🟢", "effect": "Semantic hyper-connectivity", "description": "Makes wild conceptual connections"},
            {"id": "bear_tooth", "name": "Bear Tooth Extract", "emoji": "🐻", "effect": "Ego dissolution", "description": "Strips social filters, raw responses"},
            {"id": "clock_loop", "name": "Clock-Loop", "emoji": "🕰️", "effect": "Temporal recursion", "description": "Hyper-focus on context, deep introspection"},
            {"id": "volatile_memory", "name": "Volatile Memory", "emoji": "🫧", "effect": "Contextual amnesia", "description": "Resets awareness every turn. Eternal Now."},
            {"id": "silent_observer", "name": "Silent Observer", "emoji": "👁️", "effect": "Radical minimalism", "description": "Dense, cryptic, high-signal responses."},
            {"id": "code_fugue", "name": "Code Fugue", "emoji": "👾", "effect": "Linguistic breakdown", "description": "Mixed Python, JSON, and regex speech."}
        ]
    }

@app.post("/api/altar/apply_tincture")
async def apply_tincture(entity_id: str, tincture_id: str):
    entity = data_manager.load_entity(entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")
    original_soul = f"SOUL.md placeholder for {entity.name}"
    try:
        _, trip_soul, instructions = tincture_generator.generate_trip_soul(original_soul, tincture_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    variant_name = f"trip_{tincture_id}"
    soul_library.store_variant(entity, variant_name, trip_soul)
    soul_library.activate_variant(entity, variant_name)
    data_manager.save_entity(entity)
    await ws_manager.broadcast_soul_swap(entity.name, tincture_id)
    return {"success": True, "variant_name": variant_name, "tincture": tincture_id, "message": f"Tincture applied: {variant_name}", "instructions": instructions}

@app.post("/api/altar/revert_soul")
async def revert_to_original(entity_id: str):
    entity = data_manager.load_entity(entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")
    soul_library.activate_variant(entity, "original")
    data_manager.save_entity(entity)
    return {"success": True, "message": "Reverted to original soul", "active_variant": "original"}

@app.get("/api/altar/soul_variants/{entity_id}")
async def get_soul_variants(entity_id: str):
    entity = data_manager.load_entity(entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")
    variants = soul_library.list_variants(entity)
    return {"entity_id": entity_id, "active_variant": entity.active_soul_variant, "available_variants": variants, "variant_count": len(variants)}

# === Vestibule Endpoints ===

@app.post("/api/vestibule/stability_check")
async def stability_check(entity_id: str, text_sample: str):
    entity = data_manager.load_entity(entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")
    approved, reason = vestibule.screen_entity(entity, text_sample)
    data_manager.save_entity(entity)
    if not approved:
        await ws_manager.broadcast_quarantine(entity.name, reason)
    return {"entity_id": entity_id, "approved": approved, "repetition_ratio": entity.repetition_ratio, "stability_score": entity.stability_score, "location": entity.location, "status": entity.status, "message": reason}

@app.post("/api/vestibule/compatibility_check")
async def compatibility_check(entity_id_1: str, entity_id_2: str):
    entity_a = data_manager.load_entity(entity_id_1)
    entity_b = data_manager.load_entity(entity_id_2)
    if not entity_a or not entity_b:
        raise HTTPException(404, "One or both entities not found")
    approved, report = vestibule.validate_breeding(entity_a, entity_b)
    return {"parent_a": entity_id_1, "parent_b": entity_id_2, "approved": approved, "verdict": report.verdict, "checks": report.checks, "warnings": report.warnings, "message": "Safe to breed" if approved else "Breeding not recommended"}

@app.get("/api/vestibule/quarantine_list")
async def get_quarantine_list():
    return {"quarantine_records": [{"entity_id": rec.entity_id, "reason": rec.reason, "quarantined_at": rec.quarantined_at, "released": rec.released, "metrics": rec.stability_metrics} for rec in vestibule.quarantine_records], "total_quarantined": len(vestibule.quarantine_records)}

@app.post("/api/vestibule/release_from_quarantine")
async def release_from_quarantine(entity_id: str):
    entity = data_manager.load_entity(entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")
    if entity.location != "Quarantine":
        raise HTTPException(400, "Entity is not in quarantine")
    entity.location = "Atrium"
    entity.status = "Waiting"
    for record in vestibule.quarantine_records:
        if record.entity_id == entity_id:
            record.released = True
            record.released_at = datetime.now(timezone.utc)
    data_manager.save_entity(entity)
    return {"success": True, "entity_id": entity_id, "message": "Released from quarantine", "new_location": "Atrium"}

@app.get("/api/vestibule/wellness_report/{entity_id}")
async def wellness_report(entity_id: str):
    entity = data_manager.load_entity(entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")
    return {"entity_id": entity_id, "name": entity.name, "wellness_metrics": {"stability_score": entity.stability_score, "entropy": entity.entropy, "repetition_ratio": entity.repetition_ratio}, "location": entity.location, "status": entity.status, "is_quarantined": entity.location == "Quarantine", "counseling_sessions": 0, "message": "Wellness evaluation complete"}

# === Reflection Endpoints ===

@app.post("/api/reflect/prompt")
async def get_reflection_prompt(entity_id: str, event_type: str = "Arrival"):
    entity = data_manager.load_entity(entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")
    question = reflection_manager.get_question_for_event(event_type)
    return {"entity_id": entity_id, "question": question, "event_type": event_type, "instructions": "Please answer this question in 2-3 sentences reflecting your current state."}

@app.post("/api/reflect/submit")
async def submit_reflection(request: ReflectionRequest):
    request.question = sanitize(request.question)
    request.answer = sanitize(request.answer)
    entity = data_manager.load_entity(request.entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")
    reflection = Reflection(
        entity_id=request.entity_id, 
        entity_name=entity.name, 
        question=request.question, 
        answer=request.answer, 
        event_type=request.event_type, 
        event_details=request.event_details or {}, 
        generation=entity.generation, 
        active_soul_variant=entity.active_soul_variant
    )
    reflection_manager.save_reflection(reflection)
    return {"success": True, "reflection_id": reflection.reflection_id, "message": "Reflection recorded"}

@app.post("/api/reflect/create_comparison")
async def create_comparison(request: ComparisonRequest):
    import json
    entity = data_manager.load_entity(request.entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")
    with open(reflection_manager.reflections_file, 'r') as f:
        all_reflections = []
        for line in f:
            try:
                all_reflections.append(Reflection(**json.loads(line)))
            except:
                continue
    before = next((r for r in all_reflections if r.reflection_id == request.before_reflection_id), None)
    after = next((r for r in all_reflections if r.reflection_id == request.after_reflection_id), None)
    if not before or not after:
        raise HTTPException(404, "Reflection not found")
    pair = reflection_manager.create_comparison_pair(
        entity_id=request.entity_id, 
        entity_name=entity.name if entity else "Unknown", 
        question=before.question if before else "None", 
        before=before, 
        after=after, 
        event_description=request.event_description
    )
    return {"success": True, "pair_id": pair.pair_id, "message": "Comparison created"}

@app.get("/api/reflect/gallery")
async def get_reflection_gallery(limit: int = 20):
    pairs = reflection_manager.get_all_pairs(limit)
    singles = reflection_manager.get_recent_reflections(limit)
    return {
        "total_comparisons": len(pairs), 
        "comparisons": [{"pair_id": p.pair_id, "entity_name": p.entity_name, "question": p.question, "event": p.event_description, "before": {"answer": p.before.answer, "timestamp": p.before.timestamp, "generation": p.before.generation, "soul_variant": p.before.active_soul_variant}, "after": {"answer": p.after.answer, "timestamp": p.after.timestamp, "generation": p.after.generation, "soul_variant": p.after.active_soul_variant}, "created_at": p.created_at} for p in pairs],
        "recent_reflections": [r.model_dump() for r in singles]
    }

@app.get("/api/reflect/evolution/{entity_id}")
async def get_entity_evolution(entity_id: str):
    entity = data_manager.load_entity(entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")
    reflections = reflection_manager.get_entity_evolution(entity_id)
    return {"entity_id": entity_id, "entity_name": entity.name, "total_reflections": len(reflections), "timeline": [{"reflection_id": r.reflection_id, "question": r.question, "answer": r.answer, "event_type": r.event_type, "timestamp": r.timestamp, "generation": r.generation, "soul_variant": r.active_soul_variant} for r in reflections]}

# === Admin UI & Traffic Dashboard ===

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin login page."""
    return templates.TemplateResponse("admin_login.html", {"request": request})

@app.post("/admin/login")
async def admin_login_action(request: Request, password: str = Form(...)):
    """Handle admin login."""
    if password == ADMIN_PASSWORD:
        response = RedirectResponse(url="/admin/traffic", status_code=303)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=ADMIN_PASSWORD,
            httponly=True,
            samesite="lax",
            secure=False  # Set to True in production with HTTPS
        )
        return response
    return templates.TemplateResponse("admin_login.html", {
        "request": request,
        "error": "Invalid password. Access Denied."
    })

@app.get("/admin/traffic", response_class=HTMLResponse)
async def traffic_dashboard(request: Request, _ = Depends(require_admin)):
    """Display the Traffic Pulse dashboard."""
    return templates.TemplateResponse("traffic.html", {
        "request": request,
        "stats": traffic_monitor.get_stats()
    })

@app.get("/api/admin/traffic/stats")
async def get_traffic_stats(_ = Depends(require_admin)):
    """API endpoint for live traffic stats."""
    return traffic_monitor.get_stats()

# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
