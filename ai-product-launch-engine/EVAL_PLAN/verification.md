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

- The current default graders are unchanged.
- Task `b2b_recruiting_meeting_assistant` loads.

### Commands

```bash
uv run python -m unittest tests.test_reference_trial -v
uv run python -m evals.run_evals --validate-only --task b2b_recruiting_meeting_assistant
git diff --check
```

### Expected result

- `tests.test_reference_trial` passes.
- Every current default grader passes on the reference trial.
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

- Any current grader fails on the reference trial.
- The reference trial has a placeholder such as `TODO` or `[citation needed]`.
- The contract says something that the task file or the graders do not do.
- A binary zip is committed.

## Phase 1: Trajectory grader

### Preconditions

- Phase 0 is verified.
- `evals/fixtures/transcripts/` contains the six fixtures listed in `PLAN.md`.

### Commands

```bash
uv run python -m unittest tests.test_trajectory_grader -v
uv run python -m unittest discover -s tests -v
uv run python -m evals.run_evals --validate-only --task b2b_recruiting_meeting_assistant
```

### Expected result

The test for `pass.jsonl` reports:

- `passed: true`.
- `delegated_subagents` contains all three subagents.
- `missing_subagents` is empty.
- `gtm_after_research` is `true`.
- `tool_call_count` is less than or equal to `max_tool_calls`.

The test for `missing_gtm.jsonl` reports:

- `passed: false`.
- `missing_subagents` contains `gtm_strategist`.

The test for `gtm_before_research.jsonl` reports:

- `passed: false`.
- `gtm_after_research` is `false`.

The test for `tool_loop.jsonl` reports:

- `passed: false`.
- `tool_call_count` is greater than `max_tool_calls`.

The test for `missing_research_write.jsonl` reports:

- `passed: false`.
- The detail names the missing market or customer write.

The test for `malformed.jsonl` reports:

- `passed: false`.
- The detail names the malformed line.
- The test does not raise an exception.

### Evidence to save

- The test output.
- The fixture paths.
- One full JSON result for the pass fixture and one for a failure fixture.

### Manual checks

- `TrajectoryGrader` is in `DEFAULT_GRADERS`.
- The hard gates in `evals/spec.md` name the three subagents, the GTM dependency, and the tool budget.
- The task file for `b2b_recruiting_meeting_assistant` has `required_subagents` and `max_tool_calls`.
- The grader does not require the two research agents to run in a fixed order.
- The grader does not require an exact tool-call sequence.
- The grader uses timestamps, not list order alone, for the GTM dependency check.

### Fail conditions

- A missing subagent still passes.
- GTM before the research writes still passes.
- A tool loop still passes.
- A malformed transcript crashes the runner.
- The grader requires one exact delegation order for all three agents.
- The grader depends on live model calls or network access.

## Phase 2: Trial completion

### Preconditions

- Phase 1 is verified.
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

## Phase 3: First real baseline

### Preconditions

- Phase 0, Phase 1, and Phase 2 are verified.
- `.env` has the required provider keys.
- No prompt file changed since the last commit.
- The working tree is clean except for `workspace/` output.

### Commands

Run two trials with different run IDs.

```bash
run_id_1="$(date +%Y%m%d-%H%M%S)-a"
uv run python -m evals.run_evals \
  --task b2b_recruiting_meeting_assistant \
  --trial-root "workspace/evals/$run_id_1/trials" \
  --agent-command "uv run python main.py" \
  --report "workspace/evals/$run_id_1/summary.json"

run_id_2="$(date +%Y%m%d-%H%M%S)-b"
uv run python -m evals.run_evals \
  --task b2b_recruiting_meeting_assistant \
  --trial-root "workspace/evals/$run_id_2/trials" \
  --agent-command "uv run python main.py" \
  --report "workspace/evals/$run_id_2/summary.json"
```

Then inspect each run.

```bash
find "workspace/evals/$run_id_1" -maxdepth 8 -type f | sort
find "workspace/evals/$run_id_2" -maxdepth 8 -type f | sort
```

A red baseline may make `evals.run_evals` exit with code `1`.
That is expected when a hard gate fails.
Do not treat the nonzero exit as a crash.
Inspect `summary.json` and `grader_results.json` for the real result.

### Expected result

Each run directory contains:

- `summary.json`.
- `trials/b2b_recruiting_meeting_assistant/input.json`.
- `trials/b2b_recruiting_meeting_assistant/transcript.jsonl`.
- `trials/b2b_recruiting_meeting_assistant/grader_results.json`.
- `trials/b2b_recruiting_meeting_assistant/projects/b2b-recruiting-meeting-assistant/`.

Each `grader_results.json` contains the `trajectory` grader.
Each `transcript.jsonl` contains task events for all three subagents.
The baseline record names both run IDs and the commit SHA.
The baseline record reports pass@1 and pass^2.
The baseline record reports per-grader results, not only an average.
Every failure has a failure class from `evals/spec.md`.

### Evidence to save

- Both run IDs.
- Both `summary.json` files.
- Both `grader_results.json` files.
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

### Fail conditions

- Only one run exists.
- A run has no transcript.
- A run has no `grader_results.json`.
- The baseline record is missing.
- The record reports only an average.
- A prompt changed during the phase.
- A holdout task ran.
- The phase claims a pass without a per-grader result.

## Phase 4: Model judge

### Preconditions

- Phase 3 is verified.
- The calibration labels are ready.
- Unit tests use a mocked model.

### Commands

```bash
uv run python -m unittest tests.test_model_judge -v
uv run python -m unittest discover -s tests -v
```

Then run the judge on one Phase 3 trial.

```bash
uv run python -m evals.run_evals \
  --task b2b_recruiting_meeting_assistant \
  --trial-root "workspace/evals/<run_id>/trials" \
  --judge \
  --report "workspace/evals/<run_id>/summary-with-judge.json"
```

### Expected result

- The mocked tests pass.
- The judge writes `judge_results.json`.
- The result has one entry per dimension.
- Every entry has a score, a rationale, and an `unknown` flag.
- A malformed model response is reported as a judge error.
- A judge error is not converted to a zero score.
- The calibration record lists the human labels and the agreement per dimension.

### Evidence to save

- The test output.
- One full `judge_results.json`.
- The calibration record.
- The agreement numbers.
- The list of dimensions that need rubric work.

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

## Phase 5: GTM skill

### Preconditions

- Phase 4 is verified.
- The Phase 4 calibration record exists.
- The before baseline uses the same task and the same commit except for the skill and prompt change.

### Commands

```bash
uv run python -m unittest discover -s tests -v
rg -n "gtm-strategist|SKILL.md|skills=" src/agents/gtm_strategist.py src/prompts/subagents/gtm_strategist
rg -n '"tools": \[\]' src/agents/gtm_strategist.py
```

Run task 001 twice before the change and twice after the change.
Use the Phase 3 command shape for each pair.

### Expected result

- The GTM subagent loads the skill.
- The GTM subagent still has `"tools": []`.
- The prompt path points to `v3.yaml`.
- The trajectory grader still passes.
- The before and after records use the same task.
- The comparison record includes trajectory, judge scores, cost, and latency.
- The comparison record states whether the skill is accepted.

### Evidence to save

- The skill path.
- The prompt version.
- The before run IDs.
- The after run IDs.
- The before and after `grader_results.json`.
- The before and after `judge_results.json`.
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
