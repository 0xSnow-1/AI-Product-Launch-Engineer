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

## Current limit

The current runner validates datasets and grades completed trial folders.
It does not run the supervisor yet.
The next runtime change must add trial execution and transcript capture.

## Quality scoring

Code graders enforce required outputs.
A later model judge will score research quality, evidence quality, and GTM coherence.
I will calibrate that judge against human labels before I use it as a release gate.
