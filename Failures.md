# Failures

## F-001: Bedrock specialist stream timed out

**Status:** Investigated

**Detected:** 2026-11-01

**Run:** `uv run python main.py --input evals/testing.json`

### Result

The supervisor started and delegated work.
One specialist model call then failed with `urllib3.exceptions.ReadTimeoutError`.
The full launch run stopped before it wrote an artifact.

### Evidence

- The run printed the supervisor startup, plan, and delegation messages.
- The traceback entered `deepagents.middleware.subagents.task`.
- The failing request used `bedrock-runtime.us-east-1.amazonaws.com`.
- The terminal reported `Read timed out` while consuming the Bedrock stream.
- `src/agents/common.py` creates `ChatBedrockConverse` without explicit timeout or retry settings.
- The installed botocore defaults use a 60-second connect timeout and a 60-second read timeout.

### Cause

The request did not receive streamed data before the SDK read timeout expired.

This failure can result from a slow model response or a network delay.
The current application treats that provider error as fatal.

### Impact

- The delegated task does not retry.
- The supervisor aborts the whole launch run.
- No partial artifact is available after the failure.

### What did not fail

- Input loading completed.
- The Bedrock client connected far enough to start the supervisor response.
- The supervisor created a todo plan.
- The supervisor started delegation.
- LangSmith configuration is present and reachable.

### Recommended fix

Configure the Bedrock runtime client with an explicit read timeout and retry policy.
Pass that client into `ChatBedrockConverse`.

Start with a bounded read timeout such as 300 seconds.
Add retries for transient connection and read failures.
Record each retry and final failure in `transcript.jsonl`.

Amazon Bedrock documents that streaming requests can require a longer SDK read timeout.
See [Amazon Bedrock troubleshooting](https://docs.aws.amazon.com/bedrock/latest/userguide/troubleshooting-api-error-codes.html) and the [ConverseStream API reference](https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-runtime/client/converse_stream.html).

### Validation after the fix

1. Run the same input once with a bounded timeout and retry policy.
2. Confirm the terminal reports progress during delegation.
3. Confirm the transcript records the specialist call and any retry.
4. Confirm that a timeout produces a clear failure record instead of an unhandled traceback.

---

## Baseline Trial Log: b2b_recruiting_meeting_assistant

| Trial | Run id | Date | Result | Note |
| --- | --- | --- | --- | --- |
| 1 | `20261102-230937-b2b_recruiting_meeting_assistant` | 2026-11-02 | 3 pass, 5 fail, exit 1 | Pre-separation layout. |
| 2 | `20261103-155304-b2b_recruiting_meeting_assistant` | 2026-11-03 | 4 pass, 4 fail, exit 0 | Current main. Path bug fixed. |

Trial 2 is the first run with the two-root layout.
Both trials fail `source_citations` and `section_coverage`.
Trial 2 adds a `delegation` budget failure and keeps the `manifest` failure.

## F-002: Customer research written to the project root

**Status:** Fixed and verified

**Detected:** 2026-11-02

**Run:** `evals/runs/20261102-230937-b2b_recruiting_meeting_assistant`

### Result

The run exited 1.
The packager raised `FileNotFoundError: Missing deliverable file for archive: research/customers.md`.
The customer research file was written to `/projects/b2b-recruiting-meeting-assistant/customers.md`.
The contract requires `/projects/b2b-recruiting-meeting-assistant/research/customers.md`.

### Cause

The agent ignored the prompt output path and wrote to the project root.
The packager correctly refused to build the archive.

### Evidence

- `src/prompts/subagents/customer_researcher/v2.yaml:17` requires `research/customers.md`.
- The agent's `write_file` call used `customers.md` at the project root.
- The agent's final message reported the project-root path.

### Impact

- `artifact_exists` failed.
- `archive` failed.
- The run exited 1.

### Fix

Trial 2 confirms the fix.
`artifact_exists`, `deprecated_path`, and `archive` pass on the current layout.

## F-003: Source citations are zero

**Status:** Open

**Detected:** 2026-11-03

**Run:** `evals/runs/20261103-155304-b2b_recruiting_meeting_assistant`

### Result

`source_citations` failed with `unique_source_count: 0` against a required minimum of 3.
`market.md` contains a source table with names, types, and credibility ratings.
The table has no URLs.

### Cause

`SOURCE_PATTERN` in `evals/evaluators.py:17` only accepts bullet links in the form `- [title](url)`.
The agent wrote a table instead.
The agent also omitted URLs from the table.

### Impact

Material market, pricing, and competitor claims are not verifiable.
This is the only real evidence-quality failure in trial 2.

### Recommended fix

Update the market research prompt to require bullet links under `Sources`.
Each material claim must have one `- [title](url)` entry.
Do not loosen the grader first.

## F-004: Required headings do not match

**Status:** Open

**Detected:** 2026-11-03

**Run:** `evals/runs/20261103-155304-b2b_recruiting_meeting_assistant`

### Result

`section_coverage` failed for all four documents.

Missing headings include:

- `market.md`: `Competitor Landscape`, `Market Opportunities`, `Trends and Insights`, `Sources`.
- `customers.md`: `Ideal Customer Profile`.
- `gtm.md`: `Positioning Statement`, `Value Proposition`, `Messaging by Channel`, `Distribution Plan`, `Launch Sequence`, `Launch Goals`, `Risks and Assumptions`.
- `blueprint.md`: `Risks and Assumptions`.

### Cause

The prompts say "include these sections" but do not say "use these exact headings".
The agent paraphrased. Examples:

- `Competitive Landscape` instead of `Competitor Landscape`.
- `Ideal Customer Profile (ICP)` instead of `Ideal Customer Profile`.
- `SECTION 1: POSITIONING & MESSAGING` instead of the required H2 names.
- `Assumptions & Limitations` instead of `Risks and Assumptions`.

`SectionCoverageGrader` in `evals/evaluators.py:100` matches exact heading text.

### Impact

Good content is scored as missing.
The grader is not wrong. The output contract is ambiguous.

### Recommended fix

Add a new prompt version that names the exact H2 headings.
Keep the grader strict.
Do not normalize away real wording differences.

## F-005: Manifest omits the supervisor

**Status:** Open

**Detected:** 2026-11-03

**Run:** `evals/runs/20261103-155304-b2b_recruiting_meeting_assistant`

### Result

`manifest` failed with `execution.agents_used is incomplete`.
The manifest lists `customer_researcher`, `market_researcher`, and `gtm_strategist`.
The task requires `supervisor` too.

### Cause

`collect_metrics` in `src/metrics.py:131` only records subagent names.
It never adds `supervisor`.

### Impact

The manifest never satisfies the contract.

### Recommended fix

Always add `supervisor` to `agents_used`.
Add a unit test for the manifest agent list.

## F-006: Tool call budget exceeded

**Status:** Open

**Detected:** 2026-11-03

**Run:** `evals/runs/20261103-155304-b2b_recruiting_meeting_assistant`

### Result

`delegation` failed with `tool call count 64 exceeds budget 60`.
The three subagents ran.
`gtm_strategist` started after both research results.

### Cause

The run used 64 tool calls.
The task budget is 60.
The research agents reread both research files many times.

### Impact

A correct delegation sequence is scored as failed.

### Recommended fix

Decide after the post-fix run.
Raise the budget to 80, or reduce repeated reads in the research prompts.
Do not raise the budget only to hide inefficiency.

## O-001: Token metrics are always zero

**Status:** Open

**Detected:** 2026-11-03

**Run:** `evals/runs/20261103-155304-b2b_recruiting_meeting_assistant`

### Result

`manifest.execution.total_tokens` is `0`.
The transcript contains model events and token usage.

### Cause

`_token_count` in `src/metrics.py:71` reads a top-level `usage` field.
Transcript `model_finished` events store the response as a string representation.
No top-level usage field exists.

### Impact

Cost and token metrics cannot be tracked.

### Recommended fix

Capture usage metadata at the model callback boundary.
Write it as a structured field in the transcript event.
