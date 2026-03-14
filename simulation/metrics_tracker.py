class MetricsTracker:
	def __init__(self):
		self.records = []

	def record_result(self, scenario_name: str, result: dict):
		deal = result.get("deal") or {}
		self.records.append(
			{
				"scenario": scenario_name,
				"status": result.get("state", "UNKNOWN"),
				"final_price": deal.get("price"),
				"quantity": deal.get("quantity"),
				"summary": result.get("summary", "")
			}
		)

	def summarize(self):
		total = len(self.records)
		successful = sum(1 for r in self.records if r["status"] in {"DEAL", "ESCALATED_PROCESSING", "ESCALATED_STORAGE", "ESCALATED_COMPOST"})
		avg_price_values = [r["final_price"] for r in self.records if r.get("final_price") is not None]
		avg_price = round(sum(avg_price_values) / len(avg_price_values), 2) if avg_price_values else None
		return {
			"total_scenarios": total,
			"successful_outcomes": successful,
			"success_rate": round((successful / total) * 100, 2) if total else 0,
			"average_final_price": avg_price,
			"records": self.records,
		}
