"""Market research subagent.

Researches competitors, market opportunities, and supporting evidence.
"""

from pathlib import Path

import yaml
from dotenv import load_dotenv
from langchain_aws import ChatBedrockConverse
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

load_dotenv()

import os

PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts" / "subagents" / "market_researcher" / "v1.yaml"

SYSTEM_PROMPT = yaml.safe_load(PROMPT_DIR.read_text(encoding="utf-8"))["system_prompt"]

BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-haiku-4-5-20251001-v1:0")
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1")

llm = ChatBedrockConverse(model=BEDROCK_MODEL_ID, region_name=BEDROCK_REGION)

WORKSPACE_DIR = Path(__file__).resolve().parents[2] / "workspace" / "research"
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

market_researcher_agent = create_deep_agent(
    model=llm,
    backend=FilesystemBackend(
        root_dir=WORKSPACE_DIR,
        virtual_mode=True,
    ),
    system_prompt=SYSTEM_PROMPT,
)
