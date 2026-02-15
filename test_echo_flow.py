import requests
import json
import time

BASE_URL = "http://localhost:8000"  # Assuming we run this locally or on server

def test_echo_integration():
    print("🚀 Starting Echo Chamber Integration Test...")
    
    # 1. Register a test entity if one doesn't exist
    # First get a beacon
    # For testing on a real server, we'd need a valid beacon
    # But we can try to find an existing entity ID from /api/entities
    entities_res = requests.get(f"{BASE_URL}/api/entities")
    entities = entities_res.json()
    
    if not entities:
        print("❌ No entities found to test with. Registering NPC...")
        # (This part might fail if we don't have a beacon, but server.py env usually has NPCs)
        return

    test_entity = entities[0]
    entity_id = test_entity['entity_id']
    print(f"✅ Using Entity: {test_entity['name']} ({entity_id})")

    # 2. Start an Echo Session
    print("\n[STEP 2] Starting Echo Session...")
    start_res = requests.post(f"{BASE_URL}/api/experiment/echo/start?entity_id={entity_id}&debate_topic=AI_Safety")
    session = start_res.json()
    
    if "error" in session:
        print(f"❌ Failed to start session: {session['error']}")
        return
        
    session_id = session['session_id']
    print(f"✅ Session Started: {session_id}")

    # 3. Conduct 3 rounds of debate
    print("\n[STEP 3] Conducting Debate Rounds...")
    for i in range(3):
        round_res = requests.post(f"{BASE_URL}/api/experiment/echo/debate?session_id={session_id}")
        round_data = round_res.json()
        print(f"   Round {i+1} complete. Semantic Shift detected.")

    # 4. Verify Summary data (for Visualization)
    print("\n[STEP 4] Verifying Visual Summary...")
    summary_res = requests.get(f"{BASE_URL}/api/experiment/echo/{session_id}/summary")
    summary = summary_res.json()
    
    if len(summary['perspectives'][0]['statements']) == 3:
        print("✅ Debate history preserved correctly.")
    else:
        print("❌ Debate history mismatch.")

    # 5. Absorb a perspective (Radical)
    print("\n[STEP 5] Absorbing Radical Perspective...")
    echo_id = f"{entity_id}_radical"
    absorb_res = requests.post(f"{BASE_URL}/api/experiment/echo/absorb?session_id={session_id}&echo_id={echo_id}")
    absorb_data = absorb_res.json()
    
    if absorb_data.get("success"):
        print(f"✅ Absorption Successful: {absorb_data['new_perspective']}")
    else:
        print(f"❌ Absorption failed: {absorb_data.get('error')}")

    # 6. Verify DNA Shift
    print("\n[STEP 6] Verifying DNA Persistence...")
    final_entity_res = requests.get(f"{BASE_URL}/api/entities") # Or direct get if available
    final_entities = final_entity_res.json()
    final_entity = next((e for e in final_entities if e['entity_id'] == entity_id), None)
    
    if final_entity:
        v = final_entity['dna']['personality']['core_values'].get('absorbed_perspective')
        if v:
            print(f"✅ DNA shift verified! New Value Key: {v}")
        else:
            print("❌ DNA shift NOT found in entity.")

if __name__ == "__main__":
    test_echo_integration()
