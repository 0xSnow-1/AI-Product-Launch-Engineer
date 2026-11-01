# AI Product Launch Engineer Evaluation Contract

## Project Overview
An autonomous agent system that turns a product idea into an evidence-backed launch blueprint. The system coordinates specialized agents to produce a validated launch blueprint with traceable evidence.

## Input Schema
```yaml
idea: string  # Product idea description (max 500 chars)
audience: string  # Target audience description (max 200 chars)
constraints: object  # Optional project constraints
  - budget: string  # "low", "medium", "high"
  - geography: string  # Geographic scope
  - timeline: string  # Optional timeline constraints
```

## Output Schema
The system produces a structured launch blueprint with the following artifacts:

### Required Files
- `/projects/{project_slug}/research/market.md`
- `/projects/{project_slug}/research/customers.md`
- `/projects/{project_slug}/strategy/gtm.md`
- `/projects/{project_slug}/blueprint.md`
- `/projects/{project_slug}/manifest.json`

### Blueprint.md Structure
```yaml
sections:
  - market_research:
      - competitor_landscape
      - market_opportunities
      - trends_and_insights
  - customer_research:
      - ideal_customer_profile
      - personas
      - customer_problems
      - buying_triggers
  - gtm_strategy:
      - positioning_statement
      - value_proposition
      - messaging_by_channel
      - distribution_plan
      - launch_sequence
      - launch_goals
      - risks_and_assumptions
```

### Manifest.json Structure
```yaml
metadata:
  project_slug: string
  created_at: timestamp
  version: string
artifacts:
  - market.md
  - customers.md
  - gtm.md
  - blueprint.md
execution:
  agents_used: ["market_researcher", "customer_researcher", "gtm_strategist", "supervisor"]
  total_turns: number
  total_tool_calls: number
  total_tokens: number
```

## Artifact Paths
**Virtual Filesystem Scheme:**
- Physical root: `ai-product-launch-engine/workspace`
- Virtual root: `/`
- Project root: `/projects/{project_slug}/`

**Required artifacts:**
```
/projects/{project_slug}/
├── research/
│   ├── market.md
│   └── customers.md
├── strategy/
│   └── gtm.md
├── blueprint.md
├── manifest.json
└── deliverable.zip
## References

- Anthropic's "Demystifying evals for AI agents"
- Eval Golden Reference guidelines
- AI Product Launch Engineer project requirements
- ASD-STE100 communication standards
- Code rules and pull request guidelines
```