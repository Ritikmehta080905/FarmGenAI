import sys
import os

# Ensure project root is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.controllers.simulation_controller import run_simulation_controller


if __name__ == "__main__":

    payload = {"scenario": "direct-sale", "user_id": "test_user"}
    result = run_simulation_controller(payload)

    print("\nFinal Result:")
    print(result)