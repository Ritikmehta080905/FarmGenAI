"""Unit tests for the simulation scenario runner."""

import unittest

from simulation import scenario_runner


class TestScenarioRunner(unittest.TestCase):

    def test_run_direct_sale_returns_dict(self):
        result = scenario_runner.run_all(scenario_name="direct_sale")
        self.assertIn("scenarios", result)
        self.assertIn("metrics", result)
        self.assertIn("results", result)

    def test_run_all_returns_3_scenarios(self):
        result = scenario_runner.run_all(scenario_name="all")
        self.assertEqual(result["metrics"]["total_scenarios"], 3)

    def test_metrics_keys_present(self):
        result = scenario_runner.run_all(scenario_name="direct_sale")
        m = result["metrics"]
        for key in ("total_scenarios", "success_rate",
                    "average_final_price", "successful_outcomes"):
            self.assertIn(key, m)

    def test_scenario_result_has_required_fields(self):
        result = scenario_runner.run_all(scenario_name="direct_sale")
        rec = result["results"][0]
        for key in ("scenario_type", "status", "summary", "offers"):
            self.assertIn(key, rec)

    def test_run_scenario_result_state_is_valid(self):
        scenario = scenario_runner._SCENARIO_DEFS["direct_sale"]
        result = scenario_runner.run_scenario(scenario)
        valid = {"DEAL", "FAILED", "ESCALATED_STORAGE",
                 "ESCALATED_PROCESSING", "ESCALATED_COMPOST"}
        self.assertIn(result["result"]["state"], valid)

    def test_storage_scenario_runs(self):
        result = scenario_runner.run_all(scenario_name="storage")
        self.assertEqual(len(result["results"]), 1)

    def test_processing_scenario_runs(self):
        result = scenario_runner.run_all(scenario_name="processing")
        self.assertEqual(len(result["results"]), 1)


if __name__ == "__main__":
    unittest.main()
