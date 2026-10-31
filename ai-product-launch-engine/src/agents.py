from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents.middleware import TodoListMiddleware
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from pathlib import Path

load_dotenv()

import os
import getpass

if not os.environ.get("TAVILY_API_KEY"):
    os.environ["TAVILY_API_KEY"] = getpass.getpass("Tavily API key:\n")


from langchain_aws import ChatBedrockConverse

BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-haiku-4-5-20251001-v1:0")
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1")


llm = ChatBedrockConverse(model=BEDROCK_MODEL_ID, region_name=BEDROCK_REGION)


WORKSPACE_DIR = Path(__file__).resolve().parents[1] / "workspace" / "research" 
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


gmail_system_prompt = """

You are an Expert Formatter, made to write gmail's ina format that is so concise tailord towards recruiters from a student/candidate's perspective, you are to save results under /home/snowaflic/GTM-autonomous/ai-product-launch-engine/src/workspace/research
"""
# Use TavilySearchResults with max_results instead of Topic
tavily_tool = TavilySearchResults(max_results=3)

# Use the correct provider format or model string for Bedrock / Gemini
mainAgent = create_deep_agent(
    model= llm,
    backend=FilesystemBackend(
        root_dir=WORKSPACE_DIR,
        virtual_mode=True
    ),
    system_prompt=gmail_system_prompt,
)
#tools=[tavily_tool, TodoListMiddleware()],

user_input = "Create a gmail draft for my professor, he's name is Juan and i want this to be about me, a 24 year old no degree wanting to join his engineering team at anthopic"

result = mainAgent.stream_events({"messages": [{"role": "user", "content": user_input}]}, version='v3')

for i in result.values:
    i["messages"][-1].pretty_print()