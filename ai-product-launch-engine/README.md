# AI Product Launch Engineer

Implementation package for the AI Product Launch Engineer.

See the [root README](../README.md) for the project overview, architecture, and setup instructions.

## Contracts

`src/contracts.py` freezes the data contracts for the MVP: research artifacts,
the GTM strategy, the strategic decision, the launch pack, and the project record.
`src/workflows/validation.py` loads the three specialist JSON artifacts and
validates them against those models.

## MVP plan

The MVP scope, phase order, and per-phase checks live in
[MVP_PLAN/PLAN.md](MVP_PLAN/PLAN.md) and
[MVP_PLAN/verification.md](MVP_PLAN/verification.md).
The MVP specification is [MVP.md](../MVP.md) at the repository root.

## Agent entry points

- `src/agents/supervisor.py`
- `src/agents/market_researcher.py`
- `src/agents/customer_researcher.py`
- `src/agents/gtm_strategist.py`

## Prompt layout

- `src/prompts/supervisor/v4.yaml`
- `src/prompts/subagents/market_researcher/v3.yaml`
- `src/prompts/subagents/customer_researcher/v3.yaml`
- `src/prompts/subagents/gtm_strategist/v3.yaml`

## Run

```bash
uv sync
uv run python main.py --help
```

See `evals/RUNBOOK.md` for eval commands and artifact locations.
