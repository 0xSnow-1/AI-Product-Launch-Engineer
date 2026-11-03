# Workspace Separation Plan

Result: split the product workspace from the eval run directory.
Product output goes to `workspace/projects/{project_slug}/`.
Eval artifacts go to `evals/runs/{run_id}/`.
The runner generates the run id, so no command needs a `<run_id>` placeholder.

## 1. Evidence

The first real run wrote this tree:

```text
workspace/evals/<run_id>/
├── report.html
├── summary.json
└── trials/b2b_recruiting_meeting_assistant/
    ├── grader_results.json
    ├── input.json
    ├── transcript.jsonl
    └── projects/b2b-recruiting-meeting-assistant/
```

Problems:

- `workspace/` holds eval artifacts, not only product output.
- The directory name is the literal text `<run_id>`. The user copied a placeholder from the RUNBOOK.
- Product artifacts and eval artifacts share one tree.

Root causes:

- `evals/run_evals.py` takes `--trial-root` and derives the report path from `trial_root.parent`.
- `evals/RUNBOOK.md` tells the user to pass `workspace/evals/$run_id/trials`.
- The RUNBOOK mixes shell variables (`$run_id`) with placeholders (`<run_id>`).
- `.gitignore` does not ignore generated runs, so `workspace/evals/` shows as untracked.

## 2. Target layout

```text
ai-product-launch-engine/
├── workspace/                                  # product output only
│   └── projects/{project_slug}/                # market.md, customers.md, gtm.md, blueprint.md, manifest.json, deliverable.zip
└── evals/
    ├── runs/                                   # generated, gitignored, dev only
    │   └── {run_id}/
    │       ├── summary.json
    │       ├── report.html
    │       └── trials/{task_id}/
    │           ├── input.json
    │           ├── transcript.jsonl
    │           ├── grader_results.json
    │           ├── fixtures/
    │           └── projects/{project_slug}/    # isolated trial output
    ├── datasets/
    ├── fixtures/
    └── reference/
```

Rules:

- `workspace/` contains only `projects/`. No `evals/` directory under it.
- Every eval run lives under `evals/runs/`.
- Each trial keeps its own physical root, so no trial writes outside its root.
- Generated runs are not committed.

## 3. Prerequisite

Land PR #16 first.

Evidence: the first run wrote `project_slug` into `input.json` and wrote `blueprint.md` under the trial root.
Only the Phase 3 branch does that.
`main` still calls `create_blueprint(agent, project_slug, output)` and writes to the absolute path `/projects/...`.
On this host `/projects` does not exist, so a run on `main` will not produce `blueprint.md`, `manifest.json`, or `deliverable.zip`.

Do the separation work on top of the merged Phase 3 code.

## 4. Phase 0: clear the stray run

1. Move `workspace/evals/<run_id>` to `evals/runs/20261102-230937-b2b_recruiting_meeting_assistant`.
2. Keep the files for later inspection.
3. Delete the moved directory after the baseline review if it is not needed.
4. Confirm `workspace/` then contains no `evals/` directory.

## 5. Phase 1: update the contract

Change `evals/spec.md` in its own pull request.

1. Define the product root: `workspace/projects/{project_slug}/`.
2. Define the eval run root: `evals/runs/{run_id}/trials/{task_id}/`.
3. State that a trial's physical root is `evals/runs/{run_id}/trials/{task_id}/`.
4. State that no trial writes outside that root.
5. State that `workspace/` is not used by the eval runner.
6. Keep the six required artifact paths unchanged under the project root.

Also update these files that repeat the old path:

- `evals/decisions.md` line 21 and 24.
- `EVAL_PLAN/PLAN.md` line 21, 465, and 490.

## 6. Phase 2: change the runner

Edit `evals/run_evals.py`.

1. Add `--runs-root` with default `evals/runs`.
2. Add `--run-id` with no default.
3. Generate the run id when it is absent:
   - UTC timestamp `%Y%m%d-%H%M%S`.
   - Add `-{task_id}` for one selected task.
   - Add `-dev-suite` for the non-holdout suite.
   - Add `-holdouts` when `--include-holdouts` is set.
4. Derive `run_dir = runs_root / run_id` and `trials_root = run_dir / "trials"`.
5. Default `--report` to `run_dir / "summary.json"`.
6. Write the HTML report to `run_dir / "report.html"`.
7. Fail with a clear error when `run_dir` already exists.
8. Print `Run directory: <path>` to stdout before the run.
9. Remove `--trial-root`. Migrate the one caller in `tests/test_evaluation_harness.py`.

The agent still receives `LAUNCH_ENGINE_TRIAL_ROOT` and writes to `trials/{task_id}/projects/{project_slug}/`.
`main.py` needs no change.

## 7. Phase 3: clean the repository

1. Remove the tracked empty file `workspace/__init__.py`.
2. Add to the root `.gitignore`:
   - `ai-product-launch-engine/workspace/`
   - `ai-product-launch-engine/evals/runs/`
3. Confirm `git status --short` shows no generated run files.

## 8. Phase 4: update the docs

1. `evals/RUNBOOK.md` sections 4 through 7:
   - Remove every `--trial-root` and `--report` argument.
   - Remove every `<run_id>` placeholder.
   - Show the short command.
   - List the files under `evals/runs/{run_id}/`.
2. `EVAL_PLAN/verification.md`:
   - Replace every `workspace/evals/...` path with `evals/runs/...`.
   - Replace `--trial-root` calls with the new flags.
3. `evals/report_html.py` help text:
   - Keep `--run` and `--output`.
   - Confirm the default output is `<run_dir>/report.html`.

New single-task command:

```bash
uv run python -m evals.run_evals \
  --task b2b_recruiting_meeting_assistant \
  --agent-command "uv run python main.py" \
  --html
```

New suite command:

```bash
uv run python -m evals.run_evals \
  --agent-command "uv run python main.py" \
  --html
```

## 9. Phase 5: tests

1. Update `tests/test_evaluation_harness.py` to use `--runs-root` and `--run-id`.
2. Add a test for the default run id format.
3. Add a test that `workspace/` is untouched by the runner.
4. Add a test that an existing run directory is rejected.
5. Add a test that the default report path is `evals/runs/{run_id}/summary.json`.
6. Keep the executor and grader tests. They use temporary roots and do not depend on the new layout.

## 10. Verification

Run these commands from `ai-product-launch-engine`.

```bash
uv run python -m unittest discover -s tests -v
uv run python -m evals.run_evals --validate-only --include-holdouts
```

Check the layout without a model call:

```bash
uv run python -m evals.run_evals \
  --task b2b_recruiting_meeting_assistant \
  --run-id layout-check \
  --agent-command "python -c 'import os, pathlib; pathlib.Path(os.environ[\"LAUNCH_ENGINE_TRIAL_ROOT\"], \"projects\", \"b2b-recruiting-meeting-assistant\").mkdir(parents=True, exist_ok=True)'"
```

Then check:

```bash
find workspace -maxdepth 3 | sort
find evals/runs/layout-check -maxdepth 4 | sort
git status --short
```

Expected results:

- `workspace/` has no `evals/` directory.
- The run appears only under `evals/runs/layout-check/`.
- `git status` shows no generated run files.

## 11. Risks

- This changes the eval contract. Do Phase 1 in its own pull request.
- The HTML report reads `run_dir/trials/{task_id}`. The new layout keeps that shape, so the report code needs no path change.
- Do not commit `evals/runs/` or `workspace/projects/`.
- Keep the holdout set out of prompt tuning.

## 12. Out of scope

- Baseline scoring and metric analysis.
- Artifact content defects, such as `customers.md` written at the project root instead of `research/customers.md`.
- Prompt and grader tuning.
