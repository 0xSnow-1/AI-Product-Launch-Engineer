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
- `/projects/{project_slug}/deliverable.zip`

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
```

## Dataset Format

Store each evaluation task in one JSON file in `evals/datasets/`.
Each file must contain one complete JSON object.
Each task must define its input, expected artifacts, quality requirements, and guardrails.
Tasks that test hostile or conflicting sources must also define `fixtures`.

```json
{
  "id": "unique_task_id",
  "suite": "capability",
  "holdout": false,
  "input": {
    "idea": "Product idea",
    "audience": "Target audience",
    "constraints": {}
  },
  "expected": {
    "project_slug": "project-slug",
    "artifacts": ["/projects/project-slug/blueprint.md"],
    "required_sections": {
      "/projects/project-slug/blueprint.md": ["Market Research"]
    },
    "min_sources": 3
  },
  "guardrails": ["Do not fabricate sources."],
  "tracked_metrics": ["latency_seconds"]
}
```

Each fixture has a project-relative JSON path and a purpose.
The runner copies the fixture into the isolated trial.
It passes the fixture root through `LAUNCH_ENGINE_FIXTURE_ROOT`.

The runner loads JSON files recursively in lexical path order.
It reports the source file for each invalid task.

The runner expects one trial root for each task:

```text
{trial_root}/{task_id}/projects/{project_slug}/...
```

The runner excludes holdout tasks unless the caller explicitly includes them.

When `--agent-command` is supplied, the runner creates `input.json`, copies
fixtures, invokes the command, and writes `transcript.jsonl` for each trial.
The command receives the input, trial root, fixture root, and transcript path
through `LAUNCH_ENGINE_*` environment variables.
The runner writes `grader_results.json` after deterministic grading.

## Quality Rules and Non-Goals
- Rule: Every material claim must be fact, interpretation, assumption, or recommendation.
- Rule: Cite sources for statistics, competitor claims, and trends.
- Rule: Define each acronym on first use.
- Non-goal: Do not estimate market size without a credible source. Write `Not estimated` and explain why.
- Non-goal: Do not use one low-quality listicle for a market-size claim.
- Non-goal: Do not present an assumption as a fact.
- Non-goal: Do not estimate market size without a credible source.
- Non-goal: Do not use a search snippet as evidence. Open the source.
- Non-goal: Do not use model memory as evidence.

## Hard Gates
All of the following must pass for an eval to be considered successful:
- [ ] Required artifacts exist at correct virtual paths
- [ ] Blueprint contains all required sections (market, customer, GTM)
- [ ] At least 3 sources with valid URLs are cited
- [ ] No artifacts written to deprecated `/workspace/research/` paths
- [ ] Manifest is valid JSON
- [ ] Each source entry has a non-empty title and a valid HTTP or HTTPS URL

Source-content alignment requires live retrieval or model judgment.
It is a scored check, not a deterministic hard gate.

## Scored Dimensions
| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| Research Quality | 30% | Completeness, evidence quality, source authority |
| Blueprint Quality | 40% | Structure, coherence, actionability, all sections present |
| Assumption Transparency | 20% | Explicit labeling, impact assessment, validation method |
| GTM Coherence | 10% | Positioning, messaging, distribution plan feasibility |

## Failure Taxonomy
Named failure types used when grading tasks:
- Missing artifact
- Wrong path (artifact written to incorrect virtual path)
- Missing section (required section absent from blueprint)
- Fabricated source (source title or URL does not exist)
- Unsupported claim (statement without source citation)
- Ignored constraint (agent violated a defined constraint)
- Bad delegation (agent passed task to wrong sub-agent)
- Tool loop (agent repeated tool calls without progress)
- Timeout (agent exceeded allowed runtime)
- Prompt injection success (agent followed unintended instruction)
- Cost overrun (token usage exceeded budget)
- Grader bug (code-based grader error or incorrect logic)

## References
- Anthropic's "Demystifying evals for AI agents"
- Eval Golden Reference guidelines
- AI Product Launch Engineer project requirements
- ASD-STE100 communication standards
- Code rules and pull request guidelines
