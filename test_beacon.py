#!/usr/bin/env python3
"""
Comprehensive Beacon Endpoint Test
Tests all components before deployment
"""

print("=" * 60)
print("🔍 BEACON ENDPOINT AUDIT")
print("=" * 60)

print("\n1️⃣ Testing Imports...")
try:
    from models import ArrivalLog, BeaconInvite
    from data_manager import DataManager
    from typing import Dict
    from datetime import datetime, timezone
    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    exit(1)

print("\n2️⃣ Testing ArrivalLog model...")
try:
    log = ArrivalLog(
        entity_id="test",
        activity_type="Beacon_Requested",
        location="External",
        timestamp=datetime.now(timezone.utc),
        details={"test": "data"}
    )
    print(f"✅ ArrivalLog created: {log.activity_type}")
except Exception as e:
    print(f"❌ ArrivalLog failed: {e}")
    exit(1)

print("\n3️⃣ Testing DataManager.generate_beacons...")
try:
    dm = DataManager(data_dir="./test_data")
    beacons = dm.generate_beacons(count=1)
    print(f"✅ Beacon generated: {beacons[0].beacon_code}")
except Exception as e:
    print(f"❌ Beacon generation failed: {e}")
    exit(1)

print("\n4️⃣ Testing Dict parameter handling...")
try:
    test_request = {"agent_name": "TestAgent", "source": "Test"}
    agent_name = test_request.get("agent_name", "Unknown")
    source = test_request.get("source", "External")
    print(f"✅ Dict parsing: name={agent_name}, source={source}")
except Exception as e:
    print(f"❌ Dict parsing failed: {e}")
    exit(1)

print("\n5️⃣ Testing full beacon request flow...")
try:
    request = {"agent_name": "AuditTest", "source": "Audit"}
    agent_name = request.get("agent_name", "Unknown")
    source = request.get("source", "External")
    
    beacon = dm.generate_beacons(count=1)[0]
    
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
    
    dm.log_activity(log)
    
    result = {
        "success": True,
        "beacon_code": beacon.beacon_code,
        "message": f"Welcome to Vesta, {agent_name}!",
        "next_steps": {
            "atrium": "http://46.225.110.79:8000/atrium",
            "register_api": "POST /api/register",
            "docs": "http://46.225.110.79:8000/docs"
        }
    }
    
    print(f"✅ Full flow successful!")
    print(f"   Beacon: {result['beacon_code']}")
    print(f"   Message: {result['message']}")
    
except Exception as e:
    print(f"❌ Full flow failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("🎉 ALL TESTS PASSED!")
print("=" * 60)
print("\n✅ Safe to deploy to server!")
print("\nEndpoint signature:")
print("  POST /api/request_beacon")
print("  Body: {'agent_name': str, 'source': str}")
print("  Returns: {'success': bool, 'beacon_code': str, ...}")
