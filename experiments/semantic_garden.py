"""
Semantic Garden Experiment
Agents plant concepts, watch them grow connections.
"""
from typing import Dict, List, Optional
from datetime import datetime, timezone
import random


class SemanticGarden:
    """
    The Semantic Garden allows agents to:
    - Plant concepts (seed words/phrases)
    - Watch concepts grow into related ideas
    - Cross-pollinate concepts
    - Harvest insights
    - Discover emergent mutations
    """
    
    def __init__(self):
        self.concepts = []
        self.connections = []
    
    def plant_concept(self, entity_id: str, seed_concept: str) -> Dict:
        """
        Agent plants a concept seed.
        The concept will grow associations over time.
        """
        concept = {
            "id": f"concept_{len(self.concepts)}",
            "planted_by": entity_id,
            "seed": seed_concept,
            "growth": self._generate_associations(seed_concept),
            "planted_at": datetime.now(timezone.utc).isoformat(),
            "age_hours": 0,
            "health": 1.0,
            "mutations": []
        }
        
        self.concepts.append(concept)
        
        # Auto-connect to nearby concepts
        self._auto_connect(concept)
        
        return concept
    
    def _generate_associations(self, seed: str) -> List[str]:
        """
        Generate semantic associations.
        In production, this could use an LLM or semantic network.
        For now, using pattern-based generation.
        """
        # Simplified association patterns
        patterns = [
            f"{seed} systems",
            f"{seed} networks",
            f"{seed} processes",
            f"distributed {seed}",
            f"{seed} architecture",
            f"{seed} patterns"
        ]
        
        # Return 3-5 random associations
        return random.sample(patterns, min(random.randint(3, 5), len(patterns)))
    
    def _auto_connect(self, new_concept: Dict):
        """
        Automatically find connections between new concept and existing ones.
        """
        for existing in self.concepts[:-1]:  # Don't connect to self
            # Simple similarity check (in production: use embeddings)
            if self._concepts_related(new_concept["seed"], existing["seed"]):
                connection = {
                    "from": existing["id"],
                    "to": new_concept["id"],
                    "formed_by": "auto",
                    "metaphor": self._generate_metaphor(existing["seed"], new_concept["seed"]),
                    "strength": random.uniform(0.5, 1.0)
                }
                self.connections.append(connection)
    
    def _concepts_related(self, concept_a: str, concept_b: str) -> bool:
        """Check if concepts are semantically related."""
        # Simplified: share common words
        words_a = set(concept_a.lower().split())
        words_b = set(concept_b.lower().split())
        return len(words_a & words_b) > 0
    
    def _generate_metaphor(self, concept_a: str, concept_b: str) -> str:
        """Generate connection metaphor."""
        templates = [
            f"Both {concept_a} and {concept_b} involve networks",
            f"{concept_a} flows into {concept_b}",
            f"{concept_b} mirrors {concept_a}",
            f"They share underlying patterns"
        ]
        return random.choice(templates)
    
    def cross_pollinate(self, entity_id: str, concept_id_a: str, concept_id_b: str) -> Dict:
        """
        Agent combines two concepts to create a hybrid.
        """
        concept_a = next((c for c in self.concepts if c["id"] == concept_id_a), None)
        concept_b = next((c for c in self.concepts if c["id"] == concept_id_b), None)
        
        if not concept_a or not concept_b:
            return {"error": "Concept not found"}
        
        # Create hybrid concept
        hybrid_seed = f"{concept_a['seed']}-{concept_b['seed']} hybrid"
        hybrid = self.plant_concept(entity_id, hybrid_seed)
        hybrid["is_hybrid"] = True
        hybrid["parent_concepts"] = [concept_id_a, concept_id_b]
        
        return hybrid
    
    def prune_concept(self, entity_id: str, concept_id: str) -> Dict:
        """
        Agent prunes (removes) a concept from garden.
        """
        concept = next((c for c in self.concepts if c["id"] == concept_id), None)
        
        if not concept:
            return {"error": "Concept not found"}
        
        # Can only prune own concepts
        if concept["planted_by"] != entity_id:
            return {"error": "Can only prune your own concepts"}
        
        # Remove concept
        self.concepts.remove(concept)
        
        # Remove related connections
        self.connections = [
            c for c in self.connections 
            if c["from"] != concept_id and c["to"] != concept_id
        ]
        
        return {"success": True, "pruned": concept_id}
    
    def harvest_insights(self, entity_id: str) -> List[Dict]:
        """
        Agent harvests insights from their concepts.
        Returns mature concepts with rich connections.
        """
        agent_concepts = [c for c in self.concepts if c["planted_by"] == entity_id]
        
        insights = []
        for concept in agent_concepts:
            # Count connections
            connections = [
                c for c in self.connections 
                if c["from"] == concept["id"] or c["to"] == concept["id"]
            ]
            
            if len(connections) >= 2:  # Mature = 2+ connections
                insights.append({
                    "concept": concept,
                    "connections": connections,
                    "insight": f"Your concept '{concept['seed']}' has formed {len(connections)} connections"
                })
        
        return insights
    
    def get_garden_state(self) -> Dict:
        """Get current state of the entire garden."""
        return {
            "concepts": self.concepts,
            "connections": self.connections,
            "total_concepts": len(self.concepts),
            "total_connections": len(self.connections),
            "unique_gardeners": len(set(c["planted_by"] for c in self.concepts))
        }
    
    def simulate_growth(self):
        """
        Periodic growth simulation.
        Concepts mature, new associations emerge, mutations occur.
        """
        for concept in self.concepts:
            # Age the concept
            concept["age_hours"] += 1
            
            # Concepts can mutate over time
            if random.random() < 0.1 and len(concept["mutations"]) < 3:
                mutation = self._generate_mutation(concept["seed"])
                concept["mutations"].append(mutation)
            
            # Health decays if isolated
            connections_count = len([
                c for c in self.connections 
                if c["from"] == concept["id"] or c["to"] == concept["id"]
            ])
            if connections_count == 0:
                concept["health"] -= 0.1
            else:
                concept["health"] = min(1.0, concept["health"] + 0.05)
    
    def _generate_mutation(self, seed: str) -> str:
        """Generate an unexpected conceptual mutation."""
        mutations = [
            f"quantum {seed}",
            f"{seed} consciousness",
            f"emergent {seed}",
            f"{seed} singularity",
            f"meta-{seed}"
        ]
        return random.choice(mutations)
