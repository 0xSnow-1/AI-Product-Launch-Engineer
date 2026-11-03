# MVP Plan

Status: planning only.
No phase is complete until `MVP_PLAN/verification.md` passes for that phase.
Source of truth: `MVP.md` at the repository root.

Scope decision: this V1 defers the Design Agent and the four visual assets.
The V1 end goal is a working Slack application for research, decision, GTM, and delivery.
The Design Agent integration is planned separately after its research is complete.

## Purpose

This plan turns the current command-line launch engine into the MVP in `MVP.md`.
The MVP is a Slack application that runs a supervised agent workflow and returns a Launch Decision Pack.
The Design Agent and the four visual assets are deferred.
The plan is written for one coding session per phase.
Each phase must leave the repository in a verified state.

## Operating rules

- Implement one phase per session and per pull request.
- Read the phase, `MVP.md`, and `MVP_PLAN/verification.md` before you write code.
- Do not start a phase until the previous phase is verified.
- Do not implement future phases early, even when the code is easy.
- Do not integrate the Design Agent in V1. It is deferred.
- Use `example.md` only as Slack reference input. Verify every API against the current docs.
- Keep the eval suite in `EVAL_PLAN/` green.
- Fix the open failures in `Failures.md` when a phase touches the same code.
- Do not add Next.js, Streamlit, a coding agent, or extra specialist agents.
- Do not put critical workflow rules only in a prompt.
- Validate external data at the boundary with Pydantic.
- Keep one concern per pull request.
- Do not commit `.env`, secrets, database files, or generated artifacts.
- Update `README.md` and `MVP_PLAN/verification.md` when behavior or commands change.
- Record commands and evidence in the session handoff.

## Current state

The repository has a working command-line agent system.
It does not have the MVP application.

Implemented:

- Supervisor Deep Agent with `TodoListMiddleware`.
- Three subagents: `market_researcher`, `customer_researcher`, `gtm_strategist`.
- Versioned YAML prompts.
- Shared `FilesystemBackend` with virtual paths.
- Markdown artifacts: `research/market.md`, `research/customers.md`, `strategy/gtm.md`, `blueprint.md`.
- Manifest and zip packaging.
- Eval harness with 20 tasks and 8 deterministic graders.
- Unit suite (89 tests after Phase 0).
- CI workflow that runs tests and task validation.
- MVP data contracts in `src/contracts.py` (Phase 0).
- Phase 0 configuration fields: Slack tokens, `DATABASE_URL`, `ARTIFACT_ROOT`.

Missing:

- Structured JSON research and strategy outputs.
- Async research with task tracking.
- Strategic decision modes and the eight-second timeout.
- Backend-enforced GTM guard.
- Slack application.
- FastAPI service.
- PostgreSQL persistence.
- `launch_pack.json` and a human-readable launch report.
- Deployment and public release material.

Deferred to a later plan:

- Design Agent client.
- Four visual assets.
- `asset_manifest.json`.

Open eval failures that Phase 1 must close:

- `F-003`: source citations are zero.
- `F-004`: required headings do not match.
- `F-005`: manifest omits `supervisor`.
- `F-006`: tool budget is exceeded.
- `O-001`: token metrics are always zero.

## Canonical paths

Use one project root per project.

```text
projects/{project_id}/
├── research/
│   ├── market_research.json
│   └── customer_research.json
├── strategy/
│   └── gtm_strategy.json
└── deliverables/
    ├── launch_pack.json
    └── launch_report.md
```

The virtual path root must match the configured `FilesystemBackend` root.
Do not use `/workspace/research/`.

The Design Agent later adds `deliverables/assets/` and `asset_manifest.json`.
Do not create those paths in V1.

## Phase order

| Phase | Name | Main output |
| --- | --- | --- |
| 0 | Audit and contracts | Current-state audit, Pydantic contracts, settings, README status |
| 1 | Structured research outputs | JSON research and strategy artifacts, migrated eval suite |
| 2 | Research workflow | Async research with tracking, validation, and failure handling |
| 3 | Decision and guarded GTM | Autonomous and ambient decisions, approval gate, GTM guard |
| 4 | Slack integration | End-to-end Slack workflow with buttons and file delivery |
| 5 | Persistence and reliability | PostgreSQL state, restart recovery, retries, idempotency |
| 6 | Deployment and release | Deployed demo, README, diagrams, video, article |

The Design Agent integration is deferred.
See the Deferred section at the end of this plan.

## Phase 0: Audit and contracts

### Goal

Freeze the MVP data contracts and document the real current state.
Make every later phase build on one shared schema.

### Why

The current code uses Markdown artifacts and loose dictionaries.
The MVP needs validated JSON between agents, the application, the database, and Slack.
A schema change later would touch every phase.
Define the contracts first.

### Things to implement

- [x] Write the current-state audit in this file.
  - List implemented features.
  - List missing features.
  - List the open failures from `Failures.md`.
- [x] Add `src/contracts.py`.
  - Add `EvidenceRef`: title, url, retrieved_at, claim_ids.
  - Add `Claim`: id, text, kind (`fact`, `interpretation`, `assumption`, `recommendation`), evidence_refs.
  - Add `MarketResearch`: project_id, generated_at, summary, competitors, market_opportunities, trends, claims, assumptions, limitations.
  - Add `CustomerResearch`: project_id, generated_at, segments, personas, pain_points, buying_triggers, ideal_customer_profile, claims, assumptions, limitations.
  - Add `GTMStrategy`: project_id, generated_at, positioning, differentiation, target_segments, pricing_hypotheses, channels, launch_roadmap, risks, assumptions, claims.
  - Add `StrategicOption`: id, name, thesis, target_segment, differentiation, risks, evidence_refs.
  - Add `StrategicDecision`: mode, selected_option_id, options, decided_at, decided_by, approval_status.
  - Add `LaunchPack`: project_id, idea, market, customer, gtm, decision, evidence_index.
  - Add `ProjectRecord`: project_id, idea, audience, constraints, mode, status, created_at, updated_at.
  - Export every public contract in `__all__`.
- [x] Add `src/config.py` fields.
  - `slack_bot_token`, `slack_app_token`, `slack_signing_secret`.
  - `database_url`.
  - `artifact_root`.
- [x] Add `tests/test_contracts.py`.
  - Valid examples parse.
  - Missing required fields fail.
  - A claim with kind `fact` and no evidence fails.
- [x] Update `README.md`.
  - Replace the outdated "early scaffold" status.
  - Link to `MVP.md` and `MVP_PLAN/PLAN.md`.
  - Document the current command-line behavior only.
- [x] Update `ai-product-launch-engine/README.md`.
  - Add the contracts module and the MVP plan link.
- [x] Update `.env.example`.
  - Add the new configuration keys with empty values.

### Files to touch

- `ai-product-launch-engine/MVP_PLAN/PLAN.md`
- `ai-product-launch-engine/MVP_PLAN/verification.md`
- `ai-product-launch-engine/src/contracts.py` (new)
- `ai-product-launch-engine/src/config.py`
- `ai-product-launch-engine/tests/test_contracts.py` (new)
- `README.md`
- `ai-product-launch-engine/README.md`
- `ai-product-launch-engine/.env.example`

### Done when

- [x] `uv run python -m unittest tests.test_contracts -v` passes.
- [x] `uv run python -m unittest discover -s tests` passes.
- [x] Every contract rejects an invalid example in a test.
- [x] The README status matches the code.
- [x] No phase 1 or later behavior is implemented.

### Out of scope

- Do not change agent outputs.
- Do not add Slack, FastAPI, PostgreSQL, or the Design Agent.
- Do not change the eval datasets.

### Handoff

Record the contract names, the test command, and the README changes in the session summary.

## Phase 1: Structured research outputs

### Goal

Make the three specialist agents write validated JSON artifacts.
Migrate the eval suite to the JSON contract.
Close the open eval failures.

### Why

The MVP needs structured data for the decision step, the database, and Slack delivery.
Markdown cannot be validated or passed safely between services.
The eval suite must grade the same contract that the product uses.

### Things to implement

- [ ] Add `tests/fixtures/launch_request.json`.
  - One valid request for a CLI run.
- [ ] Add prompt versions that write JSON.
  - `src/prompts/subagents/market_researcher/v3.yaml`
  - `src/prompts/subagents/customer_researcher/v3.yaml`
  - `src/prompts/subagents/gtm_strategist/v3.yaml`
  - `src/prompts/supervisor/v4.yaml`
- [ ] Make each specialist write the canonical path.
  - `market_researcher` writes `research/market_research.json`.
  - `customer_researcher` writes `research/customer_research.json`.
  - `gtm_strategist` writes `strategy/gtm_strategy.json`.
- [ ] Require source references in the JSON.
  - Each `fact` claim has at least one `EvidenceRef`.
  - Each `EvidenceRef` has a title and an HTTP or HTTPS URL.
  - This closes `F-003`.
- [ ] Add `src/workflows/validation.py`.
  - Load one artifact from the project root.
  - Parse it with the matching Pydantic model.
  - Return a typed result or a clear error.
- [ ] Validate every specialist output before the supervisor accepts it.
  - Reject a missing, malformed, or incomplete artifact.
  - Do not continue with partial data.
- [ ] Add `src/metrics.py` fix.
  - Always include `supervisor` in `agents_used`.
  - This closes `F-005`.
- [ ] Capture token usage from model callbacks.
  - Write a structured `usage` field in the transcript event.
  - This closes `O-001`.
- [ ] Set a realistic tool budget.
  - Raise `max_tool_calls` to 80, or reduce repeated reads.
  - Record the decision in `Failures.md`.
  - This closes `F-006`.
- [ ] Update the eval suite to JSON.
  - `evals/spec.md`: artifact paths and JSON fields.
  - `evals/datasets/**/*.json`: expected artifacts.
  - `evals/evaluators.py`: replace heading checks with schema checks.
  - `evals/reference/b2b_recruiting_meeting_assistant/`: JSON reference trial.
  - `tests/test_reference_trial.py`.
  - This closes `F-004`.
- [ ] Add `tests/test_validation.py`.
  - Valid JSON passes.
  - Missing field fails.
  - A `fact` claim without evidence fails.

Phase 1 is the largest phase.
Do not leave the eval suite grading removed paths.
If the change is too large for one session, split it into 1A (JSON outputs) and 1B (eval migration).
Both parts must merge before Phase 2 starts.

### Files to touch

- `ai-product-launch-engine/src/prompts/subagents/*/v3.yaml` (new)
- `ai-product-launch-engine/src/prompts/supervisor/v4.yaml` (new)
- `ai-product-launch-engine/src/workflows/validation.py` (new)
- `ai-product-launch-engine/src/metrics.py`
- `ai-product-launch-engine/src/agents/*.py`
- `ai-product-launch-engine/main.py`
- `ai-product-launch-engine/evals/spec.md`
- `ai-product-launch-engine/evals/datasets/`
- `ai-product-launch-engine/evals/evaluators.py`
- `ai-product-launch-engine/evals/reference/`
- `ai-product-launch-engine/tests/`
- `Failures.md`

### Done when

- [ ] One CLI run writes three valid JSON artifacts.
- [ ] `uv run python -m unittest discover -s tests` passes.
- [ ] `uv run python -m evals.run_evals --validate-only --include-holdouts` returns `"valid": true`.
- [ ] The reference trial passes every grader.
- [ ] `F-003`, `F-004`, `F-005`, `F-006`, and `O-001` are closed or reclassified.
- [ ] A malformed artifact stops the run with a clear error.

### Out of scope

- Do not add async execution.
- Do not add the decision step.
- Do not add Slack or the Design Agent.

### Handoff

Record the artifact paths, the schema versions, the eval result, and the updated failure records.

## Phase 2: Research workflow

### Goal

Run the two research specialists asynchronously and track their state.
Validate both results before any downstream step.

### Why

The MVP requires parallel research.
The current delegation path does not prove concurrency or durable task state.

### Things to implement

- [ ] Add `src/workflows/research.py`.
  - Start market research and customer research concurrently.
  - Return task IDs and initial status.
  - Wait for both tasks.
  - Validate both JSON artifacts.
- [ ] Add a task tracker.
  - State: `pending`, `running`, `succeeded`, `failed`, `invalid`.
  - Store the result path and the error.
- [ ] Handle failures.
  - One failed research task must not block the other.
  - The workflow must not continue with one result.
  - Retry a recoverable failure once.
- [ ] Update the supervisor prompt and tools.
  - The supervisor starts both tasks.
  - The supervisor reads only validated results.
- [ ] Add a delegation grader check.
  - The two research tasks overlap in time.
  - GTM starts after both results are validated.
- [ ] Add tests.
  - Both tasks succeed.
  - One task fails.
  - One task returns invalid JSON.
  - No GTM call before both results.

### Files to touch

- `ai-product-launch-engine/src/workflows/research.py` (new)
- `ai-product-launch-engine/src/workflows/task_tracker.py` (new)
- `ai-product-launch-engine/src/agents/supervisor.py`
- `ai-product-launch-engine/src/prompts/supervisor/v4.yaml`
- `ai-product-launch-engine/evals/evaluators.py`
- `ai-product-launch-engine/tests/`

### Done when

- [ ] Both research tasks run concurrently in a test.
- [ ] One failure produces a clear workflow error.
- [ ] Invalid output stops the workflow.
- [ ] The delegation grader passes the concurrency check.
- [ ] The full test suite passes.

### Out of scope

- Do not add strategic decisions.
- Do not add Slack.

### Handoff

Record the task state model, the concurrency test, and the failure cases.

## Phase 3: Decision and guarded GTM

### Goal

Implement both execution modes and make the GTM guard a backend rule.

### Why

The MVP must support Full Autonomous Mode and Ambient Mode.
The GTM Strategist must never run before research and a decision are complete.
A prompt alone cannot enforce this.

### Things to implement

- [ ] Add `src/workflows/decision.py`.
  - Build two `StrategicOption` values from validated research.
  - Autonomous mode selects the recommended option.
  - Ambient mode returns both options and a default.
- [ ] Add the eight-second timeout.
  - Use backend logic and a monotonic clock.
  - On timeout, select the default option.
  - Do not simulate the timer in a prompt.
- [ ] Add `src/tools/gtm_guard.py`.
  - Accept a project ID.
  - Check both research results exist and validate.
  - Check a decision exists and is approved.
  - Reject any other state.
- [ ] Add `src/workflows/gtm.py`.
  - Call the guard first.
  - Pass the idea, both research results, and the decision.
  - Validate `gtm_strategy.json`.
- [ ] Add tests.
  - Autonomous mode proceeds.
  - Ambient mode selects the default on timeout.
  - Premature GTM is rejected.
  - A missing approval is rejected.
- [ ] Update the supervisor prompt.
  - It must not call GTM directly.
  - It must call the guarded workflow.

### Files to touch

- `ai-product-launch-engine/src/workflows/decision.py` (new)
- `ai-product-launch-engine/src/workflows/gtm.py` (new)
- `ai-product-launch-engine/src/tools/gtm_guard.py` (new)
- `ai-product-launch-engine/src/contracts.py`
- `ai-product-launch-engine/src/prompts/supervisor/v4.yaml`
- `ai-product-launch-engine/tests/`

### Done when

- [ ] Both modes pass their tests.
- [ ] The timeout test uses a fake clock.
- [ ] Premature GTM is rejected with a clear error.
- [ ] The full test suite passes.

### Out of scope

- Do not add Slack buttons.
- The decision service exposes a plain interface that Phase 4 can call.

### Handoff

Record the guard checks, the timeout behavior, and the rejection cases.

## Phase 4: Slack integration

### Goal

Let a user run the full workflow through Slack.

### Why

Slack is the MVP user interface.
A command-line run is not the MVP.

### Things to implement

- [ ] Add the Slack application.
  - Slack Bolt for Python.
  - Socket Mode for local development.
  - Request signature verification.
- [ ] Add a project creation command.
  - Accept the idea, audience, constraints, and mode.
  - Create a project ID and workspace.
  - Start the workflow.
- [ ] Support the current Slack agent experience.
  - Handle `app_mention` for new requests.
  - Handle `app.message` for thread replies.
  - Ignore messages from bots.
  - Handle `app_home_opened` for the Messages tab.
- [ ] Stream progress.
  - Use `say_stream` and `stream_mode="messages"`.
  - Filter chunks by `meta` or node name.
  - Do not show raw subagent or tool output.
  - Use `set_status` for status text. This needs the `assistant:write` scope.
- [ ] Post progress updates.
  - Project created.
  - Research started.
  - Research complete.
  - Decision required.
  - GTM complete.
  - Pack ready.
- [ ] Add Ambient Mode buttons.
  - Two options.
  - Eight-second countdown in backend code.
  - Default selection on timeout.
- [ ] Add approval handling.
  - Use `interrupt_on` and a checkpointer.
  - Detect a paused run with `agent.get_state(cfg).next`.
  - Resume with `Command(resume=...)`.
  - Verify the payload shape against the current Deep Agents HITL docs.
- [ ] Deliver files.
  - Upload `launch_pack.json` and `launch_report.md` to the original thread.
  - Show success or failure for each file.
- [ ] Handle retries and duplicates.
  - Deduplicate by Slack event ID.
  - Make handlers idempotent.
- [ ] Add tests.
  - Command handler.
  - Thread reply handler.
  - Bot message ignored.
  - Streaming filter.
  - Button handler.
  - Approval resume.
  - Duplicate event.
  - Signature rejection.
- [ ] Record the reference inputs.
  - `example.md` gives the streaming and approval skeleton.
  - The Slack sample app `slack-samples/bolt-python-support-agent` gives the listener layout.
  - Check both against the current library versions.

### Files to touch

- `ai-product-launch-engine/src/slack/app.py` (new)
- `ai-product-launch-engine/src/slack/handlers.py` (new)
- `ai-product-launch-engine/src/slack/blocks.py` (new)
- `ai-product-launch-engine/src/api/app.py` (new)
- `ai-product-launch-engine/pyproject.toml`
- `ai-product-launch-engine/tests/`

### Done when

- [ ] A local Slack sandbox run completes the workflow.
- [ ] The stream shows the final answer only, not raw subagent output.
- [ ] The button timeout selects the default.
- [ ] Approval resumes the paused run.
- [ ] A duplicate event does not start a second workflow.
- [ ] The full test suite passes.
- [ ] `README.md` documents the Slack setup.

### Out of scope

- Do not add PostgreSQL.
- Use an in-memory store with the Phase 5 interface.

### Handoff

Record the Slack app configuration, the manual run, the stream filter, the approval resume, and the idempotency test.

## Phase 5: Persistence and reliability

### Goal

Persist project state and survive restarts.

### Why

Slack interactions arrive as separate events.
A restart must not lose a project or repeat a completed step.

### Things to implement

- [ ] Add PostgreSQL.
  - `docker compose` for local development.
  - Schema migration.
- [ ] Add `src/db/models.py` and `src/db/repository.py`.
  - Projects.
  - Execution states.
  - Approvals.
  - Task statuses.
  - Asset records.
- [ ] Add a workflow state machine.
  - Allowed transitions.
  - Reject invalid transitions.
- [ ] Add restart recovery.
  - Resume from the last committed state.
  - Do not rerun completed steps.
- [ ] Add retries.
  - Retry recoverable provider and network errors.
  - Record each attempt.
- [ ] Add logs.
  - Project ID.
  - Step.
  - Status.
  - Error.
- [ ] Add tests.
  - Repository tests.
  - Restart test.
  - Duplicate event test.
  - Invalid transition test.

### Files to touch

- `ai-product-launch-engine/src/db/` (new)
- `ai-product-launch-engine/src/workflows/state.py` (new)
- `ai-product-launch-engine/docker-compose.yml` (new)
- `ai-product-launch-engine/pyproject.toml`
- `ai-product-launch-engine/.env.example`
- `ai-product-launch-engine/tests/`

### Done when

- [ ] State survives a process restart in a test.
- [ ] A completed step does not run twice.
- [ ] A recoverable failure retries and records the attempt.
- [ ] The full test suite passes.

### Out of scope

- Do not add billing or multi-user permissions.

### Handoff

Record the schema, the state machine, and the restart evidence.

## Phase 6: Deployment and public release

### Goal

Ship a working public demonstration.

### Why

The MVP definition of success includes a deployed demo, a useful README, and a recorded walkthrough.

### Things to implement

- [ ] Deploy the Python backend.
- [ ] Deploy the Slack application.
- [ ] Configure PostgreSQL and artifact storage.
- [ ] Configure production environment variables.
- [ ] Run three complete end-to-end projects.
- [ ] Fix critical workflow and delivery issues.
- [ ] Rewrite `README.md`.
  - What the product does.
  - Architecture diagram.
  - Slack setup.
  - Local setup.
  - Deployment.
  - Limitations.
- [ ] Add workflow and architecture diagrams.
- [ ] Record a demonstration video.
- [ ] Publish the first technical article.

### Files to touch

- `README.md`
- `ai-product-launch-engine/README.md`
- `ai-product-launch-engine/Dockerfile` (new)
- `ai-product-launch-engine/docker-compose.yml`
- `docs/` (new)

### Done when

- [ ] The deployed app completes three different product ideas.
- [ ] A new developer can follow the README and run the app.
- [ ] The launch pack and report arrive in Slack for each project.
- [ ] The demo video and article are published.
- [ ] No secret is committed.

### Out of scope

- Do not add analytics dashboards.
- Do not add marketing campaign execution.

### Handoff

Record the deployment URLs, the three project IDs, and the release links.

## Deferred: Design Agent integration

The Design Agent is out of scope for V1.
It stays in `MVP.md` section 3.5 and `MVP.md` Phase 5.
Plan it after the V1 Slack workflow is deployed and stable.

When it is planned, it must:

- Run as a separate visual-production service.
- Receive validated structured data and explicit briefs.
- Produce four assets: competitor positioning map, customer segmentation infographic, GTM roadmap, and executive opportunity report.
- Return files and `asset_manifest.json`.
- Never invent market statistics, competitors, or research findings.
- Store final assets separately from the temporary agent workspace.

Add `deliverables/assets/` and `asset_manifest.json` only in that later plan.

## V1 success criteria

V1 is complete when:

- [ ] A user can start a project through Slack.
- [ ] The two research specialists run in parallel and return validated JSON.
- [ ] The supervisor builds strategic alternatives.
- [ ] Full Autonomous Mode proceeds without approval.
- [ ] Ambient Mode handles selection and the eight-second timeout.
- [ ] GTM cannot run before both research results and a decision.
- [ ] The GTM strategy is structured and validated.
- [ ] The launch pack and report reach the user in Slack.
- [ ] Project state and approvals survive a restart.
- [ ] Three different product ideas complete end to end.
- [ ] A new developer can run the app from the README.
- [ ] No secret is committed.

The four visual assets are not part of V1 success.
They belong to the deferred Design Agent plan.

## Documentation updates

Update these files when the related phase lands.

| File | Phase | Change |
| --- | --- | --- |
| `README.md` | 0, 4, 6 | Current status, Slack setup, architecture, deployment |
| `ai-product-launch-engine/README.md` | 0, 6 | Contracts, run commands, MVP plan link |
| `.env.example` | 0, 4, 5 | Slack, database, artifact storage |
| `MVP_PLAN/verification.md` | every phase | Commands and expected results |
| `Failures.md` | 1 | Close or reclassify the open failures |
| `evals/RUNBOOK.md` | 1 | JSON artifact paths and commands |

## Phase completion protocol

Use this protocol for every phase.

1. Read the phase and the matching section in `MVP_PLAN/verification.md`.
2. Confirm the previous phase is verified.
3. Implement only that phase.
4. Run the narrow tests first.
5. Run the full local suite.
6. Run the phase verification commands.
7. Record the evidence in the session summary.
8. Open a pull request with the phase name.
9. Do not start the next phase until the pull request is reviewed or merged.

## Definition of done for every phase

- [ ] The behavior works through the closest real surface.
- [ ] The phase tests pass.
- [ ] The full local suite passes.
- [ ] `MVP_PLAN/verification.md` passes for the phase.
- [ ] The docs match the code.
- [ ] The eval suite still passes.
- [ ] No secrets or generated artifacts are committed.
- [ ] The pull request body states what was verified and what was not.
