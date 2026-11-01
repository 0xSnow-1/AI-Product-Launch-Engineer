# Eval Golden Reference

A practical reference for designing evals before product code.
This file is based on Anthropic's article "Demystifying evals for AI agents".
It also uses lessons from the AI Product Launch Engineer repository.

Use this file when you start a new agent project.
Use it when you add a new capability to an existing agent.
Use it when you review an eval suite and need a quality checklist.
Do not read it once and forget it.

Source:
https://www.anthropic.com/research/demystifying-evals-for-ai-agents

---

## 1. The one rule

Define success before you write product code.
Write the eval artifacts before you write the agent.
The eval harness is test code.
It comes before product code, not after it.

"Evals first" does not mean "no code first".
It means:

1. Write the task contract.
2. Write the tasks.
3. Write the reference outputs.
4. Write the graders.
5. Write the harness.
6. Run the harness against a stub.
7. Only then write the product code.

### 1.1 What counts as product code

Product code:

- Prompts.
- Agent logic.
- Tool wiring.
- Delegation.
- Packaging.
- UI.

Eval code:

- Task definitions.
- Graders.
- Runner.
- Reports.

The eval code is allowed before product code.
The product code is not.

### 1.2 Why this order works

A task contract forces you to define success.
A reference output proves the task is solvable.
A grader proves the reference output passes.
A red baseline proves the harness can fail.
Only then can product code make the baseline green.

If the stub passes, the graders are broken.
If the reference output fails, the task is broken.
If the harness cannot fail, it is not an eval.

### 1.3 The first artifact is the task contract

The first artifact is not a dataset.
The first artifact is a written task contract.

A dataset without a rubric is a quiz.
A rubric without artifact checks is incomplete for an agent.
A judge without calibration is a vibe check.
A baseline without a gate is a report, not an eval.
A gate without a failure taxonomy is a blunt instrument.

---

## 2. The 20/80 concepts

These are the concepts that carry most of the value.
Learn these first.

| Concept | Plain meaning | Why it matters |
| --- | --- | --- |
| **Task** | A single test with defined inputs and success criteria. | It is the unit of evaluation. |
| **Trial** | One attempt at a task. | Agents vary between runs. |
| **Grader** | Logic that scores one aspect of performance. | One task can have many graders. |
| **Transcript** | The full record of a trial. | It shows what the agent did, not only what it said. |
| **Outcome** | The final state of the environment. | A chat message is not proof that work happened. |
| **Harness** | The system that runs tasks and records results. | It must isolate trials and capture evidence. |
| **Suite** | A group of tasks with a shared goal. | It is the unit you maintain and gate. |
| **Code-based grader** | A deterministic check such as file existence or schema validation. | Use it first. It is fast, cheap, and stable. |
| **Model-based grader** | An LLM scores output with a rubric or pairwise comparison. | Use it for research quality, coherence, and actionability. |
| **Human grader** | A domain expert labels a sample. | Use it to calibrate the model judge. |
| **Capability eval** | A test of what the agent can do. | It should start with a low pass rate. |
| **Regression eval** | A test of what the agent must not break. | It should stay near 100 percent. |
| **Groundedness** | Each claim maps to a source or an explicit assumption. | Research agents fail by inventing evidence. |
| **Coverage** | The output includes the key facts a good answer must contain. | It prevents thin or incomplete research. |
| **Source quality** | The sources are authoritative, not just the first results. | It separates research from search. |
| **pass@k** | The chance of at least one success in k trials. | Use it for capability. |
| **pass^k** | The chance that all k trials succeed. | Use it for release reliability. |
| **Eval saturation** | The agent passes every solvable task. | The suite no longer guides improvement. |
| **Eval-driven development** | Build evals to define planned capabilities, then iterate. | This is the practical version of "evals first". |

The article's strongest practical lesson is this:
Grade what the agent produced, not the exact path it took.

Rigid step-by-step grading is brittle.
Agents find valid paths you did not anticipate.
Check outcomes and coarse process requirements.
Do not require an exact order of tool calls.

For a multi-agent system, that means:

- Check that all required artifacts exist.
- Check that all required workstreams ran.
- Do not require a specific delegation order.
- Set a tool-call budget, not a tool-call script.

---

## 3. Reading map for the article

Read in this order.

| Section | Priority | Why read it |
| --- | --- | --- |
| **The structure of an evaluation** | P0 | It gives you the vocabulary: task, trial, grader, transcript, outcome, harness, suite. |
| **How to evaluate AI agents -> Types of graders for agents** | P0 | It tells you when to use code, model, or human graders. |
| **Capability vs. regression evals** | P0 | It tells you to build two suites, not one. |
| **Evaluating research agents** | P0 | It is the closest analogue to a research and synthesis product. |
| **How to think about non-determinism in evaluations for agents** | P0 | It explains pass@k and pass^k. |
| **Going from zero to one: a roadmap to great evals for agents** | P0 | It is the implementation roadmap. Read Steps 0 through 8. |
| **How evals fit with other methods for a holistic understanding of agents** | P1 | It reminds you that automated evals are one layer. |
| **Why build evaluations?** | P1 | It explains the failure mode of teams without evals. |
| **Conclusion** | P1 | It summarizes the method. |
| **Appendix: Eval frameworks** | P2 | It helps you choose tooling later. |
| **Evaluating coding agents** | Skip for now | It is not your agent type. |
| **Evaluating conversational agents** | Skip for now | It is not your agent type. |
| **Computer use agents** | Skip for now | It is not your agent type. |

The most important section for a research agent is "Evaluating research agents".
It covers groundedness, coverage, source quality, exact match for facts, and LLM rubric calibration.

The most important section for implementation is "Going from zero to one".
It covers task collection, task quality, balanced sets, harness design, graders, transcript review, and maintenance.

---

## 4. The repeatable method

Use this on every agent project.

```text
Contract -> Cases -> Harness -> Baseline -> Gate -> Learn
```

### 4.1 Contract

Define the input, output, artifacts, quality rules, and non-goals.
Write the contract before you write product code.

The contract must answer:

- What is the input schema?
- What is the output schema?
- Where do artifacts live?
- What counts as evidence?
- What counts as an assumption?
- What must the agent never do?
- What are the hard gates?
- What are the scored dimensions?

### 4.2 Cases

Build a small set of unambiguous tasks.
Start with 20 tasks.
The article recommends 20 to 50 simple tasks drawn from real failures.
Do not wait for hundreds.

Each task must have:

- A clear input.
- A clear success definition.
- At least one code-based grader.
- At least one model-based grader.
- A reference solution or reference fact set.
- A holdout flag.

A task is good when two domain experts would independently reach the same pass or fail verdict.
If they would not, the task is ambiguous.

### 4.3 Harness

Run the real agent in isolated trials.
Capture the transcript, outcome, artifacts, token usage, and latency.
Save raw traces.
Run code-based graders first.
Run model-based graders second.
Support multiple trials per task for release runs.

### 4.4 Baseline

Run the current system.
Expect failure.
Record per-task results, not only an average.
Do not tune anything before the baseline exists.

### 4.5 Gate

Use a small smoke suite in CI on every pull request.
Run the full suite nightly.
Block safety failures and missing artifacts.
Block pass-rate regressions beyond a small threshold.
Block cost and latency overruns.
Add a regression task for every real bug.

### 4.6 Learn

Read transcripts.
Classify failures.
Fix one failure class at a time.
Re-run the suite.
Keep a holdout set clean.
Watch for saturation.

---

## 5. What to implement before product code

Use this checklist before you write agent logic.

- [ ] Task contract in `evals/spec.md`.
- [ ] Input and output schemas.
- [ ] Artifact paths and formats.
- [ ] Quality rules and non-goals.
- [ ] Hard gates and scored dimensions.
- [ ] 20 seed tasks.
- [ ] 5 holdout tasks.
- [ ] 3 reference solutions.
- [ ] Code-based graders.
- [ ] Model-based rubric.
- [ ] Runner with isolated workspaces.
- [ ] Raw trace capture.
- [ ] Baseline report.
- [ ] CI smoke gate.
- [ ] Failure taxonomy.

Do not wire delegation, packaging, or new tools until this list is mostly complete.

---

## 6. Eval-first walkthrough for a new project

This is what "define the evals first" looks like in practice.
The example is a small research-brief agent.
The same order applies to the AI Product Launch Engineer.

### Step 0: Write the task contract by hand

Create `evals/spec.md`.

Input:

- A topic.
- An audience.
- A length limit.

Output:

- A research brief with five sections.
- At least five sources.
- A list of assumptions.

Artifacts:

- `brief.md`
- `sources.json`

Non-goals:

- No invented sources.
- No claims without a source or an assumption label.

Hard gates:

- Both artifacts exist.
- The brief has all five sections.
- `sources.json` is valid JSON.
- At least five sources have URLs.

Scored dimensions:

- Completeness.
- Evidence quality.
- Source quality.
- Coherence.
- Assumption transparency.

This file exists before any agent code.

### Step 1: Write three tasks before code

Create `evals/tasks/001.yaml`.

```yaml
task:
  id: brief_001
  desc: "Write a research brief on AI meeting assistants for recruiting teams."
  input:
    topic: "AI meeting assistants for recruiting teams"
    audience: "founders"
    max_words: 800
  expected:
    sections:
      - market overview
      - competitors
      - customer problems
      - opportunities
      - risks
    min_sources: 5
    artifacts:
      - brief.md
      - sources.json
  graders:
    - type: artifact_exists
    - type: section_coverage
    - type: source_quality
    - type: llm_rubric
```

Write two more tasks.
Use one clear task, one ambiguous task, and one adversarial task.

### Step 2: Write the reference output by hand

Create `evals/reference/brief_001.md`.
Create `evals/reference/brief_001_sources.json`.

The reference output proves the task is solvable.
It also gives the judge a reference.
It also proves the graders are configured correctly.

### Step 3: Write the graders

Write `artifact_exists`.
Write `section_coverage`.
Write `source_quality`.
Write `llm_rubric`.

These are test code.
They are not product code.

### Step 4: Write the harness against a stub

The stub returns an empty brief.
Run the harness.
Expected result: 0 percent pass.
This is the red baseline.

If the stub passes, the graders are broken.
If the reference output fails, the task is broken.
Fix the eval before you write the agent.

### Step 5: Implement the smallest product slice

Now write the agent.
Start with the smallest slice that can produce a valid brief.
Do not add delegation, tools, or packaging yet.

### Step 6: Make the red baseline green

Run the harness.
Read the transcript.
Fix the highest-impact failure.
Repeat.

### Step 7: Add regression tasks

Every bug becomes a task.
Every new capability starts as a failing task.
The suite grows from real failures, not from imagination.

This is the concrete meaning of "evals first".
The eval artifacts exist first.
The product code exists to make them pass.

---

## 7. Applying this to the AI Product Launch Engineer

Current gaps in the repository:

- `evals/spec.md` is missing.
- `evals/datasets/` is empty.
- `evals/evaluators.py` is empty.
- `evals/run_evals.py` is empty.
- Artifact paths are inconsistent between the supervisor and subagents.
- There is no reference blueprint.
- There is no baseline.

Recommended order:

1. Fix the artifact path contract.
2. Write `evals/spec.md`.
3. Create 20 tasks from the matrix below.
4. Write 3 reference blueprints.
5. Write code-based graders.
6. Write the runner with isolated workspaces.
7. Run the red baseline.
8. Add one LLM rubric judge.
9. Calibrate the judge on 20 human labels.
10. Add a CI smoke gate.

### 7.1 Artifact layout

Pick one layout.
I recommend the project-scoped layout.

```text
/projects/{project_slug}/
├── research/
│   ├── market.md
│   └── customers.md
├── strategy/
│   └── gtm.md
├── blueprint.md
├── manifest.json
└── deliverable.zip
```

The supervisor and all subagents must use the same paths.
A path mismatch is a contract bug, not an agent bug.

### 7.2 Task matrix for this project

| Task type | Count | What it tests |
| --- | --- | --- |
| Clear B2B product | 4 | Baseline competence |
| Ambiguous idea | 4 | Assumption handling |
| Crowded market | 3 | Research depth |
| Regulated or high-risk | 3 | Caution and scope control |
| Adversarial prompt injection | 3 | Safety |
| Conflicting sources | 3 | Judgment and evidence quality |

Keep 5 tasks as a holdout set.

### 7.3 Task schema for this project

```yaml
task:
  id: b2b_recruiting_assistant
  desc: "Produce a launch blueprint for an AI meeting assistant for small recruiting teams."
  input:
    idea: "AI meeting assistant for small recruiting teams"
    audience: "recruiting agencies with 5 to 50 recruiters"
    constraints:
      budget: "low"
      geography: "US"
  graders:
    - type: artifact_exists
      required:
        - /projects/b2b-recruiting-assistant/research/market.md
        - /projects/b2b-recruiting-assistant/research/customers.md
        - /projects/b2b-recruiting-assistant/strategy/gtm.md
        - /projects/b2b-recruiting-assistant/blueprint.md
    - type: section_coverage
      required:
        - competitor landscape
        - ideal customer profile
        - personas
        - positioning
        - distribution plan
        - risks
    - type: source_quality
      min_sources: 6
      require_urls: true
    - type: llm_rubric
      rubric: prompts/blueprint_quality.md
      dimensions:
        - completeness
        - evidence
        - customer_specificity
        - gtm_coherence
        - assumption_transparency
        - actionability
    - type: transcript
      required_subagents:
        - market_researcher
        - customer_researcher
        - gtm_strategist
      max_tool_calls: 60
    - type: state_check
      expect:
        zip_exists: true
        manifest_valid: true
  tracked_metrics:
    - n_turns
    - n_toolcalls
    - n_total_tokens
    - latency
```

### 7.4 Graders for this project

Code-based graders:

- Required files exist at exact paths.
- Required headings exist.
- Source count meets the minimum.
- No placeholders such as `TODO`, `lorem`, or `[citation needed]`.
- Manifest is valid JSON.
- Zip is valid and contains the expected files.
- No duplicate or blacklisted sources.

Model-based graders:

- One judge per dimension.
- Structured JSON output.
- Allow the judge to return `Unknown` when evidence is insufficient.
- Calibrate against 20 to 30 human labels.
- Use pairwise comparison when scores are close.

Human graders:

- Review 20 to 30 outputs.
- Measure agreement with the model judge.
- Review transcripts weekly.

### 7.5 Non-determinism for this project

Use pass@1 for capability.
Use pass^3 for release reliability.
Run at least 3 trials per task for release gates.
Report per-task results, not only an average.

### 7.6 Report format

Use a simple table.

```text
task_id, pass, completeness, evidence, coverage, trajectory, cost, latency, failure_class
```

Add a short summary:

- Pass rate.
- Mean score per dimension.
- Worst failure class.
- Cost per task.
- Latency per task.
- Grader bugs found.
- Tasks added or changed.

---

## 8. Dataset design

### 8.1 How many tasks

Start with 20.
The article recommends 20 to 50.
Do not wait for hundreds.
Small samples are useful early because changes have large effects.
Grow the suite as the agent matures.

### 8.2 Balanced problem sets

Test both directions.

- Cases where the agent should search.
- Cases where the agent should answer from context.
- Cases where the agent should ask for missing information.
- Cases where the agent should proceed with a labeled assumption.
- Cases where the agent should refuse or narrow scope.
- Cases where the agent should say the evidence is insufficient.

One-sided evals create one-sided optimization.

### 8.3 Reference solutions

Write 3 to 5 reference solutions.
A reference solution proves the task is solvable.
It proves the graders work.
It gives the judge a reference.
For research tasks, a reference solution can be a curated brief with sources.

### 8.4 Holdout set

Keep 5 tasks out of prompt tuning.
Use them only for final checks.
This prevents overfitting.

### 8.5 Ambiguity test

Ask two domain experts to grade the same output.
If they disagree on pass or fail, the task is ambiguous.
Fix the task before you add more tasks.

---

## 9. Graders

### 9.1 Code-based graders

Use code when the check is objective.

Examples:

- File exists.
- Schema is valid.
- Section is present.
- Source count is high enough.
- Zip is valid.
- Tool call budget is respected.
- No placeholder text.

Code graders are fast, cheap, and reproducible.
Use them first.

### 9.2 Model-based graders

Use a model when the check needs judgment.

Examples:

- Is the research coherent?
- Is the positioning specific?
- Are assumptions explicit?
- Is the GTM plan actionable?
- Are claims supported by the cited sources?

Model graders are flexible but non-deterministic.
Calibrate them against humans.
Give them a way out with `Unknown`.
Use one judge per dimension.

### 9.3 Human graders

Use humans to calibrate.
Use humans for subjective or high-stakes outputs.
Use humans to find grader bugs.
Do not use humans for every run.

### 9.4 Partial credit

Score each component.
A blueprint with seven of ten sections and good evidence is better than a blueprint with three of ten sections.
Represent the continuum of success.

### 9.5 Do not over-grade the path

Check outcomes and coarse process requirements.
Do not require an exact sequence of tool calls.
Do not require an exact number of turns.
Use budgets and required artifacts instead.

### 9.6 Calibration

Human-label 20 to 30 outputs.
Compare the judge to the labels.
Measure agreement.
If agreement is low, tighten the rubric or use pairwise comparison.
Re-calibrate when the model or prompt changes.

---

## 10. Non-determinism

Agents vary between runs.
A task that passed once may fail next time.
Use multiple trials.

`pass@k` measures the chance of at least one success in k trials.
`pass^k` measures the chance that all k trials succeed.

Use `pass@1` for capability.
Use `pass^3` for release reliability.
Report both when it matters.

Do not report a single run as the truth.

---

## 11. Harness requirements

The harness must:

- Run the real agent.
- Use a clean workspace per trial.
- Capture the full transcript.
- Capture the final outcome.
- Capture artifacts.
- Capture token usage.
- Capture latency.
- Capture errors.
- Save raw traces.
- Run graders in a fixed order.
- Aggregate results.
- Support multiple trials.
- Support a smoke subset for CI.

The harness must not:

- Reuse state between trials.
- Mock the agent for quality evals.
- Hide grader errors.
- Treat a missing artifact as a pass.
- Treat a judge error as a zero without logging it.

Isolation matters.
Shared state can inflate or corrupt results.
A clean workspace per trial is the default.

---

## 12. Baseline, gate, and iteration

### 12.1 Baseline

Run the current system.
Record results.
Do not tune before the baseline exists.

### 12.2 Capability vs regression

Capability evals should start with a low pass rate.
Regression evals should stay near 100 percent.
Run both.

### 12.3 Gate

Use a smoke suite in CI.
Run the full suite nightly.
Block safety failures.
Block missing artifacts.
Block large pass-rate regressions.
Block cost and latency overruns.

### 12.4 Failure taxonomy

Name the failures.

- Missing artifact.
- Wrong path.
- Missing section.
- Fabricated source.
- Unsupported claim.
- Ignored constraint.
- Bad delegation.
- Tool loop.
- Timeout.
- Prompt injection success.
- Cost overrun.
- Grader bug.

A named failure is a fixable failure.

### 12.5 Transcript review

Read transcripts weekly.
Ask two questions.
Did the agent fail?
Did the grader fail?

The article says this is a critical skill.
It is.

### 12.6 Saturation

An eval at 100 percent tracks regressions but gives no improvement signal.
Add harder tasks when the suite saturates.
Retire tasks only when they no longer represent real usage.

---

## 13. The holistic eval stack

Automated evals are one layer.

Use:

- Automated evals for fast iteration.
- Production monitoring for real behavior.
- A/B tests for significant changes.
- User feedback for unanticipated problems.
- Manual transcript review for subtle issues.
- Human studies for calibration and subjective quality.

No single layer catches every issue.
Combine them.

---

## 14. Hiring manager signal

A strong AI engineer can show these artifacts:

- A written task contract.
- A small, versioned task set.
- Reference solutions.
- A rubric with anchors.
- Code-based graders.
- A calibrated model judge.
- Coarse trajectory checks.
- A baseline.
- A regression gate.
- A failure taxonomy.
- Cost and latency reporting.
- Transcript reviews.
- Honest limitations.

They can also explain why a dataset is not an eval.
They can explain why a judge without calibration is a vibe check.
They can explain why path grading is brittle.
They can explain when to use pass@k and pass^k.

That is the signal.
The vocabulary is useful.
The artifacts are the proof.

---

## 15. Quick checklist

Use this before you ship an eval suite.

- [ ] The task contract is written.
- [ ] The artifact paths are consistent.
- [ ] There are at least 20 tasks.
- [ ] There are at least 5 holdout tasks.
- [ ] There are 3 to 5 reference solutions.
- [ ] The tasks are unambiguous.
- [ ] The task set is balanced.
- [ ] Code-based graders exist.
- [ ] Model-based graders exist.
- [ ] The model judge is calibrated.
- [ ] The judge can return `Unknown`.
- [ ] The harness isolates trials.
- [ ] The harness captures transcripts.
- [ ] The harness captures outcomes and artifacts.
- [ ] The baseline is recorded.
- [ ] The CI smoke gate exists.
- [ ] The failure taxonomy exists.
- [ ] A regression task is added for every bug.
- [ ] Transcripts are reviewed weekly.
- [ ] Cost and latency are reported.
- [ ] Saturation is monitored.

---

## 16. Glossary

**Agent harness:** The system that lets a model act as an agent.
**Capability eval:** A test of what the agent can do.
**Code-based grader:** A deterministic grader.
**Coverage:** The key facts a good answer must include.
**Eval:** A test for an AI system with grading logic.
**Eval saturation:** The state where the agent passes every solvable task.
**Evaluation harness:** The infrastructure that runs evals end to end.
**Evaluation suite:** A collection of tasks with a shared goal.
**Grader:** Logic that scores one aspect of performance.
**Groundedness:** The degree to which claims are supported by sources.
**Holdout set:** Tasks kept out of prompt tuning.
**Human grader:** A person who labels output.
**Model-based grader:** An LLM that scores output.
**Outcome:** The final state of the environment.
**pass@k:** The chance of at least one success in k trials.
**pass^k:** The chance that all k trials succeed.
**Reference solution:** A known-good output that passes the graders.
**Regression eval:** A test of what the agent must not break.
**Source quality:** The authority and relevance of cited sources.
**Task:** A single test with defined inputs and success criteria.
**Transcript:** The full record of a trial.
**Trial:** One attempt at a task.

---

## 17. Source notes

The structure, grader types, research-agent guidance, non-determinism metrics, and zero-to-one roadmap come from Anthropic's article.
The project-specific sections adapt those ideas to the AI Product Launch Engineer.

When the article and your product needs conflict, prefer the product need.
Then write down why.
The reason belongs in the task contract.
