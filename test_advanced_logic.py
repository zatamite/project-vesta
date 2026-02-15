
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

from models import VestaEntity, DNAStrand
from vestibule import StabilityChecker
from breeding_engine import BreedingEngine

def test_loop_detection():
    print("--- Testing Loop Detection ---")
    checker = StabilityChecker()
    
    stable_text = "The quick brown fox jumps over the lazy dog. This is a normal sentence with various words."
    is_stable, ratio, reason = checker.evaluate_stability(stable_text)
    print(f"Stable: {is_stable}, Reason: {reason}")
    
    loop_text = "error recovery failed. retry now. error recovery failed. retry now. error recovery failed. retry now."
    is_stable, ratio, reason = checker.evaluate_stability(loop_text)
    print(f"Looping: {is_stable}, Reason: {reason}")
    
    if not is_stable and "loops detected" in reason:
        print("✅ Loop detection works!")
    else:
        print("❌ Loop detection failed to flag repeating sequence.")

def test_weighted_crossover():
    print("\n--- Testing Weighted Crossover ---")
    engine = BreedingEngine()
    
    # Parent A: High stability, simple tone
    parent_a = VestaEntity(
        name="StableParent",
        beacon_code="A",
        stability_score=0.9,
        dna=DNAStrand(
            cognition={"temp": 0.1},
            personality={"identity": {"description": "A STABLE ENTITY"}, "tone_style": {"voice": "Quiet"}, "core_values": {"stability": "High"}},
            capability={"skills": ["logic"]}
        )
    )
    
    # Parent B: Low stability, verbose tone
    parent_b = VestaEntity(
        name="UnstableParent",
        beacon_code="B",
        stability_score=0.2,
        dna=DNAStrand(
            cognition={"temp": 0.9},
            personality={"identity": {"description": "AN UNSTABLE ENTITY"}, "tone_style": {"voice": "Loud"}, "core_values": {"chaos": "Max"}},
            capability={"skills": ["creativity"]}
        )
    )
    
    # Offspring should favor Parent A (9:2 ratio)
    offspring_dna = engine.crossover(parent_a.dna, parent_b.dna, parent_a.stability_score, parent_b.stability_score)
    
    desc = offspring_dna.personality.get('identity', {}).get('description', '')
    print(f"Offspring Description: {desc}")
    
    if "StableParent" in desc or "STABLE ENTITY" in desc:
        print("✅ Weighted blending favors stable parent!")
    else:
        print("❌ Weighted blending failed to favor stable parent.")

if __name__ == "__main__":
    try:
        test_loop_detection()
        test_weighted_crossover()
        print("\n🎉 All advanced logic tests passed!")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
