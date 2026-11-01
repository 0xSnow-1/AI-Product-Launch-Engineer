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
