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
- Do not tune prompts during Phase 4.
- Do not run holdout tasks during prompt or prompt-adjacent work.
- Add a regression task for every real bug.
- Keep generated runs under `workspace/evals/`.
- Do not commit `workspace/` output, `.env`, or secrets.
- Record commands and evidence in the session handoff.
- Update `evals/RUNBOOK.md` when a command or artifact path changes.
- Keep one concern per pull request.
- Do not implement `delegation_fix.md` in these phases.
  That document is design input for Phase 7.
  Phase 7 compares the current delegation path with the new path after a separate implementation exists.

## Phase order

| Phase | Name | Main output |
| --- | --- | --- |
| 0 | Contract and reference trial | Updated contract, task fields, reference artifacts, reference grader test |
| 1 | Delegation order and GTM dependency grader | Code grader that proves GTM starts only after both research results are received |
| 2 | HTML results viewer | Self-contained `report.html` for one task or a full suite |
| 3 | Trial completion | Slug pass-through, blueprint under the workspace root, manifest, zip |
| 4 | First real baseline | Two task 001 trials with recorded results |
| 5 | Model judge | Calibrated LLM rubric for quality and GTM dependency |
| 6 | GTM skill | Versioned skill for `gtm_strategist` with before and after results |
| 7 | Delegation fix comparison | Current supervisor compared with the programmatic orchestration in `delegation_fix.md` |

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
  - Run the seven artifact graders explicitly.
  - Do not use `DEFAULT_GRADERS`, because Phase 1 adds a transcript grader that needs a transcript.
  - Assert that every artifact grader passes.
- [ ] Add the reference check command to `evals/RUNBOOK.md`.

### Files to touch

- `ai-product-launch-engine/evals/spec.md`
- `ai-product-launch-engine/evals/datasets/capability/b2b_recruiting_meeting_assistant.json`
- `ai-product-launch-engine/evals/reference/b2b_recruiting_meeting_assistant/` (new)
- `ai-product-launch-engine/tests/test_reference_trial.py` (new)
- `ai-product-launch-engine/evals/RUNBOOK.md`

### Done when

- [ ] `uv run python -m unittest tests.test_reference_trial -v` passes.
- [ ] Every artifact grader passes on the reference trial.
- [ ] `uv run python -m evals.run_evals --validate-only --task b2b_recruiting_meeting_assistant` returns `"valid": true`.
- [ ] The input and task schema text matches the task file and the current grader behavior.
- [ ] The delegation hard gates are deferred to Phase 1.
- [ ] No binary zip is committed.

### Out of scope

- Do not add the delegation grader.
- Do not change agent code.
- Do not run the real agent.

### Handoff

Write the reference trial path, the test command, and the full grader result in the session summary.

## Phase 1: Delegation order and GTM dependency grader

Status: not started

### Goal

Add a code-based grader that reads `transcript.jsonl` and proves the subagent path.
The primary rule is this: `gtm_strategist` must start only after the supervisor has received the results from both `market_researcher` and `customer_researcher`.
The grader must also prove that all three subagents ran and that the run stayed within the tool-call budget.

### Why

The current suite grades only artifacts.
Artifacts do not prove that a subagent wrote them.
The supervisor could write every file itself and pass.
The transcript records `task` tool calls with `subagent_type`, and callbacks from subagents reach the same transcript.
The golden reference already asks for this check in `eval_golden.md` at lines 490 to 495.
This check is deterministic and does not need an LLM.
It is the first priority because the GTM output is only valid when it follows both research results.

### Delegation event contract

The grader must read one stable event shape for delegation.
The current `task` tool path produces this shape:

```json
{"event": "tool_started", "run_id": "...", "tool": "task", "input": "{'description': '...', 'subagent_type': 'market_researcher'}"}
{"event": "tool_finished", "run_id": "...", "tool": "task", "output": "..."}
```

The grader must also accept explicit delegation events:

```json
{"event": "delegation_started", "run_id": "...", "subagent": "market_researcher", "timestamp": "..."}
{"event": "delegation_finished", "run_id": "...", "subagent": "market_researcher", "status": "ok", "timestamp": "..."}
```

The programmatic orchestration in `delegation_fix.md` must emit the explicit shape when it is implemented.
That keeps the Phase 7 comparison honest.
Do not implement that orchestration in this phase.

### Things to implement

- [ ] Extend `src/transcript.py`.
  - Record `run_id` and `parent_run_id` on every event.
  - Record `tags` and `metadata` when they are present.
  - Cache the tool name by `run_id` at `on_tool_start`.
  - Include the cached `tool` name in `on_tool_end` and in `on_tool_error`.
  - Include the model name in model events.
- [ ] Extend `evals/models.py`.
  - Add `required_subagents: tuple[str, ...]` to `TaskExpectation`.
  - Add `max_tool_calls: int` to `TaskExpectation`.
  - Parse `expected.required_subagents`.
  - Parse `expected.max_tool_calls`.
  - Default `required_subagents` to the three subagents when the field is absent.
  - Default `max_tool_calls` to `60` when the field is absent.
  - Reject an empty subagent list, duplicate names, and a non-positive tool budget.
- [ ] Add `DelegationGrader` to `evals/evaluators.py`.
  - Name it `delegation`.
  - Read `trial_root/transcript.jsonl`.
  - Return a failed result, not an exception, when the file is missing or malformed.
  - Normalize explicit `delegation_started` and `delegation_finished` events.
  - Normalize `tool_started` and `tool_finished` events with `tool == "task"`.
  - Extract `subagent_type` from the `input` value.
  - Accept JSON input and Python dict string input.
  - Pair each start and finish by `run_id`.
  - Fail when `run_id` is missing and a pair cannot be proven.
  - Collect the first start time for each subagent.
  - Collect the finish time for `market_researcher` and `customer_researcher`.
  - Fail when either research finish is missing.
  - Fail when the first `gtm_strategist` start time is earlier than the market finish or the customer finish.
  - Count all `tool_started` events for the budget.
  - Put all values in `details`: required agents, delegated agents, missing agents, start and finish times, tool count, budget, and the dependency boolean.
  - Keep the research file write events as a secondary detail, not the primary gate.
- [ ] Add transcript fixtures under `evals/fixtures/transcripts/`.
  - `pass_parallel.jsonl`: market and customer run in parallel, both finish, then GTM starts.
  - `pass_sequential.jsonl`: market finishes, customer finishes, then GTM starts.
  - `gtm_before_customer_result.jsonl`: GTM starts after the market result but before the customer result.
  - `gtm_before_both_results.jsonl`: GTM starts before both results.
  - `missing_customer_result.jsonl`: no customer finish event.
  - `missing_run_id.jsonl`: task events without `run_id`.
  - `tool_loop.jsonl`: more than the budget of tool starts.
  - `malformed.jsonl`: one invalid JSON line.
- [ ] Add `tests/test_delegation_grader.py`.
  - Test both pass fixtures.
  - Test each failure fixture.
  - Test the malformed fixture returns a failed result.
  - Test the default task fields on task 001.
- [ ] Add `DelegationGrader()` to `DEFAULT_GRADERS`.
- [ ] Update the hard gates in `evals/spec.md`.
  - All three subagents must be delegated.
  - `gtm_strategist` must start after both research results are received.
  - The tool-call count must not exceed the task budget.
- [ ] Update `evals/RUNBOOK.md` to list the `delegation` grader and its details.

### Files to touch

- `ai-product-launch-engine/src/transcript.py`
- `ai-product-launch-engine/evals/models.py`
- `ai-product-launch-engine/evals/evaluators.py`
- `ai-product-launch-engine/evals/fixtures/transcripts/` (new)
- `ai-product-launch-engine/tests/test_delegation_grader.py` (new)
- `ai-product-launch-engine/evals/RUNBOOK.md`
- `ai-product-launch-engine/evals/datasets/capability/b2b_recruiting_meeting_assistant.json` if Phase 0 did not add the fields

### Done when

- [ ] `uv run python -m unittest tests.test_delegation_grader -v` passes.
- [ ] `uv run python -m unittest discover -s tests -v` passes.
- [ ] Both pass fixtures return `passed: true`.
- [ ] Each failure fixture returns `passed: false` with the expected detail.
- [ ] A malformed transcript returns a failed result and does not crash the runner.
- [ ] A missing `run_id` fails the hard gate with a clear detail.
- [ ] `uv run python -m evals.run_evals --validate-only --task b2b_recruiting_meeting_assistant` passes.
- [ ] `grader_results.json` for a graded trial contains a `delegation` entry.
- [ ] The hard gates in `evals/spec.md` match the new grader.

### Out of scope

- Do not add an LLM judge.
- Do not change prompt text.
- Do not require the two research agents to run in a fixed order.
- Do not require an exact tool-call sequence.
- Do not implement `delegation_fix.md`.

### Handoff

Write the transcript event shape, the fixture paths, and one full `grader_results.json` example in the session summary.

## Phase 2: HTML results viewer

Status: not started

### Goal

Add a self-contained HTML report for any graded run.
The report must work for one task and for a full suite.
It must show the metrics that decide whether a run is good.

### Why

`summary.json` and `grader_results.json` are hard to scan.
A visual report makes every baseline and every later comparison fast to inspect.
It also makes the GTM dependency check and the subagent timeline visible at a glance.
The report must exist before the first baseline so the baseline is actually reviewed.

### Things to implement

- [ ] Add `markdown-it-py` to `pyproject.toml` with a concrete need: safe Markdown rendering for the four artifacts.
  - Use `html=False` so raw HTML in model output is escaped.
  - Do not enable raw HTML.
- [ ] Add `evals/report_html.py`.
  - CLI: `--run <run_dir>` and optional `--output <path>`.
  - Default output: `<run_dir>/report.html`.
  - Read `summary.json`.
  - Read each trial `grader_results.json`.
  - Read `judge_results.json` when it exists.
  - Read `transcript.jsonl` when it exists.
  - Read `input.json` when it exists.
  - Read the six project artifacts when they exist.
  - Render one self-contained HTML file with inline CSS and minimal inline JavaScript.
  - Do not use a CDN, external fonts, external images, or network calls.
  - Detect a single-task run and a multi-task run from `summary.json`.
  - Render a clear empty state when a file is missing.
  - Escape all untrusted text before it enters the HTML.
- [ ] Add a `--html` flag to `evals/run_evals.py`.
  - Generate the report after grading.
  - Print the report path.
  - If HTML generation fails, print the error and keep the JSON result.
- [ ] Add the report sections.
  - Header: run ID, timestamp, commit SHA, model ID, task count, and overall status.
  - KPI cards: pass rate, pass^N when available, failed tasks, total tool calls, total tokens, latency, and GTM dependency status.
  - Task table: task ID, pass or fail, failure class, artifact score, delegation score, judge score, cost, and latency.
  - Per-task detail: input, six artifact checks, section coverage, source count, manifest, archive, placeholders, delegation timeline, judge dimensions, and failure classes.
  - Delegation timeline: market start and finish, customer start and finish, GTM start and finish, and a GTM-after-both badge.
  - Transcript timeline: delegation events, model events, tool events, and errors.
  - Artifact preview: render `market.md`, `customers.md`, `gtm.md`, and `blueprint.md`; show `manifest.json`; list zip entries.
  - Links to the raw JSON and transcript files.
- [ ] Define the visual system in the module.
  - System font stack.
  - CSS variables for background, text, border, pass, fail, warn, and muted.
  - Cards with clear spacing, rounded corners, and subtle borders.
  - Status badges with both color and text, so color is not the only signal.
  - Responsive layout for desktop and mobile.
  - Print-friendly styles.
  - Keyboard-friendly tabs and `aria` labels.
- [ ] Add `tests/test_report_html.py`.
  - Build a passing fixture run from the Phase 0 reference trial.
  - Build a failing fixture run with a missing artifact and a GTM-before-customer-result transcript.
  - Generate both reports.
  - Assert that the pass and fail status text appears.
  - Assert that the GTM dependency badge appears.
  - Assert that the task table and the metric cards appear.
  - Assert that raw HTML in an artifact is escaped.
  - Assert that no external asset reference exists: no `<script src=`, no `<link href="http`, and no `@import url(http`.
  - Assert that a single-task run and a multi-task run both render.
- [ ] Update `evals/RUNBOOK.md` with the report command for one task and for a suite.
- [ ] Update the report format section in `evals/spec.md` to name `report.html`.

### Files to touch

- `ai-product-launch-engine/pyproject.toml`
- `ai-product-launch-engine/evals/report_html.py` (new)
- `ai-product-launch-engine/evals/run_evals.py`
- `ai-product-launch-engine/evals/spec.md`
- `ai-product-launch-engine/evals/RUNBOOK.md`
- `ai-product-launch-engine/tests/test_report_html.py` (new)

### Done when

- [ ] `uv run python -m unittest tests.test_report_html -v` passes.
- [ ] `uv run python -m evals.report_html --run <fixture_run>` writes `report.html`.
- [ ] `uv run python -m evals.run_evals ... --html` writes `report.html` automatically.
- [ ] The HTML opens offline in a browser.
- [ ] The report shows the overall status, the per-task status, the per-grader status, and the delegation timeline.
- [ ] The GTM dependency badge matches the `delegation` grader result.
- [ ] A single-task run and a multi-task run both render.
- [ ] Missing files show a clear empty state, not a crash.
- [ ] No external asset is loaded.
- [ ] Raw HTML in an artifact is escaped.

### Out of scope

- Do not add a web server.
- Do not add a database.
- Do not add live refresh.
- Do not add external chart libraries.
- Do not change the grader logic.

### Handoff

Write the report command, the report path, and screenshots or a text summary of the rendered sections in the session summary.

## Phase 3: Trial completion

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
  - Infer `agents_used` from delegation events.
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

## Phase 4: First real baseline

Status: not started

### Goal

Run task 001 twice with the real agent on one commit.
Record the result as the first baseline.
Inspect the baseline in the Phase 2 HTML report.

### Why

The golden reference says to run the current system and expect failure.
One run is not a baseline because agents vary.
Two runs show whether the result is stable.
The baseline must exist before any prompt tuning.

### Preconditions

- [ ] Phase 0, Phase 1, Phase 2, and Phase 3 are verified.
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
  - Use `--html` to write the report.
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
  - Record the HTML report path for each run.
- [ ] Classify every failure with the failure taxonomy in `evals/spec.md`.
- [ ] Do not change a prompt or a tool to make the baseline pass.

### Files to touch

- `ai-product-launch-engine/evals/baselines/README.md` (new)
- `ai-product-launch-engine/evals/baselines/<date>-task-001.json` (new)
- `ai-product-launch-engine/evals/RUNBOOK.md` if the commands change

### Done when

- [ ] Two run directories exist under `workspace/evals/`.
- [ ] Each run has `summary.json`, `grader_results.json`, `transcript.jsonl`, `report.html`, and `projects/`.
- [ ] The baseline record names both runs and the commit SHA.
- [ ] The record reports per-grader results, not only an average.
- [ ] Every failure has a failure class.
- [ ] No holdout task ran.
- [ ] No prompt file changed during the phase.
- [ ] The baseline is recorded before any tuning.
- [ ] The HTML report opens and matches the JSON results.

### Out of scope

- Do not run tasks 002 to 020.
- Do not run holdouts.
- Do not tune prompts or tools.
- Do not add the model judge.

### Handoff

Write the run IDs, the pass results, the worst failure class, the report paths, and the path to the baseline record in the session summary.

## Phase 5: Model judge

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
- [ ] Render the judge scores in the Phase 2 HTML report.
  - Show a clear "not run" state when the file is absent.
- [ ] Add `tests/test_model_judge.py` with a mocked model.
  - Test valid JSON.
  - Test `Unknown`.
  - Test a malformed model response.
  - Test a model error is logged and not converted to zero.
- [ ] Add a calibration record under `evals/baselines/`.
  - Start with the reference trial and the two Phase 4 runs.
  - Label those three outputs by hand once.
  - Record agreement per dimension.
  - Expand to 20 to 30 labels before the judge becomes a release gate.
- [ ] Do not make the judge a hard gate until the calibration record exists.

### Files to touch

- `ai-product-launch-engine/evals/model_judge.py` (new)
- `ai-product-launch-engine/evals/rubrics/` (new)
- `ai-product-launch-engine/evals/run_evals.py`
- `ai-product-launch-engine/evals/report_html.py`
- `ai-product-launch-engine/evals/RUNBOOK.md`
- `ai-product-launch-engine/tests/test_model_judge.py` (new)
- `ai-product-launch-engine/evals/baselines/` (new calibration record)

### Done when

- [ ] `uv run python -m unittest tests.test_model_judge -v` passes.
- [ ] A judge run writes `judge_results.json` with the four contract dimensions plus the GTM dependency dimension.
- [ ] Every dimension can return `Unknown`.
- [ ] Judge errors appear in the result and are not silently scored as zero.
- [ ] The HTML report shows the judge scores or a clear "not run" state.
- [ ] The calibration record shows the human labels and the agreement.
- [ ] The judge is reported separately from the hard gates.

### Out of scope

- Do not tune prompts based on judge scores until the calibration record exists.
- Do not add the GTM skill.
- Do not make the judge a release gate.

### Handoff

Write the rubric paths, the calibration agreement, and one full `judge_results.json` example in the session summary.

## Phase 6: GTM skill

Status: not started
Blocked by: Phase 5 calibration

### Goal

Add a domain skill for `gtm_strategist`.
The skill must make the strategy consistent without letting the agent invent new research.

### Why

The current GTM prompt gives only generic instructions.
The GTM agent has no search tool, which enforces the dependency rule, but it also has no domain playbook.
A skill file gives it a stable method for positioning, messaging, distribution, and launch sequence.
This change is prompt-adjacent and must be measured against the Phase 4 and Phase 5 baselines.

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
- [ ] Compare the delegation result, the judge scores, the HTML reports, cost, and latency before and after.
- [ ] Add a regression task if the skill fixes a real failure.

### Files to touch

- `ai-product-launch-engine/skills/gtm-strategist/SKILL.md` (new)
- `ai-product-launch-engine/src/agents/gtm_strategist.py`
- `ai-product-launch-engine/src/prompts/subagents/gtm_strategist/v3.yaml` (new)
- `ai-product-launch-engine/evals/baselines/` (before and after record)
- `ai-product-launch-engine/tests/` for the skill wiring

### Done when

- [ ] The GTM subagent loads the skill.
- [ ] The delegation grader still passes.
- [ ] The GTM subagent still has no search tool.
- [ ] The before and after runs use the same task and the same base commit except for the skill and prompt change.
- [ ] The comparison record shows delegation, judge scores, cost, latency, and the HTML report paths.
- [ ] The skill change is accepted or rejected based on the comparison.

### Out of scope

- Do not change the market or customer prompts.
- Do not add a search tool to the GTM subagent.
- Do not skip the before and after comparison.

### Handoff

Write the skill path, the prompt version, and the before and after comparison in the session summary.

## Phase 7: Delegation fix comparison

Status: not started
Blocked by: a separate implementation of `delegation_fix.md`

### Goal

Compare the current supervisor delegation with the programmatic orchestration described in `delegation_fix.md`.
The comparison must show whether the new path makes the GTM dependency reliable without a quality or cost regression.

### Why

`delegation_fix.md` proposes parallel subagent calls with `arun` and `asyncio.gather`, then a join barrier, then the GTM call.
That design should make the GTM dependency more reliable than a turn-by-turn tool loop.
The eval suite must prove that claim with the same task and the same graders.
This phase does not implement the design.
It only compares it after a separate implementation exists.

### Preconditions

- [ ] Phase 6 is verified.
- [ ] Phase 1 accepts both the `task` tool event shape and the explicit delegation event shape.
- [ ] Phase 5 judge is calibrated enough to report scores.
- [ ] A separate branch implements `delegation_fix.md`.
- [ ] Both implementations use the same model and the same prompt versions.
- [ ] The new branch emits `delegation_started` and `delegation_finished` events for each subagent.

### Things to implement

- [ ] Confirm the new orchestration emits the delegation events from Phase 1.
- [ ] Run task 001 twice on the current supervisor.
- [ ] Run task 001 twice on the new orchestration.
- [ ] Generate the HTML report for all four runs.
- [ ] Compare these values:
  - Delegation pass or fail for each run.
  - GTM start time against both research finish times.
  - Pass@1 and pass^2.
  - Judge scores per dimension.
  - Tool calls, turns, tokens, latency, and cost.
- [ ] Add a comparison record under `evals/baselines/`.
- [ ] State whether the new path is accepted, rejected, or needs more trials.

### Files to touch

- `ai-product-launch-engine/evals/baselines/` (new comparison record)
- `ai-product-launch-engine/evals/RUNBOOK.md` if the commands change

### Done when

- [ ] Four runs exist, two per implementation.
- [ ] The delegation grader passes for both implementations.
- [ ] The comparison record names the commit or branch for each implementation.
- [ ] The comparison record shows delegation, quality, cost, and latency.
- [ ] The record states the decision.

### Out of scope

- Do not implement `delegation_fix.md` in this plan.
- Do not change the current supervisor to force a pass.
- Do not use different tasks or different graders for the two implementations.

### Handoff

Write the four run IDs, the comparison table, and the decision in the session summary.

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
