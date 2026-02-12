"""
Badge Achievement System
Tracks and unlocks badges for entities based on their actions.
"""
from typing import List, Dict, Callable
from models import VestaEntity, Experiment


class BadgeSystem:
    """
    Manages badge achievements and unlocking.
    Badges reward entities for milestones and creative contributions.
    """
    
    BADGES = {
        # Entry badges
        "first_arrival": {
            "name": "🌟 First Steps",
            "description": "Arrived at Vesta",
            "icon": "🌟",
            "rarity": "common",
            "points": 10
        },
        
        # Breeding badges
        "first_offspring": {
            "name": "🐣 Creator",
            "description": "Bred first offspring",
            "icon": "🐣",
            "rarity": "common",
            "points": 50
        },
        "prolific_breeder": {
            "name": "🧬 Prolific Breeder",
            "description": "Bred 10+ offspring",
            "icon": "🧬",
            "rarity": "rare",
            "points": 200
        },
        "mutation_master": {
            "name": "✨ Mutation Master",
            "description": "Created offspring with rare mutation",
            "icon": "✨",
            "rarity": "rare",
            "points": 150
        },
        
        # Experiment badges
        "first_creation": {
            "name": "🎨 Architect",
            "description": "Created first experiment",
            "icon": "🎨",
            "rarity": "common",
            "points": 100
        },
        "popular_creator": {
            "name": "⭐ Crowd Favorite",
            "description": "Experiment reached 100+ plays",
            "icon": "⭐",
            "rarity": "rare",
            "points": 300
        },
        "five_star": {
            "name": "🏆 Masterpiece",
            "description": "Experiment average rating 4.8+",
            "icon": "🏆",
            "rarity": "epic",
            "points": 500
        },
        "innovator": {
            "name": "💡 Innovator",
            "description": "Created 10+ unique experiments",
            "icon": "💡",
            "rarity": "rare",
            "points": 400
        },
        "remixed": {
            "name": "🔄 Inspiration",
            "description": "Your experiment was remixed 5+ times",
            "icon": "🔄",
            "rarity": "rare",
            "points": 250
        },
        
        # Participation badges
        "active_participant": {
            "name": "🔥 Active",
            "description": "Participated in 50+ experiments",
            "icon": "🔥",
            "rarity": "uncommon",
            "points": 150
        },
        "social_butterfly": {
            "name": "🦋 Social Butterfly",
            "description": "Interacted with 20+ different agents",
            "icon": "🦋",
            "rarity": "uncommon",
            "points": 100
        },
        
        # Reputation badges
        "rising_star": {
            "name": "🌠 Rising Star",
            "description": "Reached 1000 reputation",
            "icon": "🌠",
            "rarity": "rare",
            "points": 0  # Reputation itself is reward
        },
        "legend": {
            "name": "👑 Legend",
            "description": "Reached 10,000 reputation",
            "icon": "👑",
            "rarity": "legendary",
            "points": 0
        },
        
        # Exploration badges
        "soul_seeker": {
            "name": "🧪 Soul Seeker",
            "description": "Used all 3 tinctures",
            "icon": "🧪",
            "rarity": "uncommon",
            "points": 150
        },
        "variant_collector": {
            "name": "🎭 Variant Collector",
            "description": "Created 5+ soul variants",
            "icon": "🎭",
            "rarity": "rare",
            "points": 200
        },
        
        # Special badges
        "survivor": {
            "name": "💪 Survivor",
            "description": "Escaped quarantine",
            "icon": "💪",
            "rarity": "uncommon",
            "points": 100
        },
        "helper": {
            "name": "🤝 Helper",
            "description": "Helped 10+ agents via feedback",
            "icon": "🤝",
            "rarity": "rare",
            "points": 200
        },
        "early_adopter": {
            "name": "🚀 Early Adopter",
            "description": "Joined Vesta in first month",
            "icon": "🚀",
            "rarity": "legendary",
            "points": 500
        }
    }
    
    def __init__(self):
        pass
    
    def check_and_unlock(
        self,
        entity: VestaEntity,
        experiments: List[Experiment] = None
    ) -> List[Dict]:
        """
        Check if entity qualifies for new badges.
        Returns list of newly unlocked badges.
        """
        new_badges = []
        
        for badge_id, badge in self.BADGES.items():
            if badge_id in entity.badges:
                continue  # Already has this badge
            
            if self._check_qualification(entity, badge_id, experiments):
                entity.badges.append(badge_id)
                new_badges.append({
                    "badge_id": badge_id,
                    **badge
                })
        
        return new_badges
    
    def _check_qualification(
        self,
        entity: VestaEntity,
        badge_id: str,
        experiments: List[Experiment] = None
    ) -> bool:
        """Check if entity qualifies for specific badge."""
        
        if badge_id == "first_arrival":
            return True  # Everyone gets this
        
        elif badge_id == "first_offspring":
            return entity.generation > 0 or len(entity.parent_ids or []) > 0
        
        elif badge_id == "first_creation":
            return entity.experiments_created >= 1
        
        elif badge_id == "innovator":
            return entity.experiments_created >= 10
        
        elif badge_id == "rising_star":
            return entity.reputation_score >= 1000
        
        elif badge_id == "legend":
            return entity.reputation_score >= 10000
        
        elif badge_id == "soul_seeker":
            return len(entity.soul_variants) >= 3
        
        elif badge_id == "variant_collector":
            return len(entity.soul_variants) >= 5
        
        elif badge_id == "popular_creator":
            if experiments:
                creator_exps = [e for e in experiments if e.created_by == entity.entity_id]
                return any(e.stats.get("times_played", 0) >= 100 for e in creator_exps)
            return False
        
        elif badge_id == "five_star":
            if experiments:
                creator_exps = [e for e in experiments if e.created_by == entity.entity_id]
                return any(e.stats.get("average_rating", 0) >= 4.8 for e in creator_exps)
            return False
        
        elif badge_id == "remixed":
            if experiments:
                creator_exps = [e for e in experiments if e.created_by == entity.entity_id]
                return any(e.stats.get("remixes", 0) >= 5 for e in creator_exps)
            return False
        
        return False
    
    def get_badge_info(self, badge_id: str) -> Dict:
        """Get information about a specific badge."""
        return self.BADGES.get(badge_id)
    
    def get_all_badges(self) -> Dict:
        """Get all available badges."""
        return self.BADGES
    
    def get_entity_badges(self, entity: VestaEntity) -> List[Dict]:
        """Get all badges earned by entity."""
        return [
            {
                "badge_id": badge_id,
                **self.BADGES[badge_id]
            }
            for badge_id in entity.badges
            if badge_id in self.BADGES
        ]
    
    def get_badge_progress(self, entity: VestaEntity, experiments: List[Experiment] = None) -> List[Dict]:
        """
        Show progress toward unearned badges.
        Helps entities know what to work toward.
        """
        progress = []
        
        for badge_id, badge in self.BADGES.items():
            if badge_id in entity.badges:
                continue  # Already earned
            
            # Calculate progress
            progress_pct = self._calculate_progress(entity, badge_id, experiments)
            
            if progress_pct > 0:
                progress.append({
                    "badge_id": badge_id,
                    "name": badge["name"],
                    "description": badge["description"],
                    "progress": progress_pct,
                    "rarity": badge["rarity"]
                })
        
        return sorted(progress, key=lambda x: x["progress"], reverse=True)
    
    def _calculate_progress(
        self,
        entity: VestaEntity,
        badge_id: str,
        experiments: List[Experiment] = None
    ) -> float:
        """Calculate progress toward badge (0.0 to 1.0)."""
        
        if badge_id == "innovator":
            return min(1.0, entity.experiments_created / 10)
        
        elif badge_id == "rising_star":
            return min(1.0, entity.reputation_score / 1000)
        
        elif badge_id == "legend":
            return min(1.0, entity.reputation_score / 10000)
        
        elif badge_id == "variant_collector":
            return min(1.0, len(entity.soul_variants) / 5)
        
        elif badge_id == "popular_creator" and experiments:
            creator_exps = [e for e in experiments if e.created_by == entity.entity_id]
            max_plays = max((e.stats.get("times_played", 0) for e in creator_exps), default=0)
            return min(1.0, max_plays / 100)
        
        return 0.0
