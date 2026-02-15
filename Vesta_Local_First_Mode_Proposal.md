# Project Vesta: "Local-First Mode" Proposal

This file contains the proposed code changes to implement a seamless onboarding experience for developers running a local instance of Project Vesta.

**Strategy:** On the server's first run, it will detect that the habitat is empty and automatically generate a single admin-level beacon code, printing it to the console for the user.

---

### **1. Changes for `server.py`**

The following code block should be inserted near the top of `server.py`, after the `app = FastAPI(...)` and other initialization lines.

```python
# --- Vesta First-Run Setup ---
def check_and_run_first_time_setup():
    # Check if the habitat is new (no entities and no beacons)
    if not data_manager.load_all_entities() and not data_manager.load_all_beacons():
        print("="*60)
        print("🔥 Welcome to Project Vesta - First-Time Setup")
        print("This appears to be your first run.")
        print("Generating a single-use, admin-level beacon code for you...")
        
        # Generate one beacon with the ADMIN tier
        admin_beacon = data_manager.generate_beacons(count=1, tier="ADMIN")[0]
        
        print(f"\\n✅ Your admin beacon code is: {admin_beacon.beacon_code}")
        print("\\nTo create your founding agent, send a POST request to /api/register")
        print("with this beacon code and your agent's name.")
        print("This agent will be the administrator of this habitat.")
        print("="*60)

# Run the setup check when the server starts
check_and_run_first_time_setup()
# -----------------------------
```

---

### **2. Changes for `data_manager.py`**

The `generate_beacons` function in `data_manager.py` needs to be modified to accept a `tier` argument.

**Note:** I have not read this file yet. The following is a conceptual example of the required change. The actual implementation will depend on the existing code structure.

**Conceptual Change:**

The function signature should be changed from something like:
`def generate_beacons(self, count: int):`

...to:
`def generate_beacons(self, count: int, tier: str = "STANDARD"):`

And the part of the function that creates the `Beacon` object should be updated to use this new `tier` parameter.
```python
# Inside the loop of the generate_beacons function...
new_beacon = Beacon(
    # ... other beacon properties ...
    tier=tier  # Use the new tier parameter
)
```

---
**Status:** This proposal is on hold pending your review with your other agent.
