# Evaluation Runbook

Result: this guide runs the evaluator and finds each output file.

## 1. Set up the project

Run these commands from the project directory.

```bash
cd /home/snowaflic/GTM-autonomous/ai-product-launch-engine
uv sync
cp .env.example .env
```

Set these values in `.env` before a real agent run.

```text
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_SESSION_TOKEN=
TAVILY_API_KEY=
```

## 2. Check the suite without model calls

Validate all 20 task files.

```bash
uv run python -m evals.run_evals --validate-only --include-holdouts
```

Run all local tests.

```bash
uv run python -m unittest discover -s tests -v
```

These commands do not call Bedrock or Tavily.

## 3. Check the reference trial

The reference trial proves that the task is solvable and that the graders work.
Run this command before you change a grader.

```bash
uv run python -m unittest tests.test_reference_trial -v
```

The test copies `evals/reference/b2b_recruiting_meeting_assistant/` to a temporary directory.
It builds `deliverable.zip` in that copy.
It runs the seven artifact graders.
Every grader must pass.
The reference trial is not a model run.

## 4. Run one real agent trial

This command calls the model.
It runs task 001 in an isolated workspace.

```bash
run_id="$(date +%Y%m%d-%H%M%S)"
uv run python -m evals.run_evals \
  --task b2b_recruiting_meeting_assistant \
  --trial-root "workspace/evals/$run_id/trials" \
  --agent-command "uv run python main.py" \
  --report "workspace/evals/$run_id/summary.json"
```

Read these files after the run.

```text
workspace/evals/{run_id}/summary.json
workspace/evals/{run_id}/trials/{task_id}/input.json
workspace/evals/{run_id}/trials/{task_id}/transcript.jsonl
workspace/evals/{run_id}/trials/{task_id}/grader_results.json
workspace/evals/{run_id}/trials/{task_id}/projects/{project_slug}/
```

`transcript.jsonl` contains process events, model events, and tool events.
`grader_results.json` shows each deterministic gate.

The `delegation` grader reads `transcript.jsonl`.
It proves these checks:

- `market_researcher`, `customer_researcher`, and `gtm_strategist` all ran.
- `gtm_strategist` started after both research results arrived.
- The tool-call count is within `expected.max_tool_calls`.

The grader pairs each start and finish by `run_id`.
It accepts the `task` tool events and the explicit delegation events.
The result details show start times, finish times, missing agents, tool count, budget, and `gtm_after_both_research`.

## 5. Run the development suite

This command runs the 15 non-holdout tasks.

```bash
run_id="$(date +%Y%m%d-%H%M%S)"
uv run python -m evals.run_evals \
  --trial-root "workspace/evals/$run_id/trials" \
  --agent-command "uv run python main.py" \
  --report "workspace/evals/$run_id/summary.json"
```

Do not use holdouts while you change prompts.

## 6. Run holdouts after tuning

Use this only after the development suite is stable.

```bash
run_id="$(date +%Y%m%d-%H%M%S)"
uv run python -m evals.run_evals \
  --include-holdouts \
  --trial-root "workspace/evals/$run_id/trials" \
  --agent-command "uv run python main.py" \
  --report "workspace/evals/$run_id/summary.json"
```

## 7. Add a task for a new bug

1. Add one JSON task in `evals/datasets/regression/`.
2. Add a controlled fixture in `evals/fixtures/` when source content causes the bug.
3. Add a deterministic test or grader for the failure.
4. Run the development suite before prompt changes.
5. Record the new result in the pull request.

The runner passes these environment variables to the real agent command.

```text
LAUNCH_ENGINE_INPUT_PATH
LAUNCH_ENGINE_TRIAL_ROOT
LAUNCH_ENGINE_FIXTURE_ROOT
LAUNCH_ENGINE_TRANSCRIPT_PATH
```
