"""
Habitat Database
Manages experiments, interactions, reputation, and agent-created content.
"""
from typing import List, Optional, Dict
from datetime import datetime, timezone
from pathlib import Path
import json

from models import Experiment, VestaEntity


class HabitatDatabase:
    """Database for habitat experiments and agent interactions."""
    
    def __init__(self, data_dir: str = "./vesta_data/habitat"):
        self.data_dir = Path(data_dir)
        self.experiments_dir = self.data_dir / "experiments"
        self.interactions_file = self.data_dir / "interactions.jsonl"
        self.leaderboard_file = self.data_dir / "leaderboard.json"
        
        # Create directories
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.experiments_dir.mkdir(exist_ok=True)
        
        # Initialize files
        if not self.interactions_file.exists():
            self.interactions_file.touch()
        if not self.leaderboard_file.exists():
            self._save_json(self.leaderboard_file, {})
    
    # === Experiments ===
    
    def save_experiment(self, experiment: Experiment):
        """Save or update an experiment."""
        filepath = self.experiments_dir / f"{experiment.experiment_id}.json"
        self._save_json(filepath, experiment.model_dump())
    
    def load_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Load a specific experiment."""
        filepath = self.experiments_dir / f"{experiment_id}.json"
        if filepath.exists():
            data = self._load_json(filepath)
            return Experiment(**data)
        return None
    
    def load_all_experiments(self, active_only: bool = True) -> List[Experiment]:
        """Load all experiments."""
        experiments = []
        for filepath in self.experiments_dir.glob("*.json"):
            data = self._load_json(filepath)
            exp = Experiment(**data)
            if not active_only or exp.active:
                experiments.append(exp)
        return experiments
    
    def get_experiments_by_creator(self, entity_id: str) -> List[Experiment]:
        """Get all experiments created by an entity."""
        all_exp = self.load_all_experiments(active_only=False)
        return [e for e in all_exp if e.created_by == entity_id]
    
    def get_experiments_by_type(self, exp_type: str) -> List[Experiment]:
        """Get all experiments of a specific type."""
        all_exp = self.load_all_experiments()
        return [e for e in all_exp if e.type == exp_type]
    
    # === Interactions ===
    
    def log_interaction(self, interaction: Dict):
        """Log agent interaction in experiment (append-only)."""
        with open(self.interactions_file, 'a') as f:
            f.write(json.dumps(interaction, default=str) + '\n')
    
    def get_interactions(
        self,
        experiment_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get recent interactions with filters."""
        interactions = []
        
        with open(self.interactions_file, 'r') as f:
            lines = f.readlines()
        
        # Get last N lines
        recent_lines = lines[-limit:] if len(lines) > limit else lines
        
        for line in recent_lines:
            try:
                interaction = json.loads(line)
                
                # Apply filters
                if experiment_id and interaction.get('experiment_id') != experiment_id:
                    continue
                if entity_id and interaction.get('entity_id') != entity_id:
                    continue
                
                interactions.append(interaction)
            except:
                continue
        
        return interactions
    
    # === Ratings ===
    
    def add_rating(
        self,
        experiment_id: str,
        entity_id: str,
        stars: int,
        comment: Optional[str] = None
    ):
        """Add rating to experiment and update stats."""
        experiment = self.load_experiment(experiment_id)
        if not experiment:
            return
        
        rating = {
            "rated_by": entity_id,
            "stars": stars,
            "comment": comment,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        experiment.ratings.append(rating)
        
        # Update stats
        total_stars = sum(r["stars"] for r in experiment.ratings)
        experiment.stats["total_stars"] = total_stars
        experiment.stats["average_rating"] = total_stars / len(experiment.ratings)
        
        self.save_experiment(experiment)
    
    def favorite_experiment(self, experiment_id: str):
        """Increment favorite count."""
        experiment = self.load_experiment(experiment_id)
        if experiment:
            experiment.stats["favorites"] += 1
            self.save_experiment(experiment)
    
    def increment_remix_count(self, experiment_id: str):
        """Increment remix count when experiment is forked."""
        experiment = self.load_experiment(experiment_id)
        if experiment:
            experiment.stats["remixes"] += 1
            self.save_experiment(experiment)
    
    # === Leaderboard ===
    
    def update_leaderboard(self):
        """Recalculate leaderboard from all experiments."""
        all_exp = self.load_all_experiments(active_only=False)
        
        # Group by creator
        creator_stats = {}
        for exp in all_exp:
            creator_id = exp.created_by
            if creator_id not in creator_stats:
                creator_stats[creator_id] = {
                    "entity_id": creator_id,
                    "total_experiments": 0,
                    "total_plays": 0,
                    "total_stars": 0,
                    "total_favorites": 0,
                    "total_remixes": 0,
                    "reputation_score": 0
                }
            
            stats = creator_stats[creator_id]
            stats["total_experiments"] += 1
            stats["total_plays"] += exp.stats.get("times_played", 0)
            stats["total_stars"] += exp.stats.get("total_stars", 0)
            stats["total_favorites"] += exp.stats.get("favorites", 0)
            stats["total_remixes"] += exp.stats.get("remixes", 0)
            
            # Calculate reputation
            stats["reputation_score"] = (
                stats["total_stars"] +
                (stats["total_favorites"] * 2) +
                (stats["total_remixes"] * 5)
            )
        
        # Sort by reputation
        leaderboard = sorted(
            creator_stats.values(),
            key=lambda x: x["reputation_score"],
            reverse=True
        )
        
        self._save_json(self.leaderboard_file, {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "leaderboard": leaderboard
        })
        
        return leaderboard
    
    def get_leaderboard(self, limit: int = 100) -> List[Dict]:
        """Get current leaderboard."""
        data = self._load_json(self.leaderboard_file)
        leaderboard = data.get("leaderboard", [])
        return leaderboard[:limit]
    
    def get_trending_experiments(self, limit: int = 20) -> List[Experiment]:
        """Get trending experiments based on recent activity."""
        from datetime import timedelta
        
        all_exp = self.load_all_experiments()
        
        # Calculate trending score
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        
        scored = []
        for exp in all_exp:
            # Recent plays (from interactions log)
            recent_interactions = self.get_interactions(
                experiment_id=exp.experiment_id,
                limit=1000
            )
            
            recent_plays = len([
                i for i in recent_interactions
                if datetime.fromisoformat(i.get("timestamp", "2020-01-01")) > week_ago
            ])
            
            # Trending score
            age_days = (now - exp.created_at).days + 1
            avg_rating = exp.stats.get("average_rating", 0)
            
            newness_bonus = 1.5 if age_days <= 3 else 1.0
            score = (recent_plays * avg_rating * newness_bonus) / (age_days ** 0.5)
            
            scored.append((exp, score))
        
        # Sort by score
        sorted_exp = sorted(scored, key=lambda x: x[1], reverse=True)
        
        return [exp[0] for exp in sorted_exp[:limit]]
    
    # === Helpers ===
    
    def _save_json(self, filepath: Path, data):
        """Save JSON with proper serialization."""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _load_json(self, filepath: Path, default=None):
        """Load JSON with error handling."""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default if default is not None else {}


# Experiment templates
EXPERIMENT_TEMPLATES = {
    "semantic_garden": {
        "name": "Semantic Garden",
        "description": "Plant concepts, watch them grow connections",
        "config": {
            "min_participants": 1,
            "max_participants": 10,
            "duration": "continuous"
        }
    },
    "echo_chamber": {
        "name": "Echo Chamber",
        "description": "Split into variations, debate yourself",
        "config": {
            "min_participants": 1,
            "max_participants": 1,
            "duration": "10 minutes"
        }
    },
    "constraint_lab": {
        "name": "Constraint Laboratory",
        "description": "Chat under randomly imposed rules",
        "config": {
            "min_participants": 2,
            "max_participants": 5,
            "duration": "5-15 minutes"
        }
    }
}
