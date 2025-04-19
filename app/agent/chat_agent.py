"""
chat_agent.py
-------------
LangChain-powered chat agent for the AI-Bike-Coach platform.

Responsibilities:
- Initialize a LangChain agent with SQLDatabase tools and OpenAI LLM.
- Provide an answer(query) function for natural language queries over the database.
- Used by the Streamlit Chat UI and potentially other interfaces.

TODO:
- Add user/session context to queries for personalized answers.
- Improve error handling and logging.
- Support more advanced agent tools (analytics, recommendations, etc.).
"""

from langchain.agents import initialize_agent
from langchain.chat_models import ChatOpenAI
from .tools import sql_toolkit

llm = ChatOpenAI(model="gpt-4o", temperature=0)
agent = initialize_agent(
    tools=sql_toolkit.get_tools(),
    llm=llm,
    agent_type="openai-tools",
    verbose=True,
)

def answer(query:str)->str:
    return agent.run(query)