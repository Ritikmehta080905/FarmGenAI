import sys
import os

# Ensure project root is importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.simulation_controller import SimulationController


if __name__ == "__main__":

    controller = SimulationController()

    result = controller.run_simulation("direct_sale")

    print("\nFinal Result:")
    print(result)