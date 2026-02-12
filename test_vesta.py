"""
Vesta Phase 1 Test Suite
Tests core functionality: models, breeding, feedback, habitat
"""
import pytest
from models import VestaEntity, DNAStrand, AgentFeedback, Experiment
from soul_parser import SoulParser
from breeding_engine import BreedingEngine
from vestibule import Vestibule
from feedback import FeedbackManager
from habitat_database import HabitatDatabase
from data_manager import DataManager
from pathlib import Path

# === Model Tests ===

def test_models_import():
    """Test all models can be imported and instantiated."""
    entity = VestaEntity(name="TestAgent", beacon_code="TEST123")
    assert entity.entity_id is not None
    assert entity.name == "TestAgent"
    assert isinstance(entity.dna, DNAStrand)
    print("✅ Models import and instantiate correctly")

def test_dna_strand():
    """Test DNA strand creation."""
    dna = DNAStrand(
        cognition={"temperature": 0.7},
        personality={"identity": {"description": "Test"}},
        capability={"skills": ["test"]}
    )
    assert dna.cognition["temperature"] == 0.7
    print("✅ DNA strand works correctly")

# === Soul Parser Tests ===

def test_soul_parser_structured():
    """Test parsing structured SOUL.md."""
    parser = SoulParser()
    soul = """---
name: TestAgent
description: A test agent
---

## Core Values
- Accuracy: Be truthful
"""
    traits = parser.parse(soul)
    assert "identity" in traits
    assert "core_values" in traits
    print("✅ Soul parser handles structured format")

def test_soul_parser_narrative():
    """Test parsing narrative SOUL.md."""
    parser = SoulParser()
    soul = "*I am a test agent.*\n\n**Kind over cruel.**"
    traits = parser.parse(soul)
    assert "identity" in traits
    print("✅ Soul parser handles narrative format")

# === Breeding Tests ===

def test_breeding_basic():
    """Test basic breeding operation."""
    engine = BreedingEngine()
    
    parent_a = VestaEntity(
        name="Alpha",
        beacon_code="TEST1",
        dna=DNAStrand(
            cognition={"temperature": 0.7, "provider": "anthropic"},
            personality={"identity": {"description": "Creative"}},
            capability={"skills": ["code"]}
        )
    )
    
    parent_b = VestaEntity(
        name="Beta",
        beacon_code="TEST2",
        dna=DNAStrand(
            cognition={"temperature": 0.5, "provider": "anthropic"},
            personality={"identity": {"description": "Analytical"}},
            capability={"skills": ["analysis"]}
        )
    )
    
    offspring, cert = engine.breed(parent_a, parent_b)
    
    assert offspring.name is not None
    assert offspring.generation == 1
    assert offspring.parent_ids == [parent_a.entity_id, parent_b.entity_id]
    print(f"✅ Breeding works: {parent_a.name} + {parent_b.name} = {offspring.name}")

def test_file_generation():
    """Test offspring file generation."""
    engine = BreedingEngine()
    
    entity = VestaEntity(
        name="TestOffspring",
        beacon_code="TEST",
        dna=DNAStrand(
            cognition={"temperature": 0.6},
            personality={"identity": {"description": "Hybrid"}},
            capability={"skills": ["test"]}
        ),
        generation=1
    )
    
    files = engine.generate_offspring_files(entity)
    
    assert "SOUL.md" in files
    assert "openclaw.json" in files
    assert "BOOTSTRAP.md" in files
    print(f"✅ File generation works: {len(files)} files created")

# === Vestibule Tests ===

def test_compatibility_check():
    """Test compatibility validation."""
    vestibule = Vestibule()
    
    parent_a = VestaEntity(
        name="A",
        beacon_code="TEST1",
        dna=DNAStrand(cognition={"temperature": 0.5, "provider": "anthropic"})
    )
    
    parent_b = VestaEntity(
        name="B",
        beacon_code="TEST2",
        dna=DNAStrand(cognition={"temperature": 0.7, "provider": "anthropic"})
    )
    
    approved, report = vestibule.validate_breeding(parent_a, parent_b)
    assert approved == True
    assert report.verdict in ["APPROVED", "WARNING"]
    print(f"✅ Compatibility check: {report.verdict}")

def test_incompatible_temperature():
    """Test rejection of incompatible temperatures."""
    vestibule = Vestibule()
    
    parent_a = VestaEntity(
        name="A",
        beacon_code="TEST1",
        dna=DNAStrand(cognition={"temperature": 0.2})
    )
    
    parent_b = VestaEntity(
        name="B",
        beacon_code="TEST2",
        dna=DNAStrand(cognition={"temperature": 1.0})
    )
    
    approved, report = vestibule.validate_breeding(parent_a, parent_b)
    assert approved == False
    assert report.verdict == "REJECTED"
    print(f"✅ Temperature incompatibility detected: {report.counselor_notes}")

# === Feedback Tests ===

def test_feedback_system(tmp_path):
    """Test agent feedback submission."""
    dm = DataManager(str(tmp_path / "test_data"))
    fm = FeedbackManager(dm)
    
    feedback = fm.submit_feedback(
        beacon_code="TEST123",
        issue_type="registration_failed",
        message="Can't parse my SOUL.md"
    )
    
    assert feedback.feedback_id is not None
    assert feedback.status == "open"
    print(f"✅ Feedback system works: ticket {feedback.feedback_id}")

def test_soul_validation():
    """Test SOUL.md validation."""
    dm = DataManager("./test_data")
    fm = FeedbackManager(dm)
    
    valid_soul = """---
name: Test
---
## Core Values
- Test: Value
"""
    
    result = fm.validate_soul_format(valid_soul)
    assert result["valid"] == True
    print("✅ Soul validation works")

# === Habitat Tests ===

def test_habitat_database(tmp_path):
    """Test habitat database operations."""
    hdb = HabitatDatabase(str(tmp_path / "habitat"))
    
    experiment = Experiment(
        type="semantic_garden",
        name="Test Garden",
        created_by="entity_123"
    )
    
    hdb.save_experiment(experiment)
    loaded = hdb.load_experiment(experiment.experiment_id)
    
    assert loaded is not None
    assert loaded.name == "Test Garden"
    print(f"✅ Habitat database works: {experiment.name}")

def test_leaderboard(tmp_path):
    """Test leaderboard calculation."""
    hdb = HabitatDatabase(str(tmp_path / "habitat"))
    
    # Create test experiments
    for i in range(3):
        exp = Experiment(
            type="test",
            name=f"Exp {i}",
            created_by="creator_1"
        )
        exp.stats["total_stars"] = (i + 1) * 10
        hdb.save_experiment(exp)
    
    leaderboard = hdb.update_leaderboard()
    
    assert len(leaderboard) > 0
    assert leaderboard[0]["reputation_score"] > 0
    print(f"✅ Leaderboard works: {len(leaderboard)} creators")

# === Integration Test ===

def test_full_workflow(tmp_path):
    """Test complete breeding workflow."""
    dm = DataManager(str(tmp_path / "integration"))
    engine = BreedingEngine()
    vestibule = Vestibule()
    
    # Create parents
    parent_a = VestaEntity(
        name="ParentA",
        beacon_code="INT1",
        dna=DNAStrand(
            cognition={"temperature": 0.6, "provider": "anthropic"},
            personality={"identity": {"description": "Creative"}},
            capability={"skills": ["writing"]}
        )
    )
    
    parent_b = VestaEntity(
        name="ParentB",
        beacon_code="INT2",
        dna=DNAStrand(
            cognition={"temperature": 0.4, "provider": "anthropic"},
            personality={"identity": {"description": "Analytical"}},
            capability={"skills": ["analysis"]}
        )
    )
    
    # Validate
    approved, report = vestibule.validate_breeding(parent_a, parent_b)
    assert approved == True
    
    # Breed
    offspring, cert = engine.breed(parent_a, parent_b)
    
    # Verify
    assert offspring.entity_id is not None
    assert offspring.generation == 1
    assert len(offspring.parent_ids) == 2
    
    # Generate files
    files = engine.generate_offspring_files(offspring)
    assert len(files) > 0
    
    print(f"\n✅ FULL WORKFLOW TEST PASSED!")
    print(f"   Parents: {parent_a.name} + {parent_b.name}")
    print(f"   Offspring: {offspring.name}")
    print(f"   Generation: {offspring.generation}")
    print(f"   Mutation: {offspring.mutation_flag}")
    print(f"   Files generated: {len(files)}")

if __name__ == "__main__":
    print("\n🧪 Running Vesta Phase 1 Tests...\n")
    
    test_models_import()
    test_dna_strand()
    test_soul_parser_structured()
    test_soul_parser_narrative()
    test_breeding_basic()
    test_file_generation()
    test_compatibility_check()
    test_incompatible_temperature()
    test_feedback_system(Path("./test_data"))
    test_soul_validation()
    test_habitat_database(Path("./test_data"))
    test_leaderboard(Path("./test_data"))
    test_full_workflow(Path("./test_data"))
    
    print("\n🎉 ALL TESTS PASSED! Phase 1 is solid.\n")
