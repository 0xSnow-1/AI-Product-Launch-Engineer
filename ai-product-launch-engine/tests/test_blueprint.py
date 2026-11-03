"""Tests for blueprint assembly under the isolated workspace root."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from agents.supervisor import create_blueprint  # noqa: E402


PROJECT_SLUG = "b2b-recruiting-meeting-assistant"
NOW = "2026-11-04T00:00:00Z"


def _seed_research(project_root: Path) -> None:
    market = {
        "project_id": PROJECT_SLUG,
        "generated_at": NOW,
        "summary": "Narrow recruiting niche with a clear gap.",
        "competitors": [{"name": "Example ATS", "positioning": "Applicant tracking with add-ons"}],
        "market_opportunities": ["Small agencies lack structured intake notes"],
        "trends": ["Remote intake calls are common"],
        "claims": [],
        "assumptions": ["Agencies will pilot within 90 days"],
        "limitations": ["No primary survey was run"],
    }
    customer = {
        "project_id": PROJECT_SLUG,
        "generated_at": NOW,
        "segments": [{"name": "Small agencies", "description": "5 to 50 recruiters"}],
        "personas": [{"name": "Agency owner", "role": "buyer"}],
        "pain_points": ["Notes are retyped into the ATS"],
        "buying_triggers": ["New client volume exceeds capacity"],
        "ideal_customer_profile": "US recruiting agency with 5 to 50 recruiters",
        "claims": [],
        "assumptions": ["Owners approve pilots"],
        "limitations": ["Interview data is hypothetical"],
    }
    gtm = {
        "project_id": PROJECT_SLUG,
        "generated_at": NOW,
        "positioning": "The intake-call assistant for small recruiting agencies",
        "differentiation": "Structured notes and ATS follow-up actions",
        "target_segments": ["Small US recruiting agencies"],
        "pricing_hypotheses": ["Low monthly fee per recruiter"],
        "channels": ["Direct outreach"],
        "launch_roadmap": [
            {"name": "Pilot", "timeline": "Weeks 1 to 6", "activities": ["Recruit ten agencies"]}
        ],
        "risks": ["ATS integration access delays the pilot"],
        "assumptions": ["Agencies accept a paid pilot"],
        "claims": [],
    }
    research_dir = project_root / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    strategy_dir = project_root / "strategy"
    strategy_dir.mkdir(parents=True, exist_ok=True)
    (research_dir / "market_research.json").write_text(json.dumps(market), encoding="utf-8")
    (research_dir / "customer_research.json").write_text(json.dumps(customer), encoding="utf-8")
    (strategy_dir / "gtm_strategy.json").write_text(json.dumps(gtm), encoding="utf-8")


class BlueprintLocationTests(unittest.TestCase):
    def test_blueprint_writes_under_the_workspace_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace_root = Path(directory)
            project_root = workspace_root / "projects" / PROJECT_SLUG
            _seed_research(project_root)
            output = io.StringIO()
            create_blueprint(object(), PROJECT_SLUG, workspace_root, output)
            blueprint_path = project_root / "blueprint.md"
            self.assertTrue(blueprint_path.is_file())
            self.assertIn(PROJECT_SLUG, blueprint_path.read_text(encoding="utf-8"))

    def test_blueprint_does_not_write_under_host_projects(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace_root = Path(directory)
            project_root = workspace_root / "projects" / PROJECT_SLUG
            _seed_research(project_root)
            create_blueprint(object(), PROJECT_SLUG, workspace_root, io.StringIO())
            self.assertFalse((Path("/projects") / PROJECT_SLUG / "blueprint.md").exists())


if __name__ == "__main__":
    unittest.main()
