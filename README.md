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
│   │   ├── gtm_strategist.py
│   │   ├── common.py
│   │   └── tools.py
│   ├── prompts/
│   │   ├── supervisor/         (versioned YAML: v1-v3)
│   │   └── subagents/          (versioned YAML per agent)
│   ├── tools/
│   ├── workflows/
│   ├── backends/
│   ├── config.py
│   ├── contracts.py
│   ├── metrics.py
│   ├── schemas.py
│   ├── transcript.py
│   └── versions.py
├── evals/
│   ├── datasets/               (capability and holdout tasks)
│   ├── reference/              (reference trial)
│   ├── evaluators.py
│   └── run_evals.py
├── tests/
├── workspace/
├── MVP_PLAN/
├── langgraph.json
├── pyproject.toml
├── .env.example
└── README.md
```

## Getting started

### Requirements

- Python 3.12.
- AWS credentials with Amazon Bedrock access.
- A Tavily API key.

### Setup

```bash
cd ai-product-launch-engine
uv sync
cp .env.example .env
```

Set the required values in `ai-product-launch-engine/.env`.
See `ai-product-launch-engine/.env.example` for the available variables.

### Run

```bash
cd ai-product-launch-engine
uv run python main.py --input <path-to-request.json>
```

The CLI reads a launch request JSON file (idea, audience, constraints), runs the
supervisor and its three subagents, and writes a launch blueprint zip to the
workspace. There is no Slack interface yet.

## Current status

The command-line launch engine works end to end.
The supervisor plans with `TodoListMiddleware`, delegates to `market_researcher`,
`customer_researcher`, and `gtm_strategist`.
Each specialist writes one validated JSON artifact: `research/market_research.json`,
`research/customer_research.json`, and `strategy/gtm_strategy.json`.
The CLI validates the three artifacts against `src/contracts.py` before it builds
the blueprint, the manifest, and the zip.
The eval harness runs 20 tasks against 9 deterministic graders with schema checks
for the JSON artifacts.
The unit suite passes and CI runs the tests and task validation on every pull request.

The MVP scope, plan, and per-phase checks live in [MVP.md](MVP.md) and
[ai-product-launch-engine/MVP_PLAN/PLAN.md](ai-product-launch-engine/MVP_PLAN/PLAN.md).
Per-phase verification commands are in
[MVP_PLAN/verification.md](ai-product-launch-engine/MVP_PLAN/verification.md).
The MVP data contracts are frozen in
[ai-product-launch-engine/src/contracts.py](ai-product-launch-engine/src/contracts.py).
They are wired into the specialist output path.
Slack delivery, the async research workflow, and persistence are planned future
phases.

## Roadmap

The phase order is defined in
[ai-product-launch-engine/MVP_PLAN/PLAN.md](ai-product-launch-engine/MVP_PLAN/PLAN.md).
Phase 0 freezes the data contracts.
Phase 1 adds structured JSON artifacts. Phases 2 to 6 add the async research workflow, the
decision step and GTM guard, Slack integration, persistence, and deployment.
The Design Agent is deferred to a later plan.
