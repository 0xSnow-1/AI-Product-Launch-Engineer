"""Tests for the specialist artifact validation boundary."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from src.contracts import MarketResearch
from src.workflows.validation import (
    ArtifactValidationError,
    artifact_path,
    load_artifact,
    validate_project,
)

PROJECT_SLUG = "validation-fixture"
NOW = datetime(2026, 11, 4, tzinfo=UTC).isoformat()


def market_research_payload() -> dict:
    return {
        "project_id": PROJECT_SLUG,
        "generated_at": NOW,
        "summary": "Narrow recruiting niche with a clear gap.",
        "competitors": [
            {
                "name": "Example ATS",
                "positioning": "Applicant tracking with add-ons",
                "url": "https://example.com/ats",
            }
        ],
        "market_opportunities": ["Small agencies lack structured intake notes"],
        "trends": ["Remote intake calls are common"],
        "claims": [
            {
                "id": "claim-1",
                "text": "Remote intake calls are common.",
                "kind": "fact",
                "evidence_refs": [
                    {
                        "title": "Occupational Outlook Handbook",
                        "url": "https://www.bls.gov/ooh/business-and-financial/human-resources-specialists.htm",
                        "retrieved_at": NOW,
                        "claim_ids": ["claim-1"],
                    }
                ],
            }
        ],
        "assumptions": ["Agencies will pilot within 90 days"],
        "limitations": ["No primary survey was run"],
    }


def customer_research_payload() -> dict:
    return {
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


def gtm_strategy_payload() -> dict:
    return {
        "project_id": PROJECT_SLUG,
        "generated_at": NOW,
        "positioning": "The intake-call assistant for small recruiting agencies",
        "differentiation": "Structured notes and ATS follow-up actions",
        "target_segments": ["Small US recruiting agencies"],
        "pricing_hypotheses": ["Low monthly fee per recruiter"],
        "channels": ["Direct outreach", "ATS marketplaces"],
        "launch_roadmap": [
            {"name": "Pilot", "timeline": "Weeks 1 to 6", "activities": ["Recruit ten agencies"]}
        ],
        "risks": ["ATS integration access delays the pilot"],
        "assumptions": ["Agencies accept a paid pilot"],
        "claims": [],
    }


_ARTIFACT_RELATIVE_PATHS = {
    "market_research": "research/market_research.json",
    "customer_research": "research/customer_research.json",
    "gtm_strategy": "strategy/gtm_strategy.json",
}


def _write(project_root: Path, kind: str, payload: object | None) -> None:
    path = project_root / _ARTIFACT_RELATIVE_PATHS[kind]
    path.parent.mkdir(parents=True, exist_ok=True)
    if payload is None:
        return
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload), encoding="utf-8")


def _seed_project(project_root: Path) -> None:
    _write(project_root, "market_research", market_research_payload())
    _write(project_root, "customer_research", customer_research_payload())
    _write(project_root, "gtm_strategy", gtm_strategy_payload())


class LoadArtifactTests(unittest.TestCase):
    def test_valid_json_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory) / "projects" / PROJECT_SLUG
            _seed_project(project_root)
            artifacts = validate_project(project_root)
        self.assertIsInstance(artifacts["market_research"], MarketResearch)
        self.assertEqual(artifacts["customer_research"].project_id, PROJECT_SLUG)
        self.assertEqual(artifacts["gtm_strategy"].project_id, PROJECT_SLUG)

    def test_missing_field_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory) / "projects" / PROJECT_SLUG
            payload = market_research_payload()
            del payload["summary"]
            _write(project_root, "market_research", payload)
            with self.assertRaises(ArtifactValidationError) as raised:
                load_artifact(project_root, "market_research")
        self.assertIn("summary", str(raised.exception))

    def test_fact_claim_without_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory) / "projects" / PROJECT_SLUG
            payload = market_research_payload()
            payload["claims"][0]["evidence_refs"] = []
            _write(project_root, "market_research", payload)
            with self.assertRaises(ArtifactValidationError) as raised:
                load_artifact(project_root, "market_research")
        self.assertIn("evidence", str(raised.exception).lower())

    def test_missing_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory) / "projects" / PROJECT_SLUG
            project_root.mkdir(parents=True)
            with self.assertRaises(ArtifactValidationError) as raised:
                load_artifact(project_root, "customer_research")
        self.assertIn("customer_research.json", str(raised.exception))

    def test_malformed_json_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory) / "projects" / PROJECT_SLUG
            _write(project_root, "gtm_strategy", "{not json")
            with self.assertRaises(ArtifactValidationError) as raised:
                load_artifact(project_root, "gtm_strategy")
        self.assertIn("gtm_strategy.json", str(raised.exception))

    def test_non_object_root_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory) / "projects" / PROJECT_SLUG
            _write(project_root, "gtm_strategy", "[1, 2]")
            with self.assertRaises(ArtifactValidationError):
                load_artifact(project_root, "gtm_strategy")

    def test_validate_project_stops_on_first_invalid_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory) / "projects" / PROJECT_SLUG
            _write(project_root, "customer_research", customer_research_payload())
            _write(project_root, "gtm_strategy", "{broken")
            with self.assertRaises(ArtifactValidationError):
                validate_project(project_root)

    def test_artifact_path_uses_canonical_locations(self) -> None:
        project_root = Path("/tmp/root/projects/demo")
        self.assertEqual(
            artifact_path(project_root, "market_research"),
            project_root / "research" / "market_research.json",
        )
        self.assertEqual(
            artifact_path(project_root, "gtm_strategy"),
            project_root / "strategy" / "gtm_strategy.json",
        )


if __name__ == "__main__":
    unittest.main()
