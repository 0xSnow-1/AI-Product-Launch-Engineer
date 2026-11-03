
Here are the streaming and approval parts for Python. I haven't run this code, so treat it as a skeleton and check the LangGraph and Bolt details below against current versions.

## Streaming into Slack

Bolt for Python passes a `say_stream` helper to `app.event` and `app.message` listeners. It fills in the channel, thread, and recipient from the event, so you only call `append(...)` and `stop()`. Combine it with LangGraph's `stream_mode="messages"`, which yields tokens as they arrive:

```python
from langchain_core.messages import AIMessageChunk

def text_of(chunk):
    c = chunk.content
    if isinstance(c, str):
        return c
    return "".join(b.get("text", "") for b in c if isinstance(b, dict))

@app.event("app_mention")
def handle(event, say, say_stream, set_status):
    ts = event.get("thread_ts") or event["ts"]
    cfg = {"configurable": {"thread_id": f"{event['channel']}:{ts}"}}
    set_status(status="Researching...")          # needs assistant:write scope

    streamer = say_stream()
    for chunk, meta in agent.stream(
        {"messages": [{"role": "user", "content": event["text"]}]},
        cfg, stream_mode="messages",
    ):
        if isinstance(chunk, AIMessageChunk):
            if t := text_of(chunk):
                streamer.append(markdown_text=t)
    streamer.stop()
```

Two caveats. Deep agents spawn subagents and call tools, so the raw token stream will include their output too. You'll likely want to filter on `meta` (for example, by node name) so users only see the final answer. Also, `set_status` needs the `assistant:write` scope on your Slack app.

## Approval buttons (human-in-the-loop)

Set `interrupt_on={"some_tool": True}` along with a checkpointer. After a run, `agent.get_state(cfg).next` is non-empty when it's paused. Post buttons, then resume when someone clicks:

```python
from langgraph.types import Command

def post_approval(say, ts, thread_id):
    say(thread_ts=ts, text="Approval needed", blocks=[
        {"type": "section", "text": {"type": "mrkdwn",
         "text": "The agent wants to run a tool. Approve?"}},
        {"type": "actions", "elements": [
            {"type": "button", "action_id": "approve",
             "text": {"type": "plain_text", "text": "Approve"},
             "style": "primary", "value": thread_id},
            {"type": "button", "action_id": "reject",
             "text": {"type": "plain_text", "text": "Reject"},
             "style": "danger", "value": thread_id},
        ]},
    ])

@app.action("approve")
def on_approve(ack, body, say):
    ack()
    thread_id = body["actions"][0]["value"]
    cfg = {"configurable": {"thread_id": thread_id}}
    out = agent.invoke(Command(resume={"decisions": [{"type": "approve"}]}), cfg)
    say(thread_ts=body["message"]["thread_ts"], text=out["messages"][-1].content)
```

The resume payload shape (`{"decisions": [...]}`) comes from my memory of the LangChain human-in-the-loop middleware, so check it against the current Deep Agents HITL docs. A `reject` handler is the same pattern with `{"type": "reject"}`.

## Slack-side details that changed recently

- **Thread replies in channels:** the `app_mention` event only fires on @mentions. To continue a conversation without re-mentioning the bot, add an `app.message` listener. Slack's sample app does this by only handling thread replies for threads it has already started, and ignoring messages from bots.
- **Messaging experience:** Slack now treats the "agent messaging experience" (`agent_view`) as the default and only option for new apps. DMs happen in the app's Messages tab, and you detect the user opening it via the `app_home_opened` event. The older assistant side-panel flow (`assistant_thread_started`) is legacy.
- **Reference code:** Slack's own Python sample (`slack-samples/bolt-python-support-agent`, "Casey") shows the full listener layout, status, streaming, and feedback buttons. It uses Pydantic, Anthropic, or OpenAI agents rather than Deep Agents, but swapping in your `agent` object is straightforward. It also has a one-click setup through the Slack CLI.

Want me to cover persistent memory (SQLite checkpointer) or running this somewhere always-on for free next?