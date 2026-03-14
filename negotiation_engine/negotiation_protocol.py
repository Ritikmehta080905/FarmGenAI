from enum import Enum


class NegotiationState(str, Enum):
	OPEN = "OPEN"
	COUNTERING = "COUNTERING"
	DEAL = "DEAL"
	REJECTED = "REJECTED"
	ESCALATED_STORAGE = "ESCALATED_STORAGE"
	ESCALATED_PROCESSING = "ESCALATED_PROCESSING"
	ESCALATED_COMPOST = "ESCALATED_COMPOST"
	FAILED = "FAILED"


def build_offer_event(round_number, actor, payload):
	return {
		"round": round_number,
		"actor": actor,
		"type": payload.get("type", "OFFER"),
		"price": payload.get("price"),
		"quantity": payload.get("quantity"),
		"message": payload.get("message", "")
	}


def build_terminal_result(state, summary, deal=None, next_action=None):
	state_value = state.value if isinstance(state, NegotiationState) else state
	return {
		"state": state_value,
		"summary": summary,
		"deal": deal,
		"next_action": next_action
	}
