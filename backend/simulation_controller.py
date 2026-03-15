import asyncio
import threading
import time

from backend.websocket_server import start_server
from simulation import scenario_runner


class SimulationController:

    def start_ws(self):

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(start_server())
        except OSError as e:
            if e.errno == 10048 or "10048" in str(e) or "address already in use" in str(e).lower():
                print("[ws] Port 8765 already occupied — skipping WS server start.")
            else:
                raise

    def run_simulation(self, scenario_name):

        try:

            # Start WebSocket server in background thread, give it a moment
            # to bind and subscribe to the event_bus before emitting events.
            ws_thread = threading.Thread(target=self.start_ws, daemon=True)
            ws_thread.start()
            time.sleep(0.5)

            print("[simulation_started] Starting simulation for scenario:", scenario_name)

            results = scenario_runner.run_all(scenario_name=scenario_name)

            print("[simulation_completed] Simulation completed for scenario:", scenario_name)

            return {
                "status": "success",
                "scenario": scenario_name,
                "results": results
            }

        except Exception as e:

            print("[simulation_error] Simulation failed")

            import traceback
            traceback.print_exc()

            return {
                "status": "error",
                "error": str(e)
            }