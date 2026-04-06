from fastapi import APIRouter, HTTPException
from agents.agent_registry import AgentRegistry

router = APIRouter()

@router.get("/")
async def get_agents():
    """Get list of available agents."""
    try:
        registry = AgentRegistry()
        registry.create_agents()
        agents = registry.list_agents()
        return {"agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))