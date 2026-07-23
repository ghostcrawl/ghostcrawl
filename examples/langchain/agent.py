"""Give GhostCrawl tools to a LangChain agent.

    pip install ghostcrawl-langchain langchain langchain-openai
    export GHOSTCRAWL_API_KEY=YOUR_API_KEY
    export OPENAI_API_KEY=sk-...
    python agent.py

GhostCrawl tools are standard LangChain BaseTool instances, so they drop into
any LangChain agent. This example wires scrape + search + extract into a
tool-calling agent.
"""

from ghostcrawl_langchain import (
    GhostcrawlExtractTool,
    GhostcrawlScrapeTool,
    GhostcrawlSearchTool,
)
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

tools = [
    GhostcrawlScrapeTool(),
    GhostcrawlSearchTool(),
    GhostcrawlExtractTool(),
]

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a research assistant. Use the GhostCrawl tools to fetch live web data."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

result = executor.invoke({"input": "Summarize the homepage at https://example.com"})
print(result["output"])
