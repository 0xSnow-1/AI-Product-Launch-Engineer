"""Shared tools for launch agents."""

from __future__ import annotations

from dotenv import load_dotenv
from langchain_tavily import TavilySearch


load_dotenv()

search_tool = TavilySearch(max_results=5)
