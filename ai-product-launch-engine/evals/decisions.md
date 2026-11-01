# Evaluation Decisions

## Why I use one JSON file per task

I want each task to be easy to read in a pull request.
I store one formatted JSON object in each task file.
I group files by capability, holdout, and regression use.
The runner finds the files automatically.
Adding a task must not require a runner change.

## What the deterministic evaluator does

I validate task data before I grade a trial.
I check artifact paths, Markdown headings, citations, the manifest, the ZIP archive, and placeholders.
These checks use only local files.
They do not depend on a model, a search provider, or a network connection.

## What a real run must save

I will give every run an identifier.
I will save its files under `workspace/evals/{run_id}/`.

```text
workspace/evals/{run_id}/
├── summary.json
└── trials/{task_id}/
    ├── input.json
    ├── transcript.jsonl
    ├── grader_results.json
    └── projects/{project_slug}/
```

The transcript will contain agent messages, tool calls, tool results, errors, token use, and timestamps.
The grader results will explain each pass or failure.
The summary will compare all trials in the run.

## Current execution boundary

The runner validates datasets, creates an isolated trial, and grades the trial folder.
It runs a real agent only when the caller supplies `--agent-command`.
The runner does not select a provider or call a model by itself.

The runner passes the input, workspace, fixtures, and transcript path through
`LAUNCH_ENGINE_*` environment variables.
The supervisor records model and tool callback events at the supplied transcript path.

## Quality scoring

Code graders enforce required outputs.
A later model judge will score research quality, evidence quality, and GTM coherence.
I will calibrate that judge against human labels before I use it as a release gate.
