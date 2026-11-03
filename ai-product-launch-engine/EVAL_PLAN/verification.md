# Verification

This file defines how to prove that each phase in `EVAL_PLAN/PLAN.md` is correct and done.
Run the checks for one phase before you start the next phase.
Attach the command output to the phase pull request.

## How to use this file

1. Read the matching phase in `PLAN.md`.
2. Run every command in the phase section from `ai-product-launch-engine/`.
3. Compare the output to the expected result.
4. Save the evidence listed in the phase section.
5. Stop when any fail condition is true.

## Common checks

Run these from `/home/snowaflic/GTM-autonomous/ai-product-launch-engine`.

```bash
uv run python -m unittest discover -s tests -v
git diff --check
```

Expected result:

- All tests pass.
- `git diff --check` prints nothing.

Fail conditions:

- A test fails.
- A test is skipped without a written reason.
- The change adds a secret or a generated artifact to git.

## Phase 0: Contract and reference trial

### Preconditions

- The artifact graders are unchanged.
- Task `b2b_recruiting_meeting_assistant` loads.

### Commands

```bash
uv run python -m unittest tests.test_reference_trial -v
uv run python -m evals.run_evals --validate-only --task b2b_recruiting_meeting_assistant
git diff --check
```

### Expected result

- `tests.test_reference_trial` passes.
- Every artifact grader passes on the reference trial.
- The validate command prints `"valid": true`.
- The task count is `1`.
- The task ID is `b2b_recruiting_meeting_assistant`.

### Evidence to save

- The test output.
- The full reference grader result.
- The path to the reference trial.
- The updated contract section.

### Manual checks

- Open `evals/reference/b2b_recruiting_meeting_assistant/`.
- Confirm `market.md` has `Competitor Landscape`, `Market Opportunities`, `Trends and Insights`, and `Sources`.
- Confirm `customers.md` has the five required headings.
- Confirm `gtm.md` has the seven required headings.
- Confirm `blueprint.md` has the four required headings.
- Confirm `market.md` has at least three `- [Title](URL)` source lines.
- Confirm `manifest.json` is valid JSON and names the four agents.
- Confirm the manifest artifact list names the five non-archive files, including `manifest.json`.
- Confirm no zip file is committed.
- Confirm no file uses `/workspace/research/`.

### Fail conditions

- Any artifact grader fails on the reference trial.
- The reference trial has a placeholder such as `TODO` or `[citation needed]`.
- The contract says something that the task file or the graders do not do.
- A binary zip is committed.

## Phase 1: Delegation order and GTM dependency grader

### Preconditions

- Phase 0 is verified.
- `evals/fixtures/transcripts/` contains the eight fixtures listed in `PLAN.md`.
- `src/transcript.py` records `run_id` and `parent_run_id`.

### Commands

```bash
uv run python -m unittest tests.test_delegation_grader -v
uv run python -m unittest discover -s tests -v
uv run python -m evals.run_evals --validate-only --task b2b_recruiting_meeting_assistant
```

### Expected result

The test for `pass_parallel.jsonl` reports:

- `passed: true`.
- `delegated_subagents` contains `market_researcher`, `customer_researcher`, and `gtm_strategist`.
- `missing_subagents` is empty.
- `gtm_after_both_research` is `true`.
- `tool_call_count` is less than or equal to `max_tool_calls`.

The test for `pass_sequential.jsonl` reports:

- `passed: true`.
- `gtm_after_both_research` is `true`.

The test for `gtm_before_customer_result.jsonl` reports:

- `passed: false`.
- `gtm_after_both_research` is `false`.
- The detail names the missing customer result.

The test for `gtm_before_both_results.jsonl` reports:

- `passed: false`.
- `gtm_after_both_research` is `false`.

The test for `missing_customer_result.jsonl` reports:

- `passed: false`.
- The detail names the missing customer finish event.

The test for `missing_run_id.jsonl` reports:

- `passed: false`.
- The detail names the missing `run_id` and the dependency cannot be proven.

The test for `tool_loop.jsonl` reports:

- `passed: false`.
- `tool_call_count` is greater than `max_tool_calls`.

The test for `malformed.jsonl` reports:

- `passed: false`.
- The detail names the malformed line.
- The test does not raise an exception.

### Evidence to save

- The test output.
- The fixture paths.
- One full JSON result for a pass fixture and one for each failure class.
- One transcript line that shows a `task` start and finish with the same `run_id`.

### Manual checks

- `DelegationGrader` is in `DEFAULT_GRADERS`.
- The hard gates in `evals/spec.md` name the three subagents, the GTM dependency, and the tool budget.
- The task file for `b2b_recruiting_meeting_assistant` has `required_subagents` and `max_tool_calls`.
- The grader does not require the two research agents to run in a fixed order.
- The grader does not require an exact tool-call sequence.
- The grader uses timestamps and task results, not list order alone, for the GTM dependency check.
- The grader pairs each task start and finish by `run_id`.
- The research write events are supporting detail, not the primary gate.
- The grader accepts both the `task` tool event shape and the explicit delegation event shape.
- The grader does not depend on live model calls or network access.

### Fail conditions

- A missing subagent still passes.
- GTM starts after the market result but before the customer result and still passes.
- GTM starts before both results and still passes.
- A tool loop still passes.
- A malformed transcript crashes the runner.
- A missing `run_id` still passes.
- The grader requires one exact delegation order for all three agents.
- The grader depends on file write order as the primary dependency proof.
- The grader depends on live model calls or network access.

## Phase 2: HTML results viewer

### Preconditions

- Phase 1 is verified.
- A passing fixture run and a failing fixture run exist for the report tests.
- The report tests use a temporary directory for output.

### Commands

```bash
uv run python -m unittest tests.test_report_html -v
uv run python -m unittest discover -s tests -v
uv run python -m evals.report_html --run <fixture_run>
```

Then generate a report through the runner.

```bash
uv run python -m evals.run_evals \
  --task b2b_recruiting_meeting_assistant \
  --runs-root <fixture_runs_root> \
  --run-id <fixture_run_id> \
  --html
```

### Expected result

- `tests.test_report_html` passes.
- `report.html` exists at the default path and at the `--output` path.
- The runner prints the report path.
- The report shows the overall status.
- The report shows these KPI cards: pass rate, failed tasks, total tool calls, total tokens, latency, and GTM dependency status.
- The report shows a task table with per-task status and per-grader status.
- The report shows the delegation timeline for the market, customer, and GTM agents.
- The report shows a GTM-after-both-research badge that matches the `delegation` grader.
- The report renders a single-task run and a multi-task run.
- The report renders a clear empty state when a file is missing.
- The report escapes raw HTML in an artifact.
- The report has no external asset reference.
- The report opens offline.

### Evidence to save

- The test output.
- The report path for a passing run.
- The report path for a failing run.
- A screenshot or a text summary of the KPI cards, task table, and delegation timeline.

### Manual checks

- Open `report.html` with the network disabled.
- Confirm the layout works at 375 pixels and at 1280 pixels.
- Confirm no horizontal scroll on the task table at 375 pixels.
- Confirm status uses text and color, not color alone.
- Confirm the tabs work with the keyboard.
- Confirm the print layout shows the status and the task table.
- Confirm the raw JSON and transcript links point to the correct files.
- Confirm the report does not start a server.
- Confirm the report contains no CDN, external font, external image, or external script.
- Confirm the report data matches `summary.json` and `grader_results.json`.
- Confirm the GTM badge matches the `delegation` grader result.

### Fail conditions

- The report loads an external asset.
- The report crashes on a missing file.
- Raw HTML in an artifact executes as markup or script.
- The report status does not match the JSON result.
- The report omits the GTM dependency badge.
- The report only supports a single task or only supports a suite.
- The report needs a network connection or a server.
- The report exposes a secret or a full environment value.

## Phase 3: Trial completion

### Preconditions

- Phase 0, Phase 1, and Phase 2 are verified.
- The tests use a temporary workspace root.

### Commands

```bash
uv run python -m unittest tests.test_executor tests.test_blueprint tests.test_packaging -v
uv run python -m unittest discover -s tests -v
```

### Expected result

- The executor test finds `project_slug` in `input.json`.
- The executor test finds the expected value `b2b-recruiting-meeting-assistant`.
- The blueprint test finds `blueprint.md` under the temporary workspace root.
- The blueprint test does not find a write under host `/projects`.
- The packaging test finds a valid `manifest.json`.
- The packaging test finds a valid `deliverable.zip`.
- The zip contains `research/market.md`, `research/customers.md`, `strategy/gtm.md`, `blueprint.md`, and `manifest.json`.
- The manifest contains all four agents.
- The manifest contains non-negative integers for turns, tool calls, and tokens.
- The manifest artifact list names the five non-archive files, including `manifest.json`.

### Evidence to save

- The test output.
- The temporary artifact tree.
- The manifest JSON.
- The zip entry list.
- The executor `input.json`.

### Manual checks

- Run `rg -n 'Path\(f"/projects' src main.py` and confirm there are no matches.
- Confirm `create_blueprint` accepts a workspace root.
- Confirm `main.py` passes the workspace root.
- Confirm a blueprint failure returns a non-zero process code.
- Confirm `src/metrics.py` returns zeros when the transcript is absent.
- Confirm `src/packaging.py` does not write outside the project root.

### Fail conditions

- The blueprint writes to host `/projects`.
- The manifest is missing or invalid.
- The zip is missing or does not contain the required entries.
- The input file lacks the expected slug.
- A blueprint failure is swallowed and the process still returns zero.
- A file is written outside the trial root.

## Phase 4: First real baseline

### Preconditions

- Phase 0, Phase 1, Phase 2, and Phase 3 are verified.
- `.env` has the required provider keys.
- No prompt file changed since the last commit.
- The working tree is clean except for `workspace/` output.

### Commands

Run two trials with different run IDs.
The runner prints each run directory.

```bash
uv run python -m evals.run_evals \
  --task b2b_recruiting_meeting_assistant \
  --run-id "$(date +%Y%m%d-%H%M%S)-a" \
  --agent-command "uv run python main.py" \
  --html

uv run python -m evals.run_evals \
  --task b2b_recruiting_meeting_assistant \
  --run-id "$(date +%Y%m%d-%H%M%S)-b" \
  --agent-command "uv run python main.py" \
  --html
```

Then inspect each run under `evals/runs/`.

```bash
find evals/runs -maxdepth 8 -type f | sort
```

A red baseline may make `evals.run_evals` exit with code `1`.
That is expected when a hard gate fails.
Do not treat the nonzero exit as a crash.
Inspect `summary.json` and `grader_results.json` for the real result.

### Expected result

Each run directory contains:

- `summary.json`.
- `report.html`.
- `trials/b2b_recruiting_meeting_assistant/input.json`.
- `trials/b2b_recruiting_meeting_assistant/transcript.jsonl`.
- `trials/b2b_recruiting_meeting_assistant/grader_results.json`.
- `trials/b2b_recruiting_meeting_assistant/projects/b2b-recruiting-meeting-assistant/`.

Each `grader_results.json` contains the `delegation` grader.
Each `transcript.jsonl` contains task events for all three subagents.
Each task start and finish pair has the same `run_id`.
The baseline record names both run IDs and the commit SHA.
The baseline record reports pass@1 and pass^2.
The baseline record reports per-grader results, not only an average.
The baseline record reports the GTM dependency result.
The baseline record names both `report.html` paths.
Every failure has a failure class from `evals/spec.md`.

### Evidence to save

- Both run IDs.
- Both `summary.json` files.
- Both `grader_results.json` files.
- Both `report.html` files.
- The baseline record path.
- The commit SHA.
- The model ID and region.
- The supervisor prompt version and the three subagent prompt versions.
- The worst failure class.
- The latency and tool count from each transcript.

### Manual checks

- Confirm no holdout task ran.
- Confirm no prompt file changed between the two runs.
- Confirm the baseline record exists before any tuning.
- Confirm the record includes both runs.
- Confirm the record includes the commit SHA and model ID.
- Confirm the record includes cost when the transcript has token data.
- Confirm each report matches its JSON result.
- Confirm the GTM badge matches the `delegation` grader.

### Fail conditions

- Only one run exists.
- A run has no transcript.
- A run has no `grader_results.json`.
- A run has no `report.html`.
- The baseline record is missing.
- The record reports only an average.
- The record omits the GTM dependency result.
- A prompt changed during the phase.
- A holdout task ran.
- The phase claims a pass without a per-grader result.

## Phase 5: Model judge

### Preconditions

- Phase 4 is verified.
- The calibration labels are ready.
- Unit tests use a mocked model.

### Commands

```bash
uv run python -m unittest tests.test_model_judge -v
uv run python -m unittest discover -s tests -v
```

Then run the judge on one Phase 4 trial.

```bash
uv run python -m evals.run_evals \
  --task b2b_recruiting_meeting_assistant \
  --run-id "$(date +%Y%m%d-%H%M%S)-judge" \
  --judge \
  --html
```

### Expected result

- The mocked tests pass.
- The judge writes `judge_results.json`.
- The result has one entry per dimension.
- The result includes the GTM dependency dimension.
- Every entry has a score, a rationale, and an `unknown` flag.
- A malformed model response is reported as a judge error.
- A judge error is not converted to a zero score.
- The HTML report shows the judge scores or a clear "not run" state.
- The calibration record lists the human labels and the agreement per dimension.

### Evidence to save

- The test output.
- One full `judge_results.json`.
- The calibration record.
- The agreement numbers.
- The list of dimensions that need rubric work.
- The HTML report with judge scores.

### Manual checks

- The judge reads `blueprint.md`, `market.md`, `customers.md`, and `gtm.md`.
- The judge does not read files outside the trial root.
- The judge output is valid JSON.
- The judge can return `Unknown`.
- Hard gates and judge scores are reported separately.
- The judge is not a release gate until the calibration record exists.

### Fail conditions

- A judge error becomes a zero score without a log entry.
- The judge crashes on a malformed model response.
- A unit test calls a live model.
- The judge output is free text, not JSON.
- The judge cannot return `Unknown`.
- The calibration record is missing.
- The judge becomes a hard gate before calibration.
- The report mislabels a judge error as a zero score.

## Phase 6: GTM skill

### Preconditions

- Phase 5 is verified.
- The Phase 5 calibration record exists.
- The before baseline uses the same task and the same commit except for the skill and prompt change.

### Commands

```bash
uv run python -m unittest discover -s tests -v
rg -n "gtm-strategist|SKILL.md|skills=" src/agents/gtm_strategist.py src/prompts/subagents/gtm_strategist
rg -n '"tools": \[\]' src/agents/gtm_strategist.py
```

Run task 001 twice before the change and twice after the change.
Use the Phase 4 command shape for each pair.
Generate an HTML report for each pair.

### Expected result

- The GTM subagent loads the skill.
- The GTM subagent still has `"tools": []`.
- The prompt path points to `v3.yaml`.
- The `delegation` grader still passes.
- The before and after records use the same task.
- The comparison record includes delegation, judge scores, cost, and latency.
- The comparison record includes the HTML report paths.
- The comparison record states whether the skill is accepted.

### Evidence to save

- The skill path.
- The prompt version.
- The before run IDs.
- The after run IDs.
- The before and after `grader_results.json`.
- The before and after `judge_results.json`.
- The before and after `report.html`.
- The comparison record.

### Manual checks

- The skill file gives method, not new market facts.
- The skill tells the agent to read `market.md` and `customers.md` first.
- The skill tells the agent to mark missing evidence as an assumption.
- The GTM subagent still cannot search the web.
- The comparison does not mix different tasks or different commits.

### Fail conditions

- The GTM subagent has a search tool.
- The GTM subagent does not load the skill.
- The prompt is edited in place instead of a new version.
- The change has no before and after comparison.
- The comparison mixes tasks, models, or commits.
- The skill adds market facts that the research files do not support.

## Phase 7: Delegation fix comparison

### Preconditions

- Phase 1 through Phase 6 are verified.
- A separate branch implements `delegation_fix.md`.
- The new branch emits `delegation_started` and `delegation_finished` events.
- Both implementations use the same model and the same prompt versions.
- The Phase 4 baseline is available as a historical reference.

### Commands

Run two trials on the current supervisor.

```bash
uv run python -m evals.run_evals \
  --task b2b_recruiting_meeting_assistant \
  --run-id "$(date +%Y%m%d-%H%M%S)-current-a" \
  --agent-command "uv run python main.py" \
  --html

uv run python -m evals.run_evals \
  --task b2b_recruiting_meeting_assistant \
  --run-id "$(date +%Y%m%d-%H%M%S)-current-b" \
  --agent-command "uv run python main.py" \
  --html
```

Run two trials on the new orchestration branch.
Use the same task and the same command shape.
Change only the checked-out branch or the agent entry point.

```bash
uv run python -m evals.run_evals \
  --task b2b_recruiting_meeting_assistant \
  --run-id "$(date +%Y%m%d-%H%M%S)-new-a" \
  --agent-command "uv run python main.py" \
  --html

uv run python -m evals.run_evals \
  --task b2b_recruiting_meeting_assistant \
  --run-id "$(date +%Y%m%d-%H%M%S)-new-b" \
  --agent-command "uv run python main.py" \
  --html
```

### Expected result

- Four run directories exist.
- Each run has `summary.json`, `grader_results.json`, `transcript.jsonl`, and `report.html`.
- The `delegation` grader passes for both implementations.
- The new orchestration transcript has explicit delegation events for each subagent.
- The comparison record names the commit or branch for each implementation.
- The comparison record shows delegation, pass@1, pass^2, judge scores, tool calls, turns, tokens, latency, and cost.
- The comparison record states accepted, rejected, or more trials needed.

### Evidence to save

- The four run IDs.
- The commit or branch for each implementation.
- The four `grader_results.json` files.
- The four `report.html` files.
- The comparison record.

### Manual checks

- The two implementations use the same task.
- The two implementations use the same graders.
- The two implementations use the same model.
- The new orchestration emits delegation events for market, customer, and GTM.
- The GTM start is after both research finishes in every run.
- The comparison does not hide a quality or cost regression.

### Fail conditions

- Fewer than four runs exist.
- The two implementations use different tasks, graders, or models.
- The new orchestration has no explicit delegation events.
- The `delegation` grader passes because the events are missing, not because the order is correct.
- The comparison record has no decision.
- The comparison implements `delegation_fix.md` changes inside the eval code.

## Phase evidence template

Use this template in the phase pull request.

```text
Phase: <number and name>
Commit: <sha>
Commands:
  <command 1>
  <command 2>
Result:
  <pass or fail>
Evidence:
  <paths to test output, run output, and records>
Not verified:
  <anything that needs a live model, credentials, or a later phase>
```
