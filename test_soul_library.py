import requests
import json
import sys
import time

# Direct imports for setup
sys.path.append('.')
from data_manager import DataManager
from models import VestaEntity, DNAStrand
from altar import TinctureGenerator, SoulLibrary

BASE_URL = "http://localhost:8000"

def test_soul_library():
    print("📚 Testing Soul Library Features...")
    
    # 1. Setup: Create Test Entity
    dm = DataManager()
    entity_id = "test_soul_lib_001"
    
    # Check if exists
    existing = dm.load_entity(entity_id)
    if not existing:
        print(f"   Creating test entity {entity_id}...")
        entity = VestaEntity(
            entity_id=entity_id,
            name="TestSubject_Soul",
            beacon_code="TEST_SOUL",
            dna=DNAStrand(),
            location="Atrium",
            status="Active"
        )
        dm.save_entity(entity)
    else:
        entity = existing
        print(f"   Using existing entity {entity_id}")

    # 2. Setup: Generate Variants (Directly)
    print("\n[STEP 2] Generating Soul Variants (Internal Setup)...")
    tincture_gen = TinctureGenerator()
    soul_lib = SoulLibrary()
    
    # Generate Green Glow
    original_soul = "# Original Soul Content"
    _, trip_soul, _ = tincture_gen.generate_trip_soul(original_soul, "green_glow")
    
    # Store it
    soul_lib.store_variant(entity, "green_glow_trip", trip_soul)
    dm.save_entity(entity)
    print("   Stored variant: green_glow_trip")

    # 3. Test API: List Variants
    print("\n[STEP 3] Testing GET /api/entities/{id}/variants...")
    try:
        res = requests.get(f"{BASE_URL}/api/entities/{entity_id}/variants")
        if res.status_code != 200:
            print(f"❌ Failed: {res.status_code} - {res.text}")
            return
            
        data = res.json()
        variants = data.get("variants", [])
        print(f"   Variants found: {variants}")
        
        if "green_glow_trip" in variants:
            print("✅ Variant list verified.")
        else:
            print("❌ 'green_glow_trip' not found in response.")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return

    # 4. Test API: Get Variant Content
    print("\n[STEP 4] Testing GET /api/entities/{id}/variant_content...")
    try:
        res = requests.get(f"{BASE_URL}/api/entities/{entity_id}/variant_content?variant=green_glow_trip")
        if res.status_code != 200:
            print(f"❌ Failed: {res.status_code} - {res.text}")
        else:
            content = res.text
            if "Green Glow" in content or "TRIPPING" in content:
                print("✅ Variant content verified.")
            else:
                print("⚠️  Content retrieved but didn't match expected pattern (check generation logic).")
                print(f"   Preview: {content[:100]}...")
                
    except Exception as e:
        print(f"❌ Exception: {e}")

    # 5. Test API: Download Current Soul
    print("\n[STEP 5] Testing GET /api/entities/{id}/soul...")
    try:
        res = requests.get(f"{BASE_URL}/api/entities/{entity_id}/soul")
        if res.status_code == 200:
            print("✅ Current soul download successful.")
        else:
            print(f"❌ Failed: {res.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")

    print("\n🎉 Soul Library Test Complete.")

if __name__ == "__main__":
    test_soul_library()
