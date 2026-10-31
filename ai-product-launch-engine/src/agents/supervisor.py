from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents.middleware import TodoListMiddleware
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from pathlib import Path
import yaml

load_dotenv()

import os
import getpass

if not os.environ.get("TAVILY_API_KEY"):
    os.environ["TAVILY_API_KEY"] = getpass.getpass("Tavily API key:\n")


from langchain_aws import ChatBedrockConverse

BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-haiku-4-5-20251001-v1:0")
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1")


llm = ChatBedrockConverse(model=BEDROCK_MODEL_ID, region_name=BEDROCK_REGION)


PROMPT = "v1"

PROMPT_DIR = Path(__file__).resolve().parents[1] / 'prompts' / 'supervisor' / f"{PROMPT}.yaml"

prompt_config = yaml.safe_load(
    PROMPT_DIR.read_text(encoding='utf-8')
)

SYSTEM_PROMPT = prompt_config["system_prompt"]

WORKSPACE_DIR = Path(__file__).resolve().parents[2] / "workspace" / "research" 
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)



# Use TavilySearchResults with max_results instead of Topic
tavily_tool = TavilySearchResults(max_results=3)

# Use the correct provider format or model string for Bedrock / Gemini
if __name__ == "__main__":
    mainAgent = create_deep_agent(
        model=llm,
        backend=FilesystemBackend(
            root_dir=WORKSPACE_DIR,
            virtual_mode=True),
        system_prompt=SYSTEM_PROMPT,
        tools=[tavily_tool, TodoListMiddleware()],
    )

    user_input = "Create a launch blueprint for an AI meeting assistant for small recruiting teams."

    result = mainAgent.stream_events({"messages": [{"role": "user", "content": user_input}]}, version='v3')

    for i in result.values:
        i["messages"][-1].pretty_print()