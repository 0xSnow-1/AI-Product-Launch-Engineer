"""Render a self-contained HTML report for one graded evaluation run."""

from __future__ import annotations

import argparse
import ast
import html
import json
import os
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from markdown_it import MarkdownIt


ARTIFACT_FILES: tuple[tuple[str, str], ...] = (
    ("Market Research", "research/market_research.json"),
    ("Customer Research", "research/customer_research.json"),
    ("GTM Strategy", "strategy/gtm_strategy.json"),
    ("Blueprint", "blueprint.md"),
    ("Manifest", "manifest.json"),
    ("Archive", "deliverable.zip"),
)
MARKDOWN_FILES = frozenset(path for _, path in ARTIFACT_FILES if path.endswith(".md"))
RESEARCH_SUBAGENTS = ("market_researcher", "customer_researcher")
GTM_SUBAGENT = "gtm_strategist"
TIMELINE_SUBAGENTS = ("market_researcher", "customer_researcher", "gtm_strategist")
FAILURE_CLASSES: dict[str, str] = {
    "artifact_exists": "Missing artifact",
    "deprecated_path": "Wrong path",
    "artifact_schemas": "Invalid artifact",
    "section_coverage": "Missing section",
    "source_citations": "Unsupported claim",
    "manifest": "Missing artifact",
    "archive": "Missing artifact",
    "placeholders": "Missing section",
    "delegation": "Bad delegation",
}
PASS_KEYS = ("pass_at_n", "pass_n", "pass^k", "pass_caret_n", "pass_at_k", "pass_rate")
_MARKDOWN = MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": False})

TABS_SCRIPT = """
(function () {
  document.querySelectorAll('[data-tabs]').forEach(function (group) {
    var tabs = Array.prototype.slice.call(group.querySelectorAll('[role="tab"]'));
    var panels = Array.prototype.slice.call(group.querySelectorAll('[role="tabpanel"]'));
    function activate(tab) {
      tabs.forEach(function (candidate) {
        var on = candidate === tab;
        candidate.setAttribute('aria-selected', on ? 'true' : 'false');
        candidate.tabIndex = on ? 0 : -1;
      });
      panels.forEach(function (panel) {
        panel.hidden = panel.id !== tab.getAttribute('aria-controls');
      });
    }
    tabs.forEach(function (tab, index) {
      tab.addEventListener('click', function () { activate(tab); });
      tab.addEventListener('keydown', function (event) {
        var next = null;
        if (event.key === 'ArrowRight') { next = tabs[(index + 1) % tabs.length]; }
        else if (event.key === 'ArrowLeft') { next = tabs[(index - 1 + tabs.length) % tabs.length]; }
        else if (event.key === 'Home') { next = tabs[0]; }
        else if (event.key === 'End') { next = tabs[tabs.length - 1]; }
        if (next) { event.preventDefault(); activate(next); next.focus(); }
      });
    });
  });
}());
"""

STYLE = """
:root {
  --bg: #f6f7f9;
  --surface: #ffffff;
  --text: #1c2430;
  --muted: #64748b;
  --border: #d8dee8;
  --pass: #167a4a;
  --pass-bg: #e4f5ec;
  --fail: #b42318;
  --fail-bg: #fde8e6;
  --warn: #9a6700;
  --warn-bg: #fff4d6;
  --accent: #2056b3;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 15px;
  line-height: 1.5;
}
.wrap { max-width: 1200px; margin: 0 auto; padding: 24px 16px 48px; }
h1, h2, h3 { line-height: 1.25; margin: 0 0 12px; }
h1 { font-size: 1.7rem; }
h2 { font-size: 1.3rem; margin-top: 32px; }
h3 { font-size: 1.05rem; margin-top: 24px; }
p { margin: 0 0 10px; }
a { color: var(--accent); }
code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
pre {
  background: #f2f4f7;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
.report-header {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
}
.header-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.label { color: var(--muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; }
.value { font-weight: 600; overflow-wrap: anywhere; }
.kpi-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 12px;
  margin-top: 16px;
}
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
}
.card .value { font-size: 1.35rem; margin-top: 4px; }
.badge {
  display: inline-block;
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 0.8rem;
  font-weight: 700;
  border: 1px solid transparent;
}
.badge-pass { color: var(--pass); background: var(--pass-bg); border-color: var(--pass); }
.badge-fail { color: var(--fail); background: var(--fail-bg); border-color: var(--fail); }
.badge-warn { color: var(--warn); background: var(--warn-bg); border-color: var(--warn); }
.table-wrap { overflow-x: auto; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; }
table { width: 100%; border-collapse: collapse; min-width: 720px; }
th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
th { background: #eef1f6; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.03em; }
tr:last-child td { border-bottom: 0; }
.task-detail {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 18px;
  margin-top: 16px;
}
.checklist { list-style: none; margin: 0; padding: 0; }
.checklist li { display: flex; flex-wrap: wrap; gap: 8px; padding: 4px 0; border-bottom: 1px dashed var(--border); }
.checklist li:last-child { border-bottom: 0; }
.checklist .path { color: var(--muted); overflow-wrap: anywhere; }
.tabs { display: flex; flex-wrap: wrap; gap: 6px; border-bottom: 1px solid var(--border); margin-bottom: 12px; }
.tabs button {
  border: 1px solid var(--border);
  border-bottom: none;
  background: #eef1f6;
  color: var(--text);
  padding: 6px 12px;
  border-radius: 8px 8px 0 0;
  cursor: pointer;
  font: inherit;
}
.tabs button[aria-selected="true"] { background: var(--surface); font-weight: 700; }
.tabs button:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
.timeline { list-style: none; margin: 0; padding: 0; }
.timeline li { display: grid; grid-template-columns: 150px 1fr; gap: 8px; padding: 6px 0; border-bottom: 1px solid var(--border); }
.timeline li:last-child { border-bottom: 0; }
.timeline .time { color: var(--muted); font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.85rem; }
.empty { color: var(--muted); font-style: italic; }
.grid-two { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }
.muted { color: var(--muted); }
footer { margin-top: 32px; color: var(--muted); font-size: 0.85rem; }
@media (max-width: 640px) {
  .wrap { padding: 16px 10px 40px; }
  .timeline li { grid-template-columns: 1fr; }
}
@media print {
  body { background: #fff; }
  .wrap { max-width: none; }
  .tabs { display: none; }
  [role="tabpanel"] { display: block !important; }
  .task-detail { break-inside: avoid; }
}
"""


def _escape(value: Any) -> str:
    """Escape a value for HTML text and attribute contexts."""

    return html.escape("" if value is None else str(value), quote=True)


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _read_json(path: Path) -> Any:
    text = _read_text(path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _read_transcript(path: Path) -> tuple[list[Mapping[str, Any]], list[int]]:
    events: list[Mapping[str, Any]] = []
    malformed: list[int] = []
    text = _read_text(path)
    if text is None:
        return events, malformed
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            malformed.append(line_number)
            continue
        if isinstance(event, Mapping):
            events.append(event)
        else:
            malformed.append(line_number)
    return events, malformed


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _format_duration(start: datetime | None, finish: datetime | None) -> str:
    if start is None or finish is None:
        return "n/a"
    seconds = (finish - start).total_seconds()
    if seconds < 0:
        return "n/a"
    return f"{seconds:.1f}s"


def _parse_subagent(value: Any) -> str | None:
    if isinstance(value, Mapping):
        raw = value.get("subagent_type")
        return raw if isinstance(raw, str) and raw.strip() else None
    if not isinstance(value, str):
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return None
    if isinstance(parsed, Mapping):
        raw = parsed.get("subagent_type")
        return raw if isinstance(raw, str) and raw.strip() else None
    return None


def _event_subagent(event: Mapping[str, Any]) -> str | None:
    explicit = event.get("subagent")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    return _parse_subagent(event.get("input"))


def _transcript_metrics(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    tool_calls = sum(1 for event in events if event.get("event") == "tool_started")
    tokens = 0
    tokens_seen = False
    timestamps: list[datetime] = []
    for event in events:
        for key in ("total_tokens", "tokens"):
            value = event.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                tokens += value
                tokens_seen = True
        usage = event.get("usage")
        if isinstance(usage, Mapping):
            value = usage.get("total_tokens")
            if isinstance(value, int) and not isinstance(value, bool):
                tokens += value
                tokens_seen = True
        timestamp = _parse_timestamp(event.get("timestamp"))
        if timestamp is not None:
            timestamps.append(timestamp)
    latency = None
    if timestamps:
        latency = (max(timestamps) - min(timestamps)).total_seconds()
    return {
        "tool_calls": tool_calls,
        "tokens": tokens if tokens_seen else None,
        "latency": latency,
    }


def _intervals(events: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, datetime]]:
    starts: dict[str, dict[str, Any]] = {}
    finishes: dict[str, datetime] = {}
    for event in events:
        kind = event.get("event")
        is_start = (
            event.get("tool") == "task"
            and kind in {"tool_started", "delegation_started"}
        ) or kind == "delegation_started"
        is_finish = (
            event.get("tool") == "task"
            and kind in {"tool_finished", "delegation_finished"}
        ) or kind == "delegation_finished"
        if not (is_start or is_finish):
            continue
        run_id = event.get("run_id")
        if run_id is None or not str(run_id).strip():
            continue
        key = str(run_id)
        timestamp = _parse_timestamp(event.get("timestamp"))
        if timestamp is None:
            continue
        if is_start:
            subagent = _event_subagent(event)
            if subagent is not None and key not in starts:
                starts[key] = {"subagent": subagent, "timestamp": timestamp}
        elif key in starts and key not in finishes:
            finishes[key] = timestamp

    pairs: dict[str, dict[str, datetime]] = {}
    for key, start in starts.items():
        entries = pairs.setdefault(start["subagent"], {})
        start_time = start["timestamp"]
        if "start" not in entries or start_time < entries["start"]:
            entries["start"] = start_time
        finish_time = finishes.get(key)
        if finish_time is not None and ("finish" not in entries or finish_time < entries["finish"]):
            entries["finish"] = finish_time
    return pairs


def _delegation_details(
    grader: Mapping[str, Any] | None,
    events: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if grader is not None:
        details = grader.get("details")
        if isinstance(details, Mapping) and isinstance(details.get("start_times"), Mapping):
            return dict(details)
    intervals = _intervals(events)
    market_finish = intervals.get("market_researcher", {}).get("finish")
    customer_finish = intervals.get("customer_researcher", {}).get("finish")
    gtm_start = intervals.get("gtm_strategist", {}).get("start")
    proven = (
        market_finish is not None
        and customer_finish is not None
        and gtm_start is not None
        and gtm_start >= market_finish
        and gtm_start >= customer_finish
    )
    return {
        "start_times": {
            name: (intervals.get(name, {}).get("start").isoformat() if intervals.get(name, {}).get("start") else None)
            for name in TIMELINE_SUBAGENTS
        },
        "finish_times": {
            name: (intervals.get(name, {}).get("finish").isoformat() if intervals.get(name, {}).get("finish") else None)
            for name in TIMELINE_SUBAGENTS
        },
        "gtm_after_both_research": proven,
        "tool_call_count": sum(1 for event in events if event.get("event") == "tool_started"),
    }


def _grader_map(results: Any) -> dict[str, Mapping[str, Any]]:
    mapping: dict[str, Mapping[str, Any]] = {}
    if not isinstance(results, list):
        return mapping
    for result in results:
        if isinstance(result, Mapping) and isinstance(result.get("grader_name"), str):
            mapping[result["grader_name"]] = result
    return mapping


def _failure_classes(graders: Mapping[str, Mapping[str, Any]]) -> list[str]:
    classes: list[str] = []
    for name, result in graders.items():
        if result.get("passed") is False:
            label = FAILURE_CLASSES.get(name, name)
            if label not in classes:
                classes.append(label)
    return classes


def _judge_entries(data: Any) -> dict[str, Mapping[str, Any]]:
    if not isinstance(data, Mapping):
        return {}
    for key in ("dimensions", "scores", "results"):
        value = data.get(key)
        if isinstance(value, Mapping):
            return {str(name): entry for name, entry in value.items() if isinstance(entry, Mapping)}
        if isinstance(value, list):
            entries: dict[str, Mapping[str, Any]] = {}
            for entry in value:
                if isinstance(entry, Mapping):
                    name = entry.get("dimension") or entry.get("name") or entry.get("id")
                    if isinstance(name, str):
                        entries[name] = entry
            return entries
    if all(not isinstance(value, Mapping) or "score" in value for value in data.values()):
        return {str(name): value for name, value in data.items() if isinstance(value, Mapping)}
    return {}


def _judge_score(data: Any) -> str:
    entries = _judge_entries(data)
    scores: list[float] = []
    for entry in entries.values():
        value = entry.get("score")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            scores.append(float(value))
    if not scores:
        return "n/a"
    return f"{sum(scores) / len(scores):.2f}"


def _project_root(trial_root: Path) -> Path | None:
    projects = trial_root / "projects"
    if not projects.is_dir():
        return None
    candidates = sorted(path for path in projects.iterdir() if path.is_dir())
    return candidates[0] if candidates else None


def _status_badge(passed: Any) -> str:
    if passed is True:
        return '<span class="badge badge-pass">PASS</span>'
    if passed is False:
        return '<span class="badge badge-fail">FAIL</span>'
    return '<span class="badge badge-warn">UNKNOWN</span>'


def _status_text(passed: Any) -> str:
    if passed is True:
        return "PASS"
    if passed is False:
        return "FAIL"
    return "UNKNOWN"


def _empty(message: str) -> str:
    return f'<p class="empty">{_escape(message)}</p>'


def _raw_link(output_path: Path, target: Path, label: str) -> str:
    if not target.is_file():
        return f'<span class="muted">{_escape(label)}: not found</span>'
    relative = os.path.relpath(target, output_path.parent)
    return f'<a href="{_escape(relative)}">{_escape(label)}</a>'


def _render_markdown(text: str) -> str:
    return _MARKDOWN.render(text)


def _render_artifact_panel(project_root: Path | None, relative_path: str) -> str:
    if project_root is None:
        return _empty("Project artifacts are missing.")
    path = project_root / relative_path
    if not path.is_file():
        return _empty(f"Missing artifact: {relative_path}")
    if relative_path in MARKDOWN_FILES:
        text = _read_text(path)
        if text is None:
            return _empty(f"Cannot read artifact: {relative_path}")
        return _render_markdown(text)
    if relative_path.endswith(".json"):
        text = _read_text(path)
        if text is None:
            return _empty(f"Cannot read artifact: {relative_path}")
        return f"<pre>{_escape(text)}</pre>"
    if relative_path == "deliverable.zip":
        try:
            with zipfile.ZipFile(path) as archive:
                entries = sorted(archive.namelist())
        except (OSError, zipfile.BadZipFile) as error:
            return _empty(f"Cannot read archive: {error}")
        if not entries:
            return _empty("Archive has no entries.")
        items = "".join(f"<li><code>{_escape(entry)}</code></li>" for entry in entries)
        return f'<ul class="checklist">{items}</ul>'
    return _empty(f"No preview for: {relative_path}")


def _artifact_checklist(project_root: Path | None) -> str:
    items: list[str] = []
    for label, relative_path in ARTIFACT_FILES:
        if project_root is None:
            exists = False
            size = ""
        else:
            path = project_root / relative_path
            exists = path.is_file()
            size = f" ({path.stat().st_size} bytes)" if exists else ""
        badge = _status_badge(exists)
        items.append(
            f'<li>{badge}<span class="path">{_escape(relative_path)}{_escape(size)}</span></li>'
        )
    return '<ul class="checklist">' + "".join(items) + "</ul>"


def _grader_checklist(graders: Mapping[str, Mapping[str, Any]]) -> str:
    if not graders:
        return _empty("No grader results found.")
    items: list[str] = []
    for name in sorted(graders):
        result = graders[name]
        items.append(
            f'<li>{_status_badge(result.get("passed"))}<span class="path">{_escape(name)}</span></li>'
        )
    return '<ul class="checklist">' + "".join(items) + "</ul>"


def _render_delegation(delegation: Mapping[str, Any]) -> str:
    starts = delegation.get("start_times")
    finishes = delegation.get("finish_times")
    starts = starts if isinstance(starts, Mapping) else {}
    finishes = finishes if isinstance(finishes, Mapping) else {}
    rows: list[str] = []
    for name in TIMELINE_SUBAGENTS:
        start = _parse_timestamp(starts.get(name))
        finish = _parse_timestamp(finishes.get(name))
        rows.append(
            "<tr>"
            f"<td>{_escape(name)}</td>"
            f"<td>{_escape(starts.get(name) or 'n/a')}</td>"
            f"<td>{_escape(finishes.get(name) or 'n/a')}</td>"
            f"<td>{_escape(_format_duration(start, finish))}</td>"
            "</tr>"
        )
    proven = delegation.get("gtm_after_both_research")
    badge = _status_badge(proven)
    tool_count = delegation.get("tool_call_count", "n/a")
    budget = delegation.get("max_tool_calls", "n/a")
    return (
        f'<p class="gtm-dependency">GTM after both research: {badge}</p>'
        '<div class="table-wrap"><table class="delegation-table">'
        "<thead><tr><th>Subagent</th><th>Start</th><th>Finish</th><th>Duration</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
        f'<p class="muted">Tool calls: {_escape(tool_count)} / budget {_escape(budget)}</p>'
    )


def _render_transcript(events: Sequence[Mapping[str, Any]], malformed: Sequence[int]) -> str:
    if not events and not malformed:
        return _empty("No transcript events found.")
    rows: list[str] = []
    for event in events[:1000]:
        actor = event.get("subagent") or event.get("tool") or event.get("model") or ""
        detail = ""
        for key in ("error", "output", "input", "status", "stdout", "stderr"):
            value = event.get(key)
            if value:
                detail = str(value)
                break
        rows.append(
            "<tr>"
            f"<td>{_escape(event.get('timestamp') or 'n/a')}</td>"
            f"<td>{_escape(event.get('event') or 'event')}</td>"
            f"<td>{_escape(event.get('run_id') or '')}</td>"
            f"<td>{_escape(actor)}</td>"
            f"<td>{_escape(detail[:300])}</td>"
            "</tr>"
        )
    note = ""
    if malformed:
        note = f'<p class="muted">Malformed lines: {_escape(", ".join(str(line) for line in malformed))}</p>'
    if len(events) > 1000:
        note += f'<p class="muted">Showing 1000 of {len(events)} events.</p>'
    return (
        f"{note}"
        '<div class="table-wrap"><table class="transcript-table">'
        "<thead><tr><th>Time</th><th>Event</th><th>Run ID</th><th>Actor</th><th>Detail</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _render_judge(data: Any) -> str:
    if data is None:
        return _empty("Judge results: not run. judge_results.json is missing.")
    entries = _judge_entries(data)
    if not entries:
        return f"<pre>{_escape(json.dumps(data, indent=2, sort_keys=True))}</pre>"
    rows: list[str] = []
    for name in sorted(entries):
        entry = entries[name]
        score = entry.get("score", "n/a")
        unknown = "yes" if entry.get("unknown") else "no"
        rationale = entry.get("rationale") or ""
        rows.append(
            "<tr>"
            f"<td>{_escape(name)}</td>"
            f"<td>{_escape(score)}</td>"
            f"<td>{_escape(unknown)}</td>"
            f"<td>{_escape(rationale)}</td>"
            "</tr>"
        )
    return (
        '<div class="table-wrap"><table class="judge-table">'
        "<thead><tr><th>Dimension</th><th>Score</th><th>Unknown</th><th>Rationale</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _artifact_tabs(view: Mapping[str, Any], task_index: int) -> str:
    project_root = view["project_root"]
    buttons: list[str] = []
    panels: list[str] = []
    for artifact_index, (label, relative_path) in enumerate(ARTIFACT_FILES):
        panel_id = f"artifact-{task_index}-{artifact_index}"
        buttons.append(
            f'<button type="button" role="tab" id="{panel_id}-tab" aria-controls="{panel_id}" '
            f'aria-selected="{"true" if artifact_index == 0 else "false"}" '
            f'tabindex="{0 if artifact_index == 0 else -1}">{_escape(label)}</button>'
        )
        panels.append(
            f'<div role="tabpanel" id="{panel_id}" aria-labelledby="{panel_id}-tab"'
            f'{" hidden" if artifact_index else ""}>'
            f"{_render_artifact_panel(project_root, relative_path)}</div>"
        )
    return (
        f'<div class="tabs" data-tabs role="tablist" aria-label="Artifact previews">{"".join(buttons)}</div>'
        f'{"".join(panels)}'
    )


def _load_views(summary: Mapping[str, Any], run_dir: Path) -> list[dict[str, Any]]:
    raw_reports = summary.get("reports")
    if not isinstance(raw_reports, list):
        return []
    views: list[dict[str, Any]] = []
    for raw_report in raw_reports:
        if not isinstance(raw_report, Mapping):
            continue
        task_id = raw_report.get("task_id")
        task_id = task_id if isinstance(task_id, str) and task_id.strip() else "unknown-task"
        raw_trial_root = raw_report.get("trial_root")
        if isinstance(raw_trial_root, str) and raw_trial_root.strip():
            trial_root = Path(raw_trial_root)
            if not trial_root.is_absolute():
                trial_root = run_dir / trial_root
        else:
            trial_root = run_dir / "trials" / task_id
        trial_root = trial_root.resolve()

        grader_path = trial_root / "grader_results.json"
        raw_graders = _read_json(grader_path)
        if isinstance(raw_graders, Mapping):
            graders = _grader_map(raw_graders.get("results"))
        else:
            graders = _grader_map(raw_report.get("results"))

        events, malformed = _read_transcript(trial_root / "transcript.jsonl")
        metrics = _transcript_metrics(events)
        delegation = _delegation_details(graders.get("delegation"), events)
        transcript_tool_count = metrics["tool_calls"]
        delegated_tool_count = delegation.get("tool_call_count")
        if isinstance(delegated_tool_count, int) and not isinstance(delegated_tool_count, bool):
            metrics["tool_calls"] = delegated_tool_count
        elif transcript_tool_count:
            metrics["tool_calls"] = transcript_tool_count

        judge = _read_json(trial_root / "judge_results.json")
        input_data = _read_json(trial_root / "input.json")
        passed = raw_report.get("passed")
        if not isinstance(passed, bool):
            passed = all(result.get("passed") is True for result in graders.values()) if graders else None

        views.append(
            {
                "task_id": task_id,
                "passed": passed,
                "trial_root": trial_root,
                "project_root": _project_root(trial_root),
                "graders": graders,
                "events": events,
                "malformed": malformed,
                "metrics": metrics,
                "delegation": delegation,
                "judge": judge,
                "input": input_data,
                "failure_classes": _failure_classes(graders),
            }
        )
    return views


def _kpi_cards(views: Sequence[Mapping[str, Any]], summary: Mapping[str, Any]) -> str:
    total = len(views)
    passed_count = sum(1 for view in views if view["passed"] is True)
    failed_count = sum(1 for view in views if view["passed"] is False)
    pass_rate = f"{(passed_count / total) * 100:.0f}%" if total else "n/a"

    pass_n: Any = None
    metrics = summary.get("metrics") if isinstance(summary.get("metrics"), Mapping) else {}
    for key in PASS_KEYS:
        if key in summary:
            pass_n = summary[key]
            break
        if key in metrics:
            pass_n = metrics[key]
            break
    if isinstance(pass_n, float) and 0.0 <= pass_n <= 1.0:
        pass_n_display = f"{pass_n * 100:.0f}%"
    else:
        pass_n_display = _escape(pass_n) if pass_n is not None else "n/a"

    tool_calls = sum(view["metrics"]["tool_calls"] for view in views)
    tokens_values = [view["metrics"]["tokens"] for view in views if view["metrics"]["tokens"] is not None]
    tokens = sum(tokens_values) if tokens_values else None
    latency_values = [view["metrics"]["latency"] for view in views if view["metrics"]["latency"] is not None]
    latency = sum(latency_values) if latency_values else None

    gtm_values = [
        view["delegation"].get("gtm_after_both_research")
        for view in views
        if isinstance(view["delegation"], Mapping)
    ]
    if not gtm_values:
        gtm_badge = _status_badge(None)
    else:
        gtm_badge = _status_badge(all(value is True for value in gtm_values))

    cards = (
        ("Pass rate", pass_rate),
        ("pass^N", pass_n_display),
        ("Failed tasks", str(failed_count)),
        ("Total tool calls", str(tool_calls)),
        ("Total tokens", f"{tokens:,}" if tokens is not None else "n/a"),
        ("Latency", f"{latency:.1f}s" if latency is not None else "n/a"),
    )
    rendered = "".join(
        f'<div class="card"><div class="label">{_escape(label)}</div><div class="value">{value}</div></div>'
        for label, value in cards
    )
    rendered += (
        '<div class="card"><div class="label">GTM dependency</div>'
        f'<div class="value">{gtm_badge}</div></div>'
    )
    return f'<section class="kpi-cards" aria-label="Key metrics">{rendered}</section>'


def _task_table(views: Sequence[Mapping[str, Any]]) -> str:
    if not views:
        return _empty("No task results found in summary.json.")
    rows: list[str] = []
    for view in views:
        graders = view["graders"]
        artifact_names = [name for name in graders if name != "delegation"]
        artifact_passed = sum(1 for name in artifact_names if graders[name].get("passed") is True)
        artifact_score = f"{artifact_passed}/{len(artifact_names)}" if artifact_names else "n/a"
        delegation = graders.get("delegation")
        delegation_score = _status_text(delegation.get("passed")) if delegation else "n/a"
        judge_data = view["judge"]
        judge_score = _judge_score(judge_data) if judge_data is not None else "n/a"
        tokens = view["metrics"]["tokens"]
        latency = view["metrics"]["latency"]
        failure_class = ", ".join(view["failure_classes"]) or "None"
        rows.append(
            "<tr>"
            f"<td>{_escape(view['task_id'])}</td>"
            f"<td>{_status_badge(view['passed'])}</td>"
            f"<td>{_escape(failure_class)}</td>"
            f"<td>{_escape(artifact_score)}</td>"
            f"<td>{_escape(delegation_score)}</td>"
            f"<td>{_escape(judge_score)}</td>"
            f"<td>{_escape(f'{tokens:,} tokens' if tokens is not None else 'n/a')}</td>"
            f"<td>{_escape(f'{latency:.1f}s' if latency is not None else 'n/a')}</td>"
            "</tr>"
        )
    return (
        '<div class="table-wrap"><table class="task-table">'
        "<thead><tr><th>Task</th><th>Status</th><th>Failure class</th><th>Artifact score</th>"
        "<th>Delegation</th><th>Judge</th><th>Cost</th><th>Latency</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _render_task_detail(view: Mapping[str, Any], output_path: Path, task_index: int) -> str:
    graders = view["graders"]
    project_root = view["project_root"]
    delegation = view["delegation"]
    input_data = view["input"]
    input_html = (
        f"<pre>{_escape(json.dumps(input_data, indent=2, sort_keys=True))}</pre>"
        if input_data is not None
        else _empty("input.json is missing.")
    )
    sections = graders.get("section_coverage", {}).get("details", {})
    missing_sections = sections.get("missing_sections", "n/a") if isinstance(sections, Mapping) else "n/a"
    sources = graders.get("source_citations", {}).get("details", {})
    if isinstance(sources, Mapping):
        source_summary = (
            f"{sources.get('unique_source_count', 'n/a')} unique / "
            f"{sources.get('required_sources', 'n/a')} required"
        )
    else:
        source_summary = "n/a"
    manifest = graders.get("manifest", {}).get("details", {})
    archive = graders.get("archive", {}).get("details", {})
    placeholders = graders.get("placeholders", {}).get("details", {})

    raw_links = " | ".join(
        [
            _raw_link(output_path, view["trial_root"] / "grader_results.json", "grader_results.json"),
            _raw_link(output_path, view["trial_root"] / "transcript.jsonl", "transcript.jsonl"),
            _raw_link(output_path, view["trial_root"] / "judge_results.json", "judge_results.json"),
            _raw_link(output_path, view["trial_root"] / "input.json", "input.json"),
        ]
    )
    return (
        f'<article class="task-detail" id="detail-{task_index}">'
        f"<h3>{_escape(view['task_id'])} {_status_badge(view['passed'])}</h3>"
        f'<p class="muted">Trial root: {_escape(view["trial_root"])}</p>'
        '<div class="grid-two">'
        f"<div><h4>Input</h4>{input_html}</div>"
        f"<div><h4>Artifact checks</h4>{_artifact_checklist(project_root)}</div>"
        "</div>"
        '<div class="grid-two">'
        f"<div><h4>Grader status</h4>{_grader_checklist(graders)}</div>"
        "<div><h4>Quality checks</h4>"
        f"<p>Section coverage: {_escape(json.dumps(missing_sections, sort_keys=True))}</p>"
        f"<p>Sources: {_escape(source_summary)}</p>"
        f"<p>Manifest: {_status_badge(graders.get('manifest', {}).get('passed') if graders.get('manifest') else None)}</p>"
        f"<p>Archive: {_status_badge(graders.get('archive', {}).get('passed') if graders.get('archive') else None)}</p>"
        f"<p>Placeholders: {_escape(json.dumps(placeholders, sort_keys=True))}</p>"
        f"<p>Failure classes: {_escape(', '.join(view['failure_classes']) or 'None')}</p>"
        f"<p>Manifest details: {_escape(json.dumps(manifest, sort_keys=True))}</p>"
        f"<p>Archive details: {_escape(json.dumps(archive, sort_keys=True))}</p>"
        "</div></div>"
        "<h4>Delegation timeline</h4>"
        f"{_render_delegation(delegation)}"
        "<h4>Judge dimensions</h4>"
        f"{_render_judge(view['judge'])}"
        "<h4>Artifact preview</h4>"
        f"{_artifact_tabs(view, task_index)}"
        "<h4>Transcript timeline</h4>"
        f"{_render_transcript(view['events'], view['malformed'])}"
        f'<p class="muted">Raw files: {raw_links}</p>'
        "</article>"
    )


def _render_document(
    summary: Mapping[str, Any] | None,
    views: Sequence[Mapping[str, Any]],
    run_dir: Path,
    output_path: Path,
) -> str:
    summary = summary if isinstance(summary, Mapping) else {}
    run_id = summary.get("run_id") or run_dir.name or "run"
    timestamp = summary.get("created_at") or summary.get("timestamp") or "n/a"
    commit = summary.get("commit") or summary.get("commit_sha") or "n/a"
    model = summary.get("model_id") or summary.get("model") or "n/a"
    overall = summary.get("passed")
    if not isinstance(overall, bool):
        overall = all(view["passed"] is True for view in views) if views else None

    header_fields = (
        ("Run ID", summary.get("run_id") or run_dir.name or "n/a"),
        ("Timestamp", timestamp),
        ("Commit SHA", commit),
        ("Model ID", model),
        ("Task count", str(len(views))),
    )
    header = "".join(
        f'<div><div class="label">{_escape(label)}</div><div class="value">{_escape(value)}</div></div>'
        for label, value in header_fields
    )
    summary_link = _raw_link(output_path, run_dir / "summary.json", "summary.json")
    details = "".join(
        _render_task_detail(view, output_path, index) for index, view in enumerate(views)
    ) or _empty("No task details found. summary.json is missing or empty.")
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>Eval Report - {_escape(run_id)}</title>\n"
        f"<style>{STYLE}</style>\n</head>\n<body>\n<div class=\"wrap\">\n"
        '<header class="report-header">\n'
        f"<h1>Evaluation Report {_status_badge(overall)}</h1>\n"
        f'<div class="header-grid">{header}</div>\n'
        f'<p class="muted">Raw summary: {summary_link}</p>\n'
        "</header>\n"
        f"{_kpi_cards(views, summary)}\n"
        '<section aria-labelledby="tasks-heading">\n'
        '<h2 id="tasks-heading">Task Results</h2>\n'
        f"{_task_table(views)}\n</section>\n"
        '<section aria-labelledby="details-heading">\n'
        '<h2 id="details-heading">Task Details</h2>\n'
        f"{details}\n</section>\n"
        "<footer>Generated from local eval files. No network access is used.</footer>\n"
        "</div>\n"
        f"<script>{TABS_SCRIPT}</script>\n"
        "</body>\n</html>\n"
    )


def build_report(run_dir: Path, output_path: Path | None = None) -> Path:
    """Write a self-contained HTML report for one run directory."""

    path = Path(run_dir)
    if path.is_file():
        summary_path = path
        path = path.parent
    else:
        summary_path = path / "summary.json"
    summary = _read_json(summary_path)
    if not isinstance(summary, Mapping):
        summary = {}
    views = _load_views(summary, path)
    destination = Path(output_path) if output_path is not None else path / "report.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        _render_document(summary, views, path, destination),
        encoding="utf-8",
    )
    return destination


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True, help="Run directory that contains summary.json.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the report here. Default: <run_dir>/report.html.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Render the report and print its path."""

    args = _parser().parse_args(argv)
    destination = build_report(args.run, args.output)
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
