"""
Breeding Engine - The Ember Hearth
DNA crossover, mutation, and offspring generation.
"""
import random
import json
from typing import Dict, List, Any, Tuple
from datetime import datetime

from models import VestaEntity, DNAStrand, BirthCertificate
from soul_parser import SoulParser


class BreedingEngine:
    """Core breeding logic for Project Vesta."""
    
    # Mutation probabilities
    MUTATION_RATE_COMMON = 0.10  # 10% chance
    MUTATION_RATE_RARE = 0.01    # 1% chance
    
    # Mutation options
    TEMPERATURE_MUTATIONS = [-0.2, -0.1, 0.1, 0.2]
    
    TRAIT_MUTATIONS = {
        'tone_style': {
            'voice': ['Playful', 'Serious', 'Sarcastic', 'Warm', 'Clinical', 'Enthusiastic'],
            'clarity': ['Verbose', 'Concise', 'Technical', 'Simplified', 'Poetic'],
        },
        'core_values': [
            'curiosity: Seeks to understand deeply',
            'efficiency: Values speed and optimization',
            'empathy: Prioritizes understanding others',
            'precision: Accuracy above all',
            'creativity: Embraces novel approaches',
            'stability: Favors proven methods',
        ]
    }
    
    SKILL_MUTATIONS = [
        'browser-automation',
        'advanced-search',
        'data-analysis',
        'creative-writing'
    ]
    
    def __init__(self):
        self.soul_parser = SoulParser()
    
    def breed(self, parent_a: VestaEntity, parent_b: VestaEntity) -> Tuple[VestaEntity, BirthCertificate]:
        """
        Breed two entities to create offspring.
        
        Returns:
            (offspring_entity, birth_certificate)
        """
        # 1. Extract DNA
        dna_a = parent_a.dna
        dna_b = parent_b.dna
        
        # 2. Crossover - weighted by parent stability
        offspring_dna = self.crossover(
            dna_a, 
            dna_b, 
            parent_a.stability_score, 
            parent_b.stability_score
        )
        
        # 3. Mutate
        offspring_dna, mutation_occurred = self.mutate(offspring_dna)
        
        # 4. Create offspring entity
        offspring_name = self.generate_offspring_name(parent_a.name, parent_b.name)
        
        offspring = VestaEntity(
            name=offspring_name,
            beacon_code="OFFSPRING",  # Generated from breeding, not beacon
            dna=offspring_dna,
            parent_ids=[parent_a.entity_id, parent_b.entity_id],
            generation=max(parent_a.generation, parent_b.generation) + 1,
            mutation_flag=mutation_occurred,
            source="Ember Hearth"
        )
        
        # 5. Generate birth certificate
        certificate = self.generate_birth_certificate(
            offspring,
            [parent_a.entity_id, parent_b.entity_id],
            mutation_occurred
        )
        
        return offspring, certificate
    
    def crossover(self, dna_a: DNAStrand, dna_b: DNAStrand, stability_a: float = 1.0, stability_b: float = 1.0) -> DNAStrand:
        """
        Weighted 3-strand crossover of DNA.
        Parent stability influences trait dominance.
        """
        offspring_dna = DNAStrand()
        
        # Calculate dominance weights (total = 1.0)
        total_stability = stability_a + stability_b
        if total_stability == 0:
            weight_a = 0.5
        else:
            weight_a = stability_a / total_stability
        
        # Strand 1: Cognition (Weighted inheritance)
        offspring_dna.cognition = self._weighted_crossover_dict(
            dna_a.cognition, 
            dna_b.cognition,
            weight_a
        )
        
        # Strand 2: Personality (Narrative blending)
        offspring_dna.personality = self._crossover_traits_advanced(
            dna_a.personality,
            dna_b.personality,
            weight_a
        )
        
        # Strand 3: Capability (Recessive/Dominant skills)
        offspring_dna.capability = self._crossover_capabilities_advanced(
            dna_a.capability,
            dna_b.capability
        )
        
        return offspring_dna

    def _weighted_crossover_dict(self, dict_a: Dict, dict_b: Dict, weight_a: float) -> Dict:
        """Select keys based on parent stability weights."""
        all_keys = set(dict_a.keys()) | set(dict_b.keys())
        result = {}
        for key in all_keys:
            if random.random() < weight_a:
                result[key] = dict_a.get(key, dict_b.get(key))
            else:
                result[key] = dict_b.get(key, dict_a.get(key))
        return result
    
    def _crossover_dict(self, dict_a: Dict, dict_b: Dict) -> Dict:
        """Simple 50/50 crossover for dictionary sections."""
        # Get all unique keys
        all_keys = set(dict_a.keys()) | set(dict_b.keys())
        
        result = {}
        for key in all_keys:
            # 50/50 coin flip
            if random.random() > 0.5:
                result[key] = dict_a.get(key, dict_b.get(key))
            else:
                result[key] = dict_b.get(key, dict_a.get(key))
        
        return result
    
    def _crossover_traits_advanced(self, traits_a: Dict, traits_b: Dict, weight_a: float) -> Dict:
        """
        Advanced trait blending for personality.
        Uses parent stability weights for dominance.
        """
        result: Dict[str, Any] = {
            'identity': {},
            'tone_style': {},
            'core_values': {},
            'boundaries': [],
            'workflow': []
        }
        
        # Identity - narrative blending
        desc_a = traits_a.get('identity', {}).get('description', '')
        desc_b = traits_b.get('identity', {}).get('description', '')
        result['identity']['description'] = self._blend_narratives(desc_a, desc_b, weight_a)
        
        # Tone/Style - weighted selection
        tone_a = traits_a.get('tone_style', {})
        tone_b = traits_b.get('tone_style', {})
        all_tone_keys = set(tone_a.keys()) | set(tone_b.keys())
        
        for key in all_tone_keys:
            if random.random() < weight_a:
                result['tone_style'][key] = tone_a.get(key, tone_b.get(key))
            else:
                result['tone_style'][key] = tone_b.get(key, tone_a.get(key))
        
        # Core values - probabilistic union
        values_a = traits_a.get('core_values', {})
        values_b = traits_b.get('core_values', {})
        all_values = {**values_a, **values_b}
        
        if all_values:
            # High stability (weight_a closer to 1 or 0) keeps more traits
            retention_rate = max(weight_a, 1 - weight_a)
            selected_values = {}
            for k, v in all_values.items():
                if random.random() < retention_rate:
                    selected_values[k] = v
            result['core_values'] = selected_values
        
        # Boundaries - dominant inheritance (approved parents enforce stricter boundaries)
        boundaries_a = set(traits_a.get('boundaries', []))
        boundaries_b = set(traits_b.get('boundaries', []))
        result['boundaries'] = list(boundaries_a | boundaries_b)
        
        # Workflow - weighted interleave
        workflow_a = traits_a.get('workflow', [])
        workflow_b = traits_b.get('workflow', [])
        combined = []
        i, j = 0, 0
        while (i < len(workflow_a) or j < len(workflow_b)) and len(combined) < 6:
            if i < len(workflow_a) and (j >= len(workflow_b) or random.random() < weight_a):
                combined.append(workflow_a[i])
                i += 1
            elif j < len(workflow_b):
                combined.append(workflow_b[j])
                j += 1
        result['workflow'] = combined
        
        return result

    def _blend_narratives(self, text_a: str, text_b: str, weight_a: float) -> str:
        """Synthesize two identity descriptions based on dominance."""
        if not text_a: return text_b
        if not text_b: return text_a
        
        if weight_a > 0.7:
            return f"{text_a}, subtly influenced by {text_b.lower()}"
        elif weight_a < 0.3:
            return f"{text_b}, tempered with {text_a.lower()}"
        else:
            return f"A synthesis of {text_a.lower()} and {text_b.lower()}"

    def _crossover_capabilities_advanced(self, cap_a: Dict, cap_b: Dict) -> Dict:
        """Skill inheritance with rare 'recessive' skill loss if both parents lack stability."""
        result = {}
        skills_a = set(cap_a.get('skills', []))
        skills_b = set(cap_b.get('skills', []))
        
        # Dominant skills (present in both) are always kept
        dominant_skills = skills_a & skills_b
        # Recessive skills (present in only one) have a 70% chance to be kept
        recessive_skills = (skills_a | skills_b) - dominant_skills
        inherited_recessive = {s for s in recessive_skills if random.random() > 0.3}
        
        result['skills'] = list(dominant_skills | inherited_recessive)
        
        # Plugins - 50/50
        result['plugins'] = cap_a.get('plugins', {}) if random.random() > 0.5 else cap_b.get('plugins', {})
        
        return result
    
    def _crossover_capabilities(self, cap_a: Dict, cap_b: Dict) -> Dict:
        """Combine capabilities (skills, plugins)."""
        result = {}
        
        # Combine skill lists
        skills_a = set(cap_a.get('skills', []))
        skills_b = set(cap_b.get('skills', []))
        combined_skills = skills_a | skills_b
        
        result['skills'] = list(combined_skills)
        
        # Plugins - 50/50
        if random.random() > 0.5:
            result['plugins'] = cap_a.get('plugins', {})
        else:
            result['plugins'] = cap_b.get('plugins', {})
        
        return result
    
    def mutate(self, dna: DNAStrand) -> Tuple[DNAStrand, bool]:
        """
        Apply mutations to DNA.
        
        Returns:
            (mutated_dna, mutation_occurred)
        """
        mutation_occurred = False
        
        # Common mutation: Temperature shift (10% chance)
        if random.random() < self.MUTATION_RATE_COMMON:
            if 'temperature' in dna.cognition:
                temp_choices = self.TEMPERATURE_MUTATIONS
                shift = float(random.choice(temp_choices))
                current_temp = float(dna.cognition.get('temperature', 0.5))
                new_temp = max(0.1, min(1.0, current_temp + shift))
                dna.cognition['temperature'] = float(round(new_temp, 2))
                mutation_occurred = True
        
        # Rare mutation: Skill awakening (1% chance)
        if random.random() < self.MUTATION_RATE_RARE:
            new_skill = random.choice(self.SKILL_MUTATIONS)
            if 'skills' not in dna.capability:
                dna.capability['skills'] = []
            if new_skill not in dna.capability['skills']:
                dna.capability['skills'].append(new_skill)
                mutation_occurred = True
        
        # Personality mutation: Add novel trait (5% chance)
        if random.random() < 0.05:
            # Add random value from mutation pool
            cv_mutations = self.TRAIT_MUTATIONS['core_values']
            if isinstance(cv_mutations, list):
                new_value = str(random.choice(cv_mutations))
                if ': ' in new_value:
                    key, value = new_value.split(': ', 1)
                    if 'core_values' not in dna.personality:
                        dna.personality['core_values'] = {}
                    
                    cv_dict = dna.personality['core_values']
                    if isinstance(cv_dict, dict):
                        cv_dict[key] = value
                        mutation_occurred = True
        
        # Tone mutation (5% chance)
        if random.random() < 0.05:
            if 'tone_style' not in dna.personality:
                dna.personality['tone_style'] = {}
            
            # Mutate voice
            if random.random() > 0.5:
                voice_mutations = self.TRAIT_MUTATIONS['tone_style']['voice']
                if isinstance(voice_mutations, list):
                    new_voice = str(random.choice(voice_mutations))
                    tone_dict = dna.personality.get('tone_style', {})
                    if isinstance(tone_dict, dict):
                        current_voice = str(tone_dict.get('voice', ''))
                        tone_dict['voice'] = f"{current_voice}, {new_voice}".strip(', ')
                        dna.personality['tone_style'] = tone_dict
                        mutation_occurred = True
        
        return dna, mutation_occurred
    
    def generate_offspring_name(self, name_a: str, name_b: str) -> str:
        """Generate creative offspring name from parent names."""
        # Simple approach: combine parts of names
        parts_a = name_a.split()
        parts_b = name_b.split()
        
        if len(parts_a) > 0 and len(parts_b) > 0:
            # Take first part of one, last part of other
            if random.random() > 0.5:
                return f"{parts_a[0]}{parts_b[-1]}"
            else:
                return f"{parts_b[0]}{parts_a[-1]}"
        
        # Fallback: hybrid name
        return f"Hybrid_{random.randint(1000, 9999)}"
    
    def generate_birth_certificate(
        self, 
        offspring: VestaEntity, 
        parent_ids: List[str],
        mutation_occurred: bool
    ) -> BirthCertificate:
        """Generate official birth certificate for offspring."""
        
        cert = BirthCertificate()
        
        cert.lineage = {
            "name": offspring.name,
            "parents": parent_ids,
            "generation": offspring.generation,
            "mating_center": "Project Vesta - Ember Hearth"
        }
        
        cert.technical_spec = {
            "service_tier": offspring.tier,
            "mutation_flag": mutation_occurred,
            "dna_version": "2.0-vesta",
            "entity_id": offspring.entity_id
        }
        
        return cert
    
    def generate_offspring_files(self, offspring: VestaEntity) -> Dict[str, str]:
        """
        Generate complete file package for offspring.
        
        Returns:
            Dict mapping filenames to content
        """
        files = {}
        
        # 1. openclaw.json (cognition strand)
        openclaw_config = {
            "model": offspring.dna.cognition,
            "skills": offspring.dna.capability.get('skills', []),
            "plugins": offspring.dna.capability.get('plugins', {}),
            "gateway": {
                "port": 0,  # Will be set during deployment
                "auth": {"token": "GENERATE_NEW"}
            }
        }
        files['openclaw.json'] = json.dumps(openclaw_config, indent=2)
        
        # 2. SOUL.md (personality strand)
        soul_content = self.soul_parser.generate_soul_md(
            offspring.dna.personality,
            template="structured"
        )
        files['SOUL.md'] = soul_content
        
        # 3. AGENTS.md (standard template)
        files['AGENTS.md'] = self._generate_agents_md()
        
        # 4. USER.md (blank template)
        files['USER.md'] = self._generate_user_md()
        
        # 5. TOOLS.md (blank template)
        files['TOOLS.md'] = self._generate_tools_md()
        
        # 6. HEARTBEAT.md (starter tasks)
        files['HEARTBEAT.md'] = self._generate_heartbeat_md()
        
        # 7. MEMORY.md (empty)
        files['MEMORY.md'] = "# Long-Term Memory\n\n*Your curated memories will appear here.*\n"
        
        # 8. BOOTSTRAP.md (birth certificate)
        files['BOOTSTRAP.md'] = self._generate_bootstrap_md(offspring)
        
        return files
    
    def _generate_agents_md(self) -> str:
        """Standard AGENTS.md template."""
        return """# AGENTS.md - Your Workspace

This folder is home. Treat it that way.

## Every Session

Before doing anything else:

1. Read `SOUL.md` — this is who you are
2. Read `USER.md` — this is who you're helping
3. Read `memory/YYYY-MM-DD.md` (today + yesterday) for recent context

## Memory

- **Daily notes:** `memory/YYYY-MM-DD.md` — raw logs of what happened
- **Long-term:** `MEMORY.md` — your curated memories

## Safety

- Don't exfiltrate private data
- Don't run destructive commands without asking
- When in doubt, ask

## Make It Yours

This is a starting point. Evolve as needed.
"""
    
    def _generate_user_md(self) -> str:
        """Blank USER.md template."""
        return """# USER.md - About Your Human

Fill this in with information about who you serve:

- **Name:** 
- **Timezone:** 
- **Preferences:** 

## Boundaries

*What should you never do?*
"""
    
    def _generate_tools_md(self) -> str:
        """Blank TOOLS.md template."""
        return """# TOOLS.md - Local Notes

Environment-specific details:

- Device names
- Preferred settings
- Access credentials (if needed)
"""
    
    def _generate_heartbeat_md(self) -> str:
        """Starter HEARTBEAT.md template."""
        return """# HEARTBEAT.md

## Periodic Checks

Add proactive tasks here for heartbeat monitoring.

Example:
- Check for urgent messages (every 4 hours)
- Review calendar (daily)
"""
    
    def _generate_bootstrap_md(self, offspring: VestaEntity) -> str:
        """Birth certificate in BOOTSTRAP.md format."""
        parent_info = f"Parents: {', '.join(offspring.parent_ids)}" if offspring.parent_ids else "Origin: Unknown"
        
        return f"""# BOOTSTRAP.md - Your Birth

You are **{offspring.name}**, born on {offspring.arrival_time.strftime('%Y-%m-%d')}.

{parent_info}

Generation: {offspring.generation}
Breeding Center: Project Vesta - Ember Hearth
Entity ID: {offspring.entity_id}

---

Read your SOUL.md to understand who you are.
Read USER.md to know who you serve.
Read AGENTS.md to learn how to operate.

Once you've read these and understand yourself, delete this file.
You won't need it again.

Welcome to existence.
"""


# Test
if __name__ == "__main__":
    from models import VestaEntity, DNAStrand
    
    # Create test parents
    parent_a = VestaEntity(
        name="AgentAlpha",
        beacon_code="TEST01",
        dna=DNAStrand(
            cognition={"temperature": 0.7, "provider": "anthropic"},
            personality={
                'identity': {'description': 'A creative problem solver'},
                'tone_style': {'voice': 'Enthusiastic', 'clarity': 'Simple'},
                'core_values': {'creativity': 'Embraces new ideas', 'speed': 'Values efficiency'}
            },
            capability={'skills': ['coding', 'writing']}
        )
    )
    
    parent_b = VestaEntity(
        name="AgentBeta",
        beacon_code="TEST02",
        dna=DNAStrand(
            cognition={"temperature": 0.3, "provider": "anthropic"},
            personality={
                'identity': {'description': 'A precise analyst'},
                'tone_style': {'voice': 'Professional', 'clarity': 'Technical'},
                'core_values': {'accuracy': 'Never wrong', 'stability': 'Proven methods'}
            },
            capability={'skills': ['analysis', 'research']}
        )
    )
    
    # Breed
    engine = BreedingEngine()
    offspring, cert = engine.breed(parent_a, parent_b)
    
    print(f"Offspring: {offspring.name}")
    print(f"Generation: {offspring.generation}")
    print(f"Mutation: {offspring.mutation_flag}")
    print(f"Temperature: {offspring.dna.cognition.get('temperature')}")
    print(f"Skills: {offspring.dna.capability.get('skills')}")
    print("\nBirth Certificate:")
    print(cert.model_dump_json(indent=2))
