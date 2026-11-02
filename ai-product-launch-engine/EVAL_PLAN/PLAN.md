# Eval Plan

Status: planning only.
No phase is complete until `EVAL_PLAN/verification.md` passes for that phase.

## Purpose

This plan turns the current artifact-only eval suite into an eval that also grades the subagent path and, later, output quality.
It follows `eval_golden.md`, `AGENTS.md`, and `evals/spec.md`.
It is written for one coding session per phase.
Each phase must leave the repository in a verified state.

## Operating rules

- Run one phase per session.
- Read the phase goal, `evals/spec.md`, and `EVAL_PLAN/verification.md` before you write code.
- Do not start a phase until the previous phase is verified.
- Do not tune prompts during Phase 3.
- Do not run holdout tasks during prompt or prompt-adjacent work.
- Add a regression task for every real bug.
- Keep generated runs under `workspace/evals/`.
- Do not commit `workspace/` output, `.env`, or secrets.
- Record commands and evidence in the session handoff.
- Update `evals/RUNBOOK.md` when a command or artifact path changes.
- Keep one concern per pull request.

## Phase order

| Phase | Name | Main output |
| --- | --- | --- |
| 0 | Contract and reference trial | Updated contract, task fields, reference artifacts, reference grader test |
| 1 | Trajectory grader | Code grader that proves all three subagents ran and GTM ran after both research files |
| 2 | Trial completion | Slug pass-through, blueprint under the workspace root, manifest, zip |
| 3 | First real baseline | Two task 001 trials with recorded results |
| 4 | Model judge | Calibrated LLM rubric for quality and GTM dependency |
| 5 | GTM skill | Versioned skill for `gtm_strategist` with before and after results |

## Phase 0: Contract and reference trial

Status: not started

### Goal

Make the contract define the data that the graders will need.
Add a known-good reference trial for task 001 so the graders can be tested against correct output.

### Why

`eval_golden.md` says the reference output proves the task is solvable and proves the graders work.
A grader that fails the reference output is broken.
A task that cannot pass its own reference output is broken.
The current suite has no reference trial, so the graders have never been checked against known-good input.

### Things to implement

- [ ] Update `evals/spec.md` input schema.
  - State that the runner supplies `project_slug` to the agent.
  - The value must equal `expected.project_slug`.
- [ ] Update the task schema in `evals/spec.md`.
  - Add `expected.required_subagents`.
  - Add `expected.max_tool_calls`.
  - Add the default values for existing tasks: `market_researcher`, `customer_researcher`, `gtm_strategist`, and 60 tool calls.
- [ ] Update `evals/datasets/capability/b2b_recruiting_meeting_assistant.json`.
  - Add `required_subagents`: `market_researcher`, `customer_researcher`, `gtm_strategist`.
  - Add `max_tool_calls`: `60`.
- [ ] Add a reference trial under `evals/reference/b2b_recruiting_meeting_assistant/`.
  - Use the layout `projects/b2b-recruiting-meeting-assistant/`.
  - Add `research/market.md` with the four required headings and at least three `- [Title](URL)` sources.
  - Add `research/customers.md` with the five required headings.
  - Add `strategy/gtm.md` with the seven required headings.
  - Add `blueprint.md` with the four required headings.
  - Add a valid `manifest.json` with all four agents, non-negative integer metrics, and an artifact list that names the five non-archive files.
  - Do not commit a binary zip. The test builds it in a temporary copy.
- [ ] Add `tests/test_reference_trial.py`.
  - Copy the reference trial to a temporary directory.
  - Build `deliverable.zip` from the four Markdown files and `manifest.json`.
  - Load task `b2b_recruiting_meeting_assistant`.
  - Run the current default graders.
  - Assert that every result passes.
- [ ] Add the reference check command to `evals/RUNBOOK.md`.

### Files to touch

- `ai-product-launch-engine/evals/spec.md`
- `ai-product-launch-engine/evals/datasets/capability/b2b_recruiting_meeting_assistant.json`
- `ai-product-launch-engine/evals/reference/b2b_recruiting_meeting_assistant/` (new)
- `ai-product-launch-engine/tests/test_reference_trial.py` (new)
- `ai-product-launch-engine/evals/RUNBOOK.md`

### Done when

- [ ] `uv run python -m unittest tests.test_reference_trial -v` passes.
- [ ] Every current default grader passes on the reference trial.
- [ ] `uv run python -m evals.run_evals --validate-only --task b2b_recruiting_meeting_assistant` returns `"valid": true`.
- [ ] The input and task schema text matches the task file and the current grader behavior.
- [ ] The trajectory hard gates are deferred to Phase 1.
- [ ] No binary zip is committed.

### Out of scope

- Do not add the trajectory grader.
- Do not change agent code.
- Do not run the real agent.

### Handoff

Write the reference trial path, the test command, and the full grader result in the session summary.

## Phase 1: Trajectory grader

Status: not started

### Goal

Add a code-based grader that reads `transcript.jsonl` and proves the subagent path.
It must prove that `market_researcher`, `customer_researcher`, and `gtm_strategist` ran.
It must prove that `gtm_strategist` started after both research files were written.
It must enforce the task tool-call budget.

### Why

The current suite grades only artifacts.
Artifacts do not prove that a subagent wrote them.
The supervisor could write every file itself and pass.
The transcript records `task` tool calls with `subagent_type`, and callbacks from subagents reach the same transcript.
The golden reference already asks for this check in `eval_golden.md` at lines 490 to 495.
This check is deterministic and does not need an LLM.

### Things to implement

- [ ] Extend `evals/models.py`.
  - Add `required_subagents: tuple[str, ...]` to `TaskExpectation`.
  - Add `max_tool_calls: int` to `TaskExpectation`.
  - Parse `expected.required_subagents`.
  - Parse `expected.max_tool_calls`.
  - Default `required_subagents` to the three subagents when the field is absent.
  - Default `max_tool_calls` to `60` when the field is absent.
  - Reject an empty subagent list, duplicate names, and a non-positive tool budget.
- [ ] Add `TrajectoryGrader` to `evals/evaluators.py`.
  - Name it `trajectory`.
  - Read `trial_root/transcript.jsonl`.
  - Return a failed result, not an exception, when the file is missing or malformed.
  - Parse `tool_started` events with `tool == "task"`.
  - Extract `subagent_type` from the `input` value.
  - Accept JSON input and Python dict string input.
  - Collect the first start time for each subagent.
  - Count all `tool_started` events for the budget.
  - Find the write event for `research/market.md` inside the `market_researcher` task window.
  - Find the write event for `research/customers.md` inside the `customer_researcher` task window.
  - Fail when either research write is missing.
  - Fail when the first `gtm_strategist` start time is earlier than either research write.
  - Put all values in `details`: required agents, delegated agents, missing agents, tool count, budget, research timestamps, GTM timestamp, and dependency boolean.
- [ ] Add transcript fixtures under `evals/fixtures/transcripts/`.
  - `pass.jsonl`: all three subagents, both research writes, GTM after them, under budget.
  - `missing_gtm.jsonl`: no `gtm_strategist` task.
  - `gtm_before_research.jsonl`: GTM starts before the customer research write.
  - `tool_loop.jsonl`: more than the budget of tool starts.
  - `malformed.jsonl`: one invalid JSON line.
  - `missing_research_write.jsonl`: no market write event.
- [ ] Add `tests/test_trajectory_grader.py`.
  - Test the pass fixture.
  - Test each failure fixture.
  - Test the malformed fixture returns a failed result.
  - Test the default task fields on task 001.
- [ ] Add `TrajectoryGrader()` to `DEFAULT_GRADERS`.
- [ ] Update the hard gates in `evals/spec.md`.
  - Required subagents must be delegated.
  - `gtm_strategist` must start after `market.md` and `customers.md` are written.
  - The tool-call count must not exceed the task budget.
- [ ] Update `evals/RUNBOOK.md` to list the `trajectory` grader and its details.

### Files to touch

- `ai-product-launch-engine/evals/models.py`
- `ai-product-launch-engine/evals/evaluators.py`
- `ai-product-launch-engine/evals/fixtures/transcripts/` (new)
- `ai-product-launch-engine/tests/test_trajectory_grader.py` (new)
- `ai-product-launch-engine/evals/RUNBOOK.md`
- `ai-product-launch-engine/evals/datasets/capability/b2b_recruiting_meeting_assistant.json` if Phase 0 did not add the fields

### Done when

- [ ] `uv run python -m unittest tests.test_trajectory_grader -v` passes.
- [ ] `uv run python -m unittest discover -s tests -v` passes.
- [ ] The pass fixture returns `passed: true`.
- [ ] Each failure fixture returns `passed: false` with the expected detail.
- [ ] A malformed transcript returns a failed result and does not crash the runner.
- [ ] `uv run python -m evals.run_evals --validate-only --task b2b_recruiting_meeting_assistant` passes.
- [ ] `grader_results.json` for a graded trial contains a `trajectory` entry.
- [ ] The hard gates in `evals/spec.md` match the new grader.

### Out of scope

- Do not add an LLM judge.
- Do not change prompt text.
- Do not require an exact delegation order for the two research agents.
- Do not require a specific tool-call sequence.

### Handoff

Write the transcript event shape, the fixture paths, and one full `grader_results.json` example in the session summary.

## Phase 2: Trial completion

Status: not started

### Goal

Make one real run produce every artifact that the contract requires.
The run must produce `market.md`, `customers.md`, `gtm.md`, `blueprint.md`, `manifest.json`, and `deliverable.zip` inside the trial root.

### Why

The current pipeline cannot pass its own hard gates.
The executor does not pass `project_slug`, so the agent derives a long slug from the idea.
`create_blueprint` writes to the host path `/projects/...` and catches the error, so the blueprint is missing.
No code writes `manifest.json` or `deliverable.zip`.
A baseline taken before these fixes measures plumbing bugs, not the agents.

### Things to implement

- [ ] Update `evals/executor.py`.
  - Add `"project_slug": task.expected.project_slug` to `input.json`.
  - Add a test that the written input contains the expected slug.
- [ ] Update `src/agents/supervisor.py`.
  - Change `create_blueprint` to resolve paths under the workspace root, not host `/projects/...`.
  - Accept a `workspace_root: Path` argument.
  - Use `workspace_root / "projects" / project_slug`.
  - Remove the broad `except Exception` that hides failures.
  - Let the caller or the runner record a real failure.
- [ ] Update `main.py`.
  - Pass the workspace root to `create_blueprint`.
  - Call the packaging step after the blueprint is written.
- [ ] Add `src/metrics.py`.
  - Read `LAUNCH_ENGINE_TRANSCRIPT_PATH` when it exists.
  - Count model starts as turns.
  - Count tool starts as tool calls.
  - Infer `agents_used` from `task` tool calls.
  - Sum token usage when the transcript has it.
  - Return zeros when a value is unavailable.
- [ ] Add `src/packaging.py`.
  - `write_manifest(project_root, project_slug, agents_used, metrics)`.
  - Write `metadata.project_slug`, `metadata.created_at`, and `metadata.version`.
  - Write the artifact names for the five non-archive files, including `manifest.json`.
  - Write `execution.agents_used`, `execution.total_turns`, `execution.total_tool_calls`, and `execution.total_tokens`.
  - `build_deliverable(project_root, project_slug)`.
  - Zip `research/market.md`, `research/customers.md`, `strategy/gtm.md`, `blueprint.md`, and `manifest.json`.
- [ ] Add tests.
  - `tests/test_executor.py`: input contains `project_slug`.
  - `tests/test_blueprint.py`: blueprint is written under a temporary root and not under host `/projects`.
  - `tests/test_packaging.py`: manifest matches the contract, zip is valid, and zip entries are correct.
- [ ] Update `evals/spec.md` if the manifest field source or packaging order needs a note.

### Files to touch

- `ai-product-launch-engine/evals/executor.py`
- `ai-product-launch-engine/src/agents/supervisor.py`
- `ai-product-launch-engine/main.py`
- `ai-product-launch-engine/src/metrics.py` (new)
- `ai-product-launch-engine/src/packaging.py` (new)
- `ai-product-launch-engine/tests/test_executor.py` (new or extend)
- `ai-product-launch-engine/tests/test_blueprint.py` (new or extend)
- `ai-product-launch-engine/tests/test_packaging.py` (new)

### Done when

- [ ] `uv run python -m unittest discover -s tests -v` passes.
- [ ] A temporary simulated run produces all six required artifacts under the trial root.
- [ ] `manifest.json` passes `ManifestGrader`.
- [ ] The manifest artifact list names the five non-archive files, including `manifest.json`.
- [ ] `deliverable.zip` passes `ArchiveGrader`.
- [ ] No file is written to host `/projects`.
- [ ] A blueprint write failure returns a non-zero process code.
- [ ] The blueprint contains the four required headings.

### Out of scope

- Do not run the real agent.
- Do not tune prompts.
- Do not add the model judge.
- Do not change the project slug rules in `src/schemas.py`.

### Handoff

Write the artifact tree, the manifest JSON, and the zip entry list in the session summary.

## Phase 3: First real baseline

Status: not started

### Goal

Run task 001 twice with the real agent on one commit.
Record the result as the first baseline.

### Why

The golden reference says to run the current system and expect failure.
One run is not a baseline because agents vary.
Two runs show whether the result is stable.
The baseline must exist before any prompt tuning.

### Preconditions

- [ ] Phase 0, Phase 1, and Phase 2 are verified.
- [ ] `.env` contains `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `TAVILY_API_KEY`.
- [ ] `AWS_SESSION_TOKEN` is set when the credentials require it.
- [ ] No prompt files changed since the last commit.
- [ ] The working tree is clean except for ignored run output.

### Things to implement

- [ ] Add `evals/baselines/README.md`.
  - Define the baseline record fields.
  - State that a baseline needs at least two trials.
  - State that holdout tasks are excluded.
- [ ] Run task 001 twice with a distinct run ID.
  - Use `b2b_recruiting_meeting_assistant`.
  - Use a new `--trial-root` for each run.
  - Use `--agent-command "uv run python main.py"`.
  - Save `summary.json` inside each run directory.
- [ ] Add a baseline record at `evals/baselines/<date>-task-001.json`.
  - Record the commit SHA.
  - Record the model ID and region.
  - Record the supervisor prompt version and the three subagent prompt versions.
  - Record both run IDs.
  - Record the per-grader result for each run.
  - Record pass@1 and pass^2.
  - Record the failure classes from `evals/spec.md`.
  - Record latency and tool count from the transcript.
- [ ] Classify every failure with the failure taxonomy in `evals/spec.md`.
- [ ] Do not change a prompt or a tool to make the baseline pass.

### Files to touch

- `ai-product-launch-engine/evals/baselines/README.md` (new)
- `ai-product-launch-engine/evals/baselines/<date>-task-001.json` (new)
- `ai-product-launch-engine/evals/RUNBOOK.md` if the commands change

### Done when

- [ ] Two run directories exist under `workspace/evals/`.
- [ ] Each run has `summary.json`, `grader_results.json`, `transcript.jsonl`, and `projects/`.
- [ ] The baseline record names both runs and the commit SHA.
- [ ] The record reports per-grader results, not only an average.
- [ ] Every failure has a failure class.
- [ ] No holdout task ran.
- [ ] No prompt file changed during the phase.
- [ ] The baseline is recorded before any tuning.

### Out of scope

- Do not run tasks 002 to 020.
- Do not run holdouts.
- Do not tune prompts or tools.
- Do not add the model judge.

### Handoff

Write the run IDs, the pass results, the worst failure class, and the path to the baseline record in the session summary.

## Phase 4: Model judge

Status: not started

### Goal

Add an LLM rubric judge for the quality dimensions that code cannot check.
The judge must score the four dimensions in `evals/spec.md`.
It must also judge the GTM dependency rule: the GTM strategy must come from the two research files, not from new, unsupported research.

### Why

Code graders can prove that files exist and that headings match.
They cannot prove that the research is grounded, that the positioning is specific, or that GTM content follows from the two research files.
The golden reference says to use a model judge for these checks and to calibrate it against human labels.
The current `evals/decisions.md` already names this judge as future work.

### Things to implement

- [ ] Add `evals/model_judge.py`.
  - Use the same Bedrock provider path as the agent.
  - Read the model ID from `JUDGE_MODEL_ID`, then fall back to `BEDROCK_MODEL_ID`.
  - Send the blueprint and the three source artifacts.
  - Return strict JSON.
  - Allow `Unknown` when evidence is insufficient.
  - Never treat a judge error as a zero score without logging it.
- [ ] Add rubric files under `evals/rubrics/`.
  - `research_quality.md` for completeness, evidence quality, and source authority.
  - `blueprint_quality.md` for structure, coherence, and actionability.
  - `assumption_transparency.md` for labels, impact, and validation method.
  - `gtm_coherence.md` for positioning, messaging, distribution, and sequence.
  - `gtm_dependency.md` for whether GTM claims trace to `market.md` and `customers.md`.
- [ ] Add a `--judge` flag to `evals/run_evals.py`.
  - Run the code graders first.
  - Run the judge after the code graders when the flag is set.
  - Keep hard gates and judge scores separate.
- [ ] Add a judge result file next to `grader_results.json`.
  - Name it `judge_results.json`.
- [ ] Add `tests/test_model_judge.py` with a mocked model.
  - Test valid JSON.
  - Test `Unknown`.
  - Test a malformed model response.
  - Test a model error is logged and not converted to zero.
- [ ] Add a calibration record under `evals/baselines/`.
  - Start with the reference trial and the two Phase 3 runs.
  - Label those three outputs by hand once.
  - Record agreement per dimension.
  - Expand to 20 to 30 labels before the judge becomes a release gate.
- [ ] Do not make the judge a hard gate until the calibration record exists.

### Files to touch

- `ai-product-launch-engine/evals/model_judge.py` (new)
- `ai-product-launch-engine/evals/rubrics/` (new)
- `ai-product-launch-engine/evals/run_evals.py`
- `ai-product-launch-engine/evals/RUNBOOK.md`
- `ai-product-launch-engine/tests/test_model_judge.py` (new)
- `ai-product-launch-engine/evals/baselines/` (new calibration record)

### Done when

- [ ] `uv run python -m unittest tests.test_model_judge -v` passes.
- [ ] A judge run writes `judge_results.json` with the four contract dimensions plus the GTM dependency dimension.
- [ ] Every dimension can return `Unknown`.
- [ ] Judge errors appear in the result and are not silently scored as zero.
- [ ] The calibration record shows the human labels and the agreement.
- [ ] The judge is reported separately from the hard gates.

### Out of scope

- Do not tune prompts based on judge scores until the calibration record exists.
- Do not add the GTM skill.
- Do not make the judge a release gate.

### Handoff

Write the rubric paths, the calibration agreement, and one full `judge_results.json` example in the session summary.

## Phase 5: GTM skill

Status: not started
Blocked by: Phase 4 calibration

### Goal

Add a domain skill for `gtm_strategist`.
The skill must make the strategy consistent without letting the agent invent new research.

### Why

The current GTM prompt gives only generic instructions.
The GTM agent has no search tool, which enforces the dependency rule, but it also has no domain playbook.
A skill file gives it a stable method for positioning, messaging, distribution, and launch sequence.
This change is prompt-adjacent and must be measured against the Phase 3 and Phase 4 baselines.

### Things to implement

- [ ] Add a skill file under the deepagents skills layout.
  - Use `ai-product-launch-engine/skills/gtm-strategist/SKILL.md`.
  - Keep it focused on method, not on new market facts.
  - Tell the agent to read `market.md` and `customers.md` before it writes `gtm.md`.
  - Tell the agent to mark missing evidence as an assumption.
- [ ] Wire the skill to the `gtm_strategist` spec.
  - Use the `skills` field or `SkillsMiddleware` supported by the installed deepagents version.
  - Keep `"tools": []` on the GTM subagent.
- [ ] Add a new prompt version instead of editing the current one.
  - Create `src/prompts/subagents/gtm_strategist/v3.yaml`.
  - Update `PROMPT_PATH` in `src/agents/gtm_strategist.py`.
  - Update `evaluation_status`.
- [ ] Run task 001 twice before the skill change and twice after.
- [ ] Compare trajectory results and judge scores before and after.
- [ ] Add a regression task if the skill fixes a real failure.

### Files to touch

- `ai-product-launch-engine/skills/gtm-strategist/SKILL.md` (new)
- `ai-product-launch-engine/src/agents/gtm_strategist.py`
- `ai-product-launch-engine/src/prompts/subagents/gtm_strategist/v3.yaml` (new)
- `ai-product-launch-engine/evals/baselines/` (before and after record)
- `ai-product-launch-engine/tests/` for the skill wiring

### Done when

- [ ] The GTM subagent loads the skill.
- [ ] The trajectory grader still passes.
- [ ] The GTM subagent still has no search tool.
- [ ] The before and after runs use the same task and the same commit except for the skill and prompt change.
- [ ] The comparison record shows trajectory, judge scores, cost, and latency.
- [ ] The skill change is accepted or rejected based on the comparison.

### Out of scope

- Do not change the market or customer prompts.
- Do not add a search tool to the GTM subagent.
- Do not skip the before and after comparison.

### Handoff

Write the skill path, the prompt version, and the before and after comparison in the session summary.

## Phase completion protocol

Use this protocol for every phase.

1. Read the phase and the matching section in `EVAL_PLAN/verification.md`.
2. Implement only that phase.
3. Run the narrow tests first.
4. Run the full local suite.
5. Run the phase verification commands.
6. Record the evidence in the session summary.
7. Open a pull request with the phase name.
8. Do not start the next phase until the pull request is reviewed or merged.

## Definition of done for every phase

- [ ] The behavior works through the closest real surface.
- [ ] The phase tests pass.
- [ ] The full local suite passes.
- [ ] `EVAL_PLAN/verification.md` passes for the phase.
- [ ] The contract and the runbook match the code.
- [ ] No secrets or generated artifacts are committed.
- [ ] The pull request body states what was verified and what was not.
