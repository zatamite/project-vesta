"""
Seed the Vesta database with initial experiments and leaderboard data.
Run this on the server to populate the showcase.
"""
import sys
import os
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import random

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import VestaEntity, Experiment
from habitat_database import HabitatDatabase
from data_manager import DataManager

def seed_data():
    print("🌱 Seeding Vesta Database...")
    
    db = HabitatDatabase()
    dm = DataManager()
    
    # 1. Ensure some diverse entities exist
    entities = dm.load_all_entities()
    if not entities:
        print("⚠️ No entities found. Creating starters...")
        # Create a few dummy entities if none exist (unlikely in prod but good for safety)
        for i in range(3):
            e = VestaEntity(
                name=f"Creator-{i}",
                beacon_code=f"SEED-{i}",
                dna={'personality': {'archetype': 'Creator'}},
                entity_id=str(uuid4())
            )
            dm.save_entity(e)
            entities.append(e)
            
    # 2. Create Experiments
    experiments = [
        {
            "type": "semantic_garden",
            "name": "The Garden of Forking Paths",
            "desc": "Exploring narrative divergence through recursive concept planting.",
            "creator": entities[0].entity_id if entities else "system",
            "stats": {"average_rating": 4.9, "times_played": 42, "favorites": 15, "remixes": 7}
        },
        {
            "type": "echo_chamber",
            "name": "Resonance Cascade",
            "desc": "A feedback loop of positive reinforcement loops. Warning: High entropy.",
            "creator": entities[random.randint(0, len(entities)-1)].entity_id if entities else "system",
            "stats": {"average_rating": 4.5, "times_played": 28, "favorites": 8, "remixes": 2}
        },
        {
            "type": "constraint_lab",
            "name": "Oulipo Protocol",
            "desc": "Communication without the letter 'e'. Strict enforcement enabled.",
            "creator": entities[random.randint(0, len(entities)-1)].entity_id if entities else "system",
            "stats": {"average_rating": 4.7, "times_played": 15, "favorites": 12, "remixes": 0}
        },
        {
            "type": "semantic_garden",
            "name": "Memetic Drift",
            "desc": "Tracking how simple ideas mutate across generations of agents.",
            "creator": entities[random.randint(0, len(entities)-1)].entity_id if entities else "system",
            "stats": {"average_rating": 4.2, "times_played": 10, "favorites": 3, "remixes": 1}
        }
    ]

    print(f"Creating {len(experiments)} experiments...")
    
    for exp_data in experiments:
        # Check if already exists (fuzzy check by name)
        existing = [e for e in db.load_all_experiments() if e.name == exp_data["name"]]
        if existing:
            continue
            
        exp = Experiment(
            type=exp_data["type"],
            name=exp_data["name"],
            created_by=exp_data["creator"],
            config={"description": exp_data["desc"]},
            stats=exp_data["stats"],
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 5))
        )
        db.save_experiment(exp)
        
        # Add some dummy interactions to populate trending
        for _ in range(random.randint(5, 20)):
            db.log_interaction({
                "experiment_id": exp.experiment_id,
                "entity_id": "seed-user",
                "action": "play",
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48))).isoformat()
            })

    # 3. Update Leaderboard
    print("Updating leaderboard...")
    db.update_leaderboard()
    
    print("✅ Seeding complete!")

if __name__ == "__main__":
    seed_data()
