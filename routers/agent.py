from fastapi import APIRouter, HTTPException, status
import logging
from schemas import AgentResponse
from agent.agent import agent
import time

# Initialize logging
logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/agent",
    tags=["Agent"]
)



@router.get("/query", response_model=AgentResponse)
async def query_agent(
                      query: str):
    """
    Query the agent with a specific question.
    Uses persistent storage per user session.
    """
    if not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty"
        )
    
    
    start_time = time.time()

    logger.info(f"Invoking agent with query: {query[:50]}...")

    invoke_start = time.time()
    response = await agent.ainvoke(
        {"messages": [("user", query)]},
    )
    invoke_time = time.time() - invoke_start
    logger.info(f"Agent invoke took: {invoke_time:.2f}s")

    end_time = time.time()
    time_needed = round(end_time - start_time, 2)

    if not response.get("messages"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent failed to give an answer. Please try again later."
        )

    # Log all messages to understand the agent's reasoning process
    messages = response.get("messages", [])
    logger.info(f"Agent returned {len(messages)} messages")
    
    for i, message in enumerate(messages):
        # Log message type and role
        message_type = type(message).__name__
        role = getattr(message, 'type', 'unknown') if hasattr(message, 'type') else 'unknown'
        # Get content (full content)
        content = getattr(message, 'content', str(message))
        
        logger.info(f"Message {i+1}/{len(messages)} - Type: {message_type}, Role: {role}")
        if len(content) > 0 and message_type != 'ToolMessage':
            logger.info(f"Content: {content}")
        
        if hasattr(message, 'tool_calls') and message.tool_calls:
            logger.info(f"Tool calls: {[tc.get('name', 'unknown') for tc in message.tool_calls]}")
    


    return AgentResponse(
        content=response["messages"][-1].content,
        role="agent",
        time_needed=time_needed
    )

