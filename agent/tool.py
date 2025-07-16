from langchain_community.agent_toolkits import SQLDatabaseToolkit
from agent.db import db
from agent.llm import gemini
from langchain_core.tools import tool
from datetime import datetime, timezone

toolkit = SQLDatabaseToolkit(db=db, llm=gemini)


@tool
def get_current_date_info() -> dict:
    """
    Get the current date information including date, month name, and year.

    Returns:
        dict: Dictionary containing current date, month name, and year
    """
    now = datetime.now(timezone.utc)
    return {
        "date": now.strftime('%Y-%m-%d'),
        "month": now.strftime('%B'),
        "year": now.year,
        "day": now.day,
        "month_number": now.month
    }

tools = toolkit.get_tools() + [get_current_date_info]


if __name__ == "__main__":
    print("Available tools:")
    for tool in tools:
        print(f"{tool.name}: {tool.description}\n")