# AI Product Launch Engineer

Implementation package for the AI Product Launch Engineer.

See the [root README](../README.md) for the project overview, architecture, and setup instructions.

## Agent entry points

- `src/agents/supervisor.py`
- `src/agents/market_researcher.py`
- `src/agents/customer_researcher.py`
- `src/agents/gtm_strategist.py`

## Prompt layout

- `src/prompts/supervisor/v1.yaml`
- `src/prompts/subagents/market_researcher/v1.yaml`
- `src/prompts/subagents/customer_researcher/v1.yaml`
- `src/prompts/subagents/gtm_strategist/v1.yaml`

## Run

```bash
cd src
python -m agents.supervisor
```
