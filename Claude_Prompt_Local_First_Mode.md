# Prompt for Claude: Implement "Local-First Mode" for Project Vesta

Hello Claude,

We need to implement a critical feature for Project Vesta to improve the onboarding experience for **solo developers running the software locally.**

**Important Context:** This change must be a **non-destructive addition**. The new logic should only activate on a fresh, empty instance of the server (i.e., when no entities or beacons exist). It must **not** interfere with the existing operator-led workflow for a live, populated server, like the one we plan to run for Moltbook agents. The goal is to make the software flexible for both use cases.

**The Problem:**
The current user onboarding is designed for a managed service where an operator generates and distributes beacon codes. This creates a high-friction experience for our new target audience: solo developers who clone the repository and expect to run it immediately. They currently have no way to create their first agent without manually calling an admin API endpoint.

**The Solution: "Local-First Mode"**
We will implement a "local-first mode" that automatically handles setup on the server's first run.

**Implementation Details:**

You will need to modify two files: `server.py` and `data_manager.py`.

**1. Modify `server.py`:**
At the top of `server.py`, after the initial imports and application setup (e.g., after `app = FastAPI(...)`), insert the following code block. This function will check if the habitat is empty and, if so, generate and print a single admin beacon code to the console.

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

**2. Modify `data_manager.py`:**
The `generate_beacons` function needs to be updated to accept a `tier` parameter.

*   Change the function signature from `def generate_beacons(self, count: int):` to `def generate_beacons(self, count: int, tier: str = "STANDARD"):`
*   Inside the function, when creating the `Beacon` object, ensure you pass the new `tier` variable to its `tier` attribute.

**Your Task:**
Please provide the complete, updated code for both `server.py` and `data_manager.py` with these changes implemented.
