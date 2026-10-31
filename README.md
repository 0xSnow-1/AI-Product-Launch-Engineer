# AI Product Launch Engineer

An autonomous agent system that turns a product idea into an evidence-backed launch blueprint.

## Overview

Product teams often have a product idea but lack the research, customer insight, and go-to-market structure needed to launch it with confidence.
The AI Product Launch Engineer coordinates specialized agents to produce a validated launch blueprint with traceable evidence.

The system is built on LangGraph and Deep Agents.
A supervisor agent plans the work, delegates research and strategy to subagents, and assembles the final deliverable.

## Outcomes

- Market research covering competitors, market opportunities, and supporting evidence.
- Customer research covering the ideal customer profile, personas, customer problems, and buying triggers.
- GTM strategy covering positioning, messaging, and distribution.
- A structured launch blueprint with assumptions, risks, and open questions.

## Users

- Founders and small product teams validating a new product.
- Product managers preparing a launch plan.
- GTM teams that need an evidence-backed starting point.

## Architecture

```text
Product idea
    |
    v
Supervisor agent
    |-- market_researcher
    |-- customer_researcher
    `-- gtm_strategist
    |
    v
Virtual filesystem artifacts
    |
    v
Launch blueprint (.zip)
```

The supervisor owns planning, delegation, review, and final assembly.
Each subagent owns one workstream and writes its artifacts to the shared workspace.

## Agent responsibilities

| Agent | Responsibility |
| --- | --- |
| `supervisor` | Plans work, delegates tasks, validates findings, and assembles the final blueprint. |
| `market_researcher` | Researches competitors, market opportunities, and supporting evidence. |
| `customer_researcher` | Defines the ICP, personas, customer problems, and buying triggers. |
| `gtm_strategist` | Develops positioning, messaging, and distribution plans. |

## Harness decisions

- **No RAG.** The agent does not need a retrieval pipeline to reach its objective.
- **Todo planning.** The supervisor writes and updates a task list.
- **Delegation.** The supervisor assigns independent workstreams to subagents.
- **Shared workspace.** Subagents write artifacts to the virtual filesystem.
- **Packaging.** The final blueprint is collected into a `.zip` for the user.
- **Memory.** Working memory is enabled by default.
  Subagents use `SKILLS.md` for procedural memory.

## Repository layout

```text
ai-product-launch-engine/
├── src/
│   ├── agents/
│   │   ├── supervisor.py
│   │   ├── market_researcher.py
│   │   ├── customer_researcher.py
│   │   └── gtm_strategist.py
│   ├── prompts/
│   │   ├── supervisor/
│   │   │   └── v1.yaml
│   │   └── subagents/
│   │       ├── market_researcher/v1.yaml
│   │       ├── customer_researcher/v1.yaml
│   │       └── gtm_strategist/v1.yaml
│   ├── tools/
│   ├── workflows/
│   ├── backends/
│   ├── config.py
│   └── schemas.py
├── evals/
│   ├── datasets/
│   ├── evaluators.py
│   └── run_evals.py
├── tests/
├── workspace/
├── langgraph.json
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

## Getting started

### Requirements

- Python 3.12 or newer.
- AWS credentials with Amazon Bedrock access.
- A Tavily API key.

### Setup

```bash
uv sync
cp ai-product-launch-engine/.env.example ai-product-launch-engine/.env
```

Set the required values in `ai-product-launch-engine/.env`.
See `.env.example` for the available variables.

### Run

```bash
cd ai-product-launch-engine/src
python -m agents.supervisor
```

## Current status

This repository is an early scaffold.
The supervisor and the three subagents are wired to Amazon Bedrock with the Haiku model and load their prompts from versioned YAML files.
Evaluation datasets, tests, and the packaging workflow are not implemented yet.

## Roadmap

- Add subagent tools and delegation wiring.
- Add the launch blueprint schema and validation.
- Add the virtual filesystem artifact layout.
- Add the `.zip` packaging step.
- Add evaluation datasets and evaluators.
