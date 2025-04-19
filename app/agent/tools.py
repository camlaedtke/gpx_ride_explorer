"""
tools.py
--------
LangChain SQLDatabase toolkit and helpers for the AI-Bike-Coach agent.

Responsibilities:
- Initialize SQLDatabase connection using app settings.
- Provide a SQLDatabaseToolkit instance for use by the chat agent.
- Encapsulate DB tool logic for agent extensibility.

TODO:
- Add more tools (analytics, recommendations, etc.) as agent capabilities expand.
- Add error handling and logging for DB operations.
"""

from langchain.tools import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from app.config import settings
db = SQLDatabase.from_uri(settings.DATABASE_URL)
sql_toolkit = SQLDatabaseToolkit(db=db)