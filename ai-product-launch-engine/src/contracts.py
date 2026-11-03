"""Frozen data contracts for the launch workflow boundary."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _require_http_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("url must be an absolute HTTP or HTTPS URL")
    return value


class _ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EvidenceRef(_ContractModel):
    title: str = Field(min_length=1)
    url: str = Field(min_length=1)
    retrieved_at: datetime
    claim_ids: list[str] = Field(default_factory=list)

    @field_validator("url")
    @classmethod
    def _url_must_be_http(cls, value: str) -> str:
        return _require_http_url(value)


ClaimKind = Literal["fact", "interpretation", "assumption", "recommendation"]


class Claim(_ContractModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    kind: ClaimKind
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)

    @model_validator(mode="after")
    def _fact_requires_evidence(self) -> "Claim":
        if self.kind == "fact" and not self.evidence_refs:
            raise ValueError("fact claims require at least one evidence reference")
        return self


class Competitor(_ContractModel):
    name: str = Field(min_length=1)
    positioning: str = Field(min_length=1)
    pricing: str | None = None
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    url: str | None = None

    @field_validator("url")
    @classmethod
    def _url_must_be_http(cls, value: str | None) -> str | None:
        return _require_http_url(value) if value is not None else value


class CustomerSegment(_ContractModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    characteristics: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)


class Persona(_ContractModel):
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    goals: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)


class LaunchPhase(_ContractModel):
    name: str = Field(min_length=1)
    timeline: str = Field(min_length=1)
    activities: list[str] = Field(default_factory=list)
    milestones: list[str] = Field(default_factory=list)


class MarketResearch(_ContractModel):
    project_id: str = Field(min_length=1)
    generated_at: datetime
    summary: str = Field(min_length=1)
    competitors: list[Competitor] = Field(default_factory=list)
    market_opportunities: list[str] = Field(default_factory=list)
    trends: list[str] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class CustomerResearch(_ContractModel):
    project_id: str = Field(min_length=1)
    generated_at: datetime
    segments: list[CustomerSegment] = Field(default_factory=list)
    personas: list[Persona] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    buying_triggers: list[str] = Field(default_factory=list)
    ideal_customer_profile: str = Field(min_length=1)
    claims: list[Claim] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class GTMStrategy(_ContractModel):
    project_id: str = Field(min_length=1)
    generated_at: datetime
    positioning: str = Field(min_length=1)
    differentiation: str = Field(min_length=1)
    target_segments: list[str] = Field(default_factory=list)
    pricing_hypotheses: list[str] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=list)
    launch_roadmap: list[LaunchPhase] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)


class StrategicOption(_ContractModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    thesis: str = Field(min_length=1)
    target_segment: str = Field(min_length=1)
    differentiation: str = Field(min_length=1)
    risks: list[str] = Field(default_factory=list)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)


DecisionMode = Literal["autonomous", "ambient"]
DecidedBy = Literal["supervisor", "user", "default"]
ApprovalStatus = Literal["pending", "approved", "auto_approved", "defaulted"]


class StrategicDecision(_ContractModel):
    mode: DecisionMode
    selected_option_id: str = Field(min_length=1)
    options: list[StrategicOption] = Field(min_length=2)
    decided_at: datetime
    decided_by: DecidedBy
    approval_status: ApprovalStatus

    @model_validator(mode="after")
    def _selected_option_must_exist(self) -> "StrategicDecision":
        option_ids = {option.id for option in self.options}
        if self.selected_option_id not in option_ids:
            raise ValueError("selected_option_id must match one of the options")
        return self


class LaunchPack(_ContractModel):
    project_id: str = Field(min_length=1)
    idea: str = Field(min_length=1)
    market: MarketResearch
    customer: CustomerResearch
    gtm: GTMStrategy
    decision: StrategicDecision
    evidence_index: list[EvidenceRef] = Field(default_factory=list)

    @model_validator(mode="after")
    def _nested_project_ids_must_match(self) -> "LaunchPack":
        nested = {
            "market": self.market.project_id,
            "customer": self.customer.project_id,
            "gtm": self.gtm.project_id,
        }
        mismatched = {name: value for name, value in nested.items() if value != self.project_id}
        if mismatched:
            raise ValueError(f"nested project_id values do not match the pack: {sorted(mismatched)}")
        return self


class ProjectRecord(_ContractModel):
    project_id: str = Field(min_length=1)
    idea: str = Field(min_length=1)
    audience: str = Field(min_length=1)
    constraints: dict[str, str] = Field(default_factory=dict)
    mode: DecisionMode
    status: str = Field(min_length=1)
    created_at: datetime
    updated_at: datetime

    @field_validator("constraints")
    @classmethod
    def _constraints_must_be_non_empty_pairs(cls, value: dict[str, str]) -> dict[str, str]:
        for key, item in value.items():
            if not key.strip() or not isinstance(item, str) or not item.strip():
                raise ValueError("constraints must contain non-empty string keys and values")
        return value

    @model_validator(mode="after")
    def _updated_at_not_before_created_at(self) -> "ProjectRecord":
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not be before created_at")
        return self


__all__ = [
    "ApprovalStatus",
    "Claim",
    "ClaimKind",
    "Competitor",
    "CustomerResearch",
    "CustomerSegment",
    "DecidedBy",
    "DecisionMode",
    "EvidenceRef",
    "GTMStrategy",
    "LaunchPack",
    "LaunchPhase",
    "MarketResearch",
    "Persona",
    "ProjectRecord",
    "StrategicDecision",
    "StrategicOption",
]
