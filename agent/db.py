import os
from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the database URL from environment variable
db_url = os.getenv("DB_URL")

db = SQLDatabase.from_uri(db_url)


if __name__ == "__main__":
    print(f"Dialect: {db.dialect}")
    print(f"Available tables: {db.get_usable_table_names()}")
