from langchain_community.agent_toolkits import SQLDatabaseToolkit
from agent.db import db
from agent.llm import gemini

toolkit = SQLDatabaseToolkit(db=db, llm=gemini)

tools = toolkit.get_tools()

if __name__ == "__main__":
    print("Available tools:")
    for tool in tools:
        print(f"{tool.name}: {tool.description}\n")