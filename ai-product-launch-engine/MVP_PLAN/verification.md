# MVP Verification

## How to use this file

Run the section for the phase you are about to close.
Do not close a phase until every command and every manual check passes.
Record the command output and the evidence path in the session summary.
If a check fails, fix the phase. Do not weaken the check.

Run all commands from `ai-product-launch-engine/`.

## Common checks

Run these for every phase.

```bash
uv run python -m unittest discover -s tests -v
uv run python -m evals.run_evals --validate-only --include-holdouts
git status --porcelain
```

Expected:

- The full test suite passes.
- The task validation returns `"valid": true`.
- `git status` shows only intended files.

Secret check:

```bash
git diff --cached | rg -n "AWS_SECRET_ACCESS_KEY|SLACK_BOT_TOKEN|DATABASE_URL|TAVILY_API_KEY=.+|password" || true
```

Expected: no real secret value appears.

## Phase 0: Audit and contracts

### Preconditions

- Phase 0 of `MVP_PLAN/PLAN.md` is the active phase.
- The repository is on a branch from `main`.

### Commands

```bash
uv run python -m unittest tests.test_contracts -v
uv run python -c "import src.contracts; print(sorted(src.contracts.__all__))"
uv run python -m unittest discover -s tests -v
```

### Expected result

- The contract tests pass.
- Every contract name imports.
- The full suite passes.
- A `fact` claim without evidence raises a validation error.

### Evidence to save

- Contract test output.
- The list of contract names.
- The README diff.

### Manual checks

- `README.md` no longer says the project is an early scaffold.
- `README.md` links to `MVP.md` and `MVP_PLAN/PLAN.md`.
- No Slack, FastAPI, PostgreSQL, or Design Agent code exists yet.
- The eval datasets are unchanged.

### Fail conditions

- A contract accepts invalid data.
- The README still describes missing behavior as current.
- Future-phase code is present.

## Phase 1: Structured research outputs

### Preconditions

- Phase 0 is verified.
- The baseline record in `Failures.md` is current.

### Commands

```bash
uv run python main.py --input tests/fixtures/launch_request.json --workspace-root /tmp/mvp-phase1
find /tmp/mvp-phase1/projects -type f -name "*.json" | sort
uv run python -m unittest tests.test_validation -v
uv run python -m unittest tests.test_reference_trial -v
uv run python -m evals.run_evals --validate-only --include-holdouts
uv run python -m evals.run_evals --task b2b_recruiting_meeting_assistant --agent-command "uv run python main.py" --html
```

### Expected result

- The run writes three JSON files:
  - `research/market_research.json`
  - `research/customer_research.json`
  - `strategy/gtm_strategy.json`
- Every file validates against its contract.
- The validation tests pass.
- The reference trial passes every grader.
- The eval run produces `summary.json` and `report.html`.
- `F-003`, `F-004`, `F-005`, `F-006`, and `O-001` are closed or reclassified in `Failures.md`.

### Evidence to save

- The three artifact paths.
- The validation output.
- The eval `summary.json` path.
- The `Failures.md` diff.

### Manual checks

- Each `fact` claim has at least one source URL.
- No Markdown research artifact is produced by the MVP path.
- The manifest includes `supervisor` in `agents_used`.
- `total_tokens` is greater than zero.
- The tool count is inside the task budget.

### Fail conditions

- A malformed artifact is accepted.
- The eval suite still grades removed Markdown paths.
- A fact claim has no source.
- The run continues after a validation error.

## Phase 2: Research workflow

### Preconditions

- Phase 1 is verified.
- Both JSON research artifacts validate.

### Commands

```bash
uv run python -m unittest tests.test_research_workflow -v
uv run python -m unittest tests.test_delegation_grader -v
```

### Expected result

- The concurrency test proves both research tasks run at the same time.
- The failure test proves one failed task stops the workflow.
- The invalid-output test proves bad JSON stops the workflow.
- The delegation grader proves GTM starts after both validated results.

### Evidence to save

- Test output.
- The transcript start and finish times for both research tasks.
- The task state records.

### Manual checks

- The two research start times overlap.
- No GTM event appears before both research finish events.
- A failed task has a clear error and a status.

### Fail conditions

- Research runs sequentially only.
- The workflow continues with one result.
- GTM starts early.

## Phase 3: Decision and guarded GTM

### Preconditions

- Phase 2 is verified.
- The task tracker records both research results.

### Commands

```bash
uv run python -m unittest tests.test_decision -v
uv run python -m unittest tests.test_gtm_guard -v
```

### Expected result

- Autonomous mode selects the recommended option.
- Ambient mode returns two options and a default.
- The timeout selects the default after eight seconds.
- The guard rejects GTM when research is missing.
- The guard rejects GTM when the decision is missing.
- The guard rejects GTM when approval is missing.
- A valid state runs GTM and validates `gtm_strategy.json`.

### Evidence to save

- Test output.
- The guard rejection messages.
- The timeout test output.

### Manual checks

- The timer is in backend code, not in a prompt.
- The supervisor calls the guarded workflow, not the GTM subagent directly.
- The decision is persisted through the storage interface.

### Fail conditions

- GTM runs before both research results validate.
- GTM runs before a decision exists.
- The timeout is simulated by the model.
- The guard can be bypassed by a prompt.

## Phase 4: Slack integration

### Preconditions

- Phase 3 is verified.
- A Slack development app exists.
- The required tokens are in the local environment.

### Commands

```bash
uv run python -m unittest tests.test_slack_app -v
uv run python -m unittest tests.test_slack_streaming -v
uv run python -m unittest tests.test_slack_approval -v
uv run python -m unittest tests.test_api -v
uv run python -m src.slack.app
```

### Expected result

- The command handler creates one project.
- The stream shows the final answer only.
- The button handler records one selection.
- Approval resumes the paused run.
- A duplicate event does not start a second workflow.
- An invalid signature is rejected.
- A local Slack sandbox run reaches delivery.

### Evidence to save

- Test output.
- Slack project ID and thread link.
- Screenshots of the progress messages and buttons.
- The duplicate-event test output.

### Manual checks

- The user starts the workflow from Slack only.
- The stream shows the final answer only, not raw subagent output.
- The progress messages arrive in order.
- The buttons work.
- The timeout selects the default.
- The approval button resumes the paused run.
- The launch pack and report arrive in the original thread.
- Every file shows a success or failure status.

### Fail conditions

- The workflow requires a terminal.
- Raw subagent or tool output appears in the stream.
- Approval does not resume the run.
- A duplicate event starts a second run.
- An unsigned request is accepted.
- A failed file is hidden.

## Phase 5: Persistence and reliability

### Preconditions

- Phase 4 is verified.
- Docker is available for local PostgreSQL.

### Commands

```bash
docker compose up -d postgres
uv run python -m unittest tests.test_db -v
uv run python -m unittest tests.test_state -v
uv run python -m unittest tests.test_restart -v
```

### Expected result

- The repository writes and reads each record type.
- Invalid state transitions are rejected.
- A restart resumes from the last committed state.
- A completed step does not run twice.
- A recoverable failure retries and records each attempt.

### Evidence to save

- Test output.
- The database schema.
- The restart test output.
- The retry log.

### Manual checks

- A project survives a process restart.
- A Slack interaction resumes the correct project.
- A duplicate event does not duplicate work.
- Logs include project ID, step, status, and error.

### Fail conditions

- State is lost on restart.
- A completed step runs twice.
- A retry loop is unbounded.
- A secret appears in a log.

## Phase 6: Deployment and public release

### Preconditions

- Phase 5 is verified.
- Production credentials and services exist.

### Commands

```bash
curl -fsS "$DEPLOYMENT_URL/health"
uv run python -m unittest discover -s tests -v
```

### Expected result

- The health check returns success.
- The full suite passes.
- Three different product ideas complete end to end.
- Each project returns the launch pack and report in Slack.

### Evidence to save

- Deployment URL.
- Three project IDs.
- Screenshots of the Slack deliveries.
- The README diff.
- The demo video link.
- The article link.

### Manual checks

- A new developer can follow the README and run the app.
- The architecture diagram matches the code.
- The Slack setup is complete.
- The environment variable list is complete.
- No secret is committed.

### Fail conditions

- A new developer cannot run the app from the README.
- A project fails end to end.
- A secret is committed.
- The demo does not show the launch pack and report.

## Deferred: Design Agent

Do not verify the Design Agent in this plan.
Its checks belong to the later plan.
Do not create `deliverables/assets/` or `asset_manifest.json` in V1.

## Phase evidence template

Record this for every phase.

```text
Phase:
Branch:
Commit:
Commands run:
Result:
Artifact paths:
Manual checks:
Known limitations:
Next phase ready: yes or no
```
