from pydantic import BaseModel



class AgentResponse(BaseModel):
    """
    Response model for agent queries.
    """
    content: str
    role: str = "agent"
    time_needed: float = 0.0