"""Tests for the frozen workflow contracts."""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone

from pydantic import ValidationError

import src.contracts as contracts
from src.contracts import (
    Claim,
    Competitor,
    CustomerResearch,
    CustomerSegment,
    EvidenceRef,
    GTMStrategy,
    LaunchPack,
    LaunchPhase,
    MarketResearch,
    Persona,
    ProjectRecord,
    StrategicDecision,
    StrategicOption,
)


def make_evidence() -> EvidenceRef:
    return EvidenceRef(
        title="Example Industry Report",
        url="https://example.com/report",
        retrieved_at=datetime(2026, 11, 4, 12, 0, 0, tzinfo=timezone.utc),
        claim_ids=["c1"],
    )


def make_fact_claim() -> Claim:
    return Claim(id="c1", text="The market grew 12% in 2025.", kind="fact", evidence_refs=[make_evidence()])


def make_competitor() -> Competitor:
    return Competitor(
        name="Acme",
        positioning="Enterprise-first",
        pricing="$50k per year",
        strengths=["Distribution"],
        weaknesses=["Slow onboarding"],
        url="https://acme.example.com",
    )


def make_segment() -> CustomerSegment:
    return CustomerSegment(
        name="Mid-market SaaS",
        description="Series A to D companies with 50 to 500 employees",
        characteristics=["In-house recruiting team"],
        pain_points=["Slow scheduling"],
    )


def make_persona() -> Persona:
    return Persona(name="Pat", role="Head of Talent", goals=["Cut time to hire"], pain_points=["No-shows"])


def make_phase() -> LaunchPhase:
    return LaunchPhase(
        name="Pilot",
        timeline="Weeks 1-4",
        activities=["Onboard three design partners"],
        milestones=["First pilot live"],
    )


def make_market() -> MarketResearch:
    return MarketResearch(
        project_id="demo-project",
        generated_at=datetime(2026, 11, 4, 12, 0, 0, tzinfo=timezone.utc),
        summary="Scheduling tools for recruiting teams are crowded but underserved.",
        competitors=[make_competitor()],
        market_opportunities=["Async scheduling for panels"],
        trends=["AI-assisted coordination"],
        claims=[make_fact_claim()],
        assumptions=["Buyers will share calendar data"],
        limitations=["No primary survey conducted"],
    )


def make_customer() -> CustomerResearch:
    return CustomerResearch(
        project_id="demo-project",
        generated_at=datetime(2026, 11, 4, 12, 0, 0, tzinfo=timezone.utc),
        segments=[make_segment()],
        personas=[make_persona()],
        pain_points=["Interview scheduling takes days"],
        buying_triggers=["A failed senior hire"],
        ideal_customer_profile="Series B SaaS with an in-house recruiting team of three or more",
        claims=[make_fact_claim()],
        assumptions=["Recruiters own the tooling budget"],
        limitations=["Persona interviews are unverified"],
    )


def make_gtm() -> GTMStrategy:
    return GTMStrategy(
        project_id="demo-project",
        generated_at=datetime(2026, 11, 4, 12, 0, 0, tzinfo=timezone.utc),
        positioning="The scheduling layer for recruiting panels",
        differentiation="Panel-aware coordination that recruiters do not configure",
        target_segments=["Mid-market SaaS"],
        pricing_hypotheses=["$500 per seat per month"],
        channels=["Founder-led outbound", "Recruiting ops communities"],
        launch_roadmap=[make_phase()],
        risks=["Calendar API rate limits"],
        assumptions=["Design partners will tolerate manual fallback"],
        claims=[make_fact_claim()],
    )


def make_options() -> list[StrategicOption]:
    return [
        StrategicOption(
            id="option-a",
            name="Panel-first",
            thesis="Win on panel coordination quality",
            target_segment="Mid-market SaaS",
            differentiation="Panel-aware sequencing",
            risks=["Longer sales cycle"],
            evidence_refs=[make_evidence()],
        ),
        StrategicOption(
            id="option-b",
            name="Coordinator replacement",
            thesis="Replace coordinator workflows end to end",
            target_segment="Enterprise",
            differentiation="Full workflow coverage",
            risks=["Feature parity pressure"],
            evidence_refs=[make_evidence()],
        ),
    ]


def make_decision() -> StrategicDecision:
    options = make_options()
    return StrategicDecision(
        mode="autonomous",
        selected_option_id="option-a",
        options=options,
        decided_at=datetime(2026, 11, 4, 12, 0, 0, tzinfo=timezone.utc),
        decided_by="supervisor",
        approval_status="auto_approved",
    )


def make_pack() -> LaunchPack:
    return LaunchPack(
        project_id="demo-project",
        idea="AI-assisted interview scheduling for recruiting panels",
        market=make_market(),
        customer=make_customer(),
        gtm=make_gtm(),
        decision=make_decision(),
        evidence_index=[make_evidence()],
    )


def make_record() -> ProjectRecord:
    return ProjectRecord(
        project_id="demo-project",
        idea="AI-assisted interview scheduling for recruiting panels",
        audience="Heads of Talent at mid-market SaaS companies",
        constraints={"timeline": "Launch within two quarters"},
        mode="ambient",
        status="created",
        created_at=datetime(2026, 11, 4, 12, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 11, 4, 12, 30, 0, tzinfo=timezone.utc),
    )


class EvidenceRefTests(unittest.TestCase):
    def test_valid_example_parses(self) -> None:
        self.assertEqual(make_evidence().claim_ids, ["c1"])

    def test_non_http_url_fails(self) -> None:
        with self.assertRaises(ValidationError):
            EvidenceRef(
                title="t",
                url="ftp://example.com/report",
                retrieved_at=datetime(2026, 11, 4, tzinfo=timezone.utc),
                claim_ids=[],
            )

    def test_missing_title_fails(self) -> None:
        with self.assertRaises(ValidationError):
            EvidenceRef(url="https://example.com", retrieved_at=datetime(2026, 11, 4, tzinfo=timezone.utc))


class ClaimTests(unittest.TestCase):
    def test_fact_claim_without_evidence_fails(self) -> None:
        with self.assertRaises(ValidationError):
            Claim(id="c1", text="The market grew.", kind="fact")

    def test_fact_claim_with_evidence_parses(self) -> None:
        self.assertEqual(make_fact_claim().kind, "fact")

    def test_interpretation_without_evidence_parses(self) -> None:
        claim = Claim(id="c2", text="Panels will dominate scheduling pain.", kind="interpretation")
        self.assertEqual(claim.evidence_refs, [])

    def test_empty_text_fails(self) -> None:
        with self.assertRaises(ValidationError):
            Claim(id="c1", text="  ", kind="assumption")


class CompetitorTests(unittest.TestCase):
    def test_valid_example_parses(self) -> None:
        self.assertEqual(make_competitor().name, "Acme")

    def test_non_http_url_fails(self) -> None:
        with self.assertRaises(ValidationError):
            Competitor(name="Acme", positioning="Enterprise-first", url="example.com")

    def test_missing_name_fails(self) -> None:
        with self.assertRaises(ValidationError):
            Competitor(positioning="Enterprise-first")


class CustomerSegmentTests(unittest.TestCase):
    def test_valid_example_parses(self) -> None:
        self.assertEqual(make_segment().name, "Mid-market SaaS")

    def test_missing_description_fails(self) -> None:
        with self.assertRaises(ValidationError):
            CustomerSegment(name="Mid-market SaaS")


class PersonaTests(unittest.TestCase):
    def test_valid_example_parses(self) -> None:
        self.assertEqual(make_persona().role, "Head of Talent")

    def test_missing_role_fails(self) -> None:
        with self.assertRaises(ValidationError):
            Persona(name="Pat")


class LaunchPhaseTests(unittest.TestCase):
    def test_valid_example_parses(self) -> None:
        self.assertEqual(make_phase().name, "Pilot")

    def test_missing_timeline_fails(self) -> None:
        with self.assertRaises(ValidationError):
            LaunchPhase(name="Pilot")


class MarketResearchTests(unittest.TestCase):
    def test_valid_example_parses(self) -> None:
        research = make_market()
        self.assertEqual(research.project_id, "demo-project")
        self.assertEqual(research.competitors[0].name, "Acme")

    def test_missing_summary_fails(self) -> None:
        payload = make_market().model_dump()
        del payload["summary"]
        with self.assertRaises(ValidationError):
            MarketResearch.model_validate(payload)

    def test_fact_claim_without_evidence_fails_inside_artifact(self) -> None:
        payload = make_market().model_dump()
        payload["claims"] = [{"id": "c9", "text": "Unsupported claim.", "kind": "fact", "evidence_refs": []}]
        with self.assertRaises(ValidationError):
            MarketResearch.model_validate(payload)

    def test_unknown_field_fails(self) -> None:
        payload = make_market().model_dump()
        payload["bogus"] = "not allowed"
        with self.assertRaises(ValidationError):
            MarketResearch.model_validate(payload)


class CustomerResearchTests(unittest.TestCase):
    def test_valid_example_parses(self) -> None:
        self.assertEqual(make_customer().ideal_customer_profile[:6], "Series")

    def test_missing_ideal_customer_profile_fails(self) -> None:
        payload = make_customer().model_dump()
        del payload["ideal_customer_profile"]
        with self.assertRaises(ValidationError):
            CustomerResearch.model_validate(payload)


class GTMStrategyTests(unittest.TestCase):
    def test_valid_example_parses(self) -> None:
        self.assertEqual(make_gtm().launch_roadmap[0].name, "Pilot")

    def test_missing_positioning_fails(self) -> None:
        payload = make_gtm().model_dump()
        del payload["positioning"]
        with self.assertRaises(ValidationError):
            GTMStrategy.model_validate(payload)

    def test_malformed_roadmap_phase_fails(self) -> None:
        payload = make_gtm().model_dump()
        payload["launch_roadmap"] = [{"name": "Pilot"}]
        with self.assertRaises(ValidationError):
            GTMStrategy.model_validate(payload)


class StrategicOptionTests(unittest.TestCase):
    def test_valid_example_parses(self) -> None:
        self.assertEqual(make_options()[0].id, "option-a")

    def test_missing_thesis_fails(self) -> None:
        payload = make_options()[0].model_dump()
        del payload["thesis"]
        with self.assertRaises(ValidationError):
            StrategicOption.model_validate(payload)


class StrategicDecisionTests(unittest.TestCase):
    def test_valid_example_parses(self) -> None:
        self.assertEqual(make_decision().approval_status, "auto_approved")

    def test_selected_option_must_exist_in_options(self) -> None:
        payload = make_decision().model_dump()
        payload["selected_option_id"] = "option-z"
        with self.assertRaises(ValidationError):
            StrategicDecision.model_validate(payload)

    def test_fewer_than_two_options_fail(self) -> None:
        payload = make_decision().model_dump()
        payload["options"] = payload["options"][:1]
        with self.assertRaises(ValidationError):
            StrategicDecision.model_validate(payload)

    def test_unknown_mode_fails(self) -> None:
        payload = make_decision().model_dump()
        payload["mode"] = "yolo"
        with self.assertRaises(ValidationError):
            StrategicDecision.model_validate(payload)


class LaunchPackTests(unittest.TestCase):
    def test_valid_example_parses(self) -> None:
        self.assertEqual(make_pack().project_id, "demo-project")

    def test_nested_project_id_mismatch_fails(self) -> None:
        payload = make_pack().model_dump()
        payload["gtm"]["project_id"] = "other-project"
        with self.assertRaises(ValidationError):
            LaunchPack.model_validate(payload)

    def test_missing_decision_fails(self) -> None:
        payload = make_pack().model_dump()
        del payload["decision"]
        with self.assertRaises(ValidationError):
            LaunchPack.model_validate(payload)

    def test_pack_survives_json_round_trip(self) -> None:
        pack = make_pack()
        restored = LaunchPack.model_validate(json.loads(pack.model_dump_json()))
        self.assertEqual(restored, pack)


class ProjectRecordTests(unittest.TestCase):
    def test_valid_example_parses(self) -> None:
        self.assertEqual(make_record().mode, "ambient")

    def test_missing_status_fails(self) -> None:
        payload = make_record().model_dump()
        del payload["status"]
        with self.assertRaises(ValidationError):
            ProjectRecord.model_validate(payload)

    def test_updated_at_before_created_at_fails(self) -> None:
        payload = make_record().model_dump()
        payload["updated_at"] = "2026-11-04T11:00:00+00:00"
        with self.assertRaises(ValidationError):
            ProjectRecord.model_validate(payload)

    def test_empty_constraint_value_fails(self) -> None:
        payload = make_record().model_dump()
        payload["constraints"] = {"timeline": "   "}
        with self.assertRaises(ValidationError):
            ProjectRecord.model_validate(payload)


class ExportTests(unittest.TestCase):
    def test_every_public_contract_is_exported(self) -> None:
        for name in contracts.__all__:
            self.assertTrue(hasattr(contracts, name), name)

    def test_all_is_sorted_and_unique(self) -> None:
        self.assertEqual(list(contracts.__all__), sorted(contracts.__all__))
        self.assertEqual(len(contracts.__all__), len(set(contracts.__all__)))


if __name__ == "__main__":
    unittest.main()
