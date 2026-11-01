"""Validated data types at the product boundary."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping


MAX_IDEA_LENGTH = 500
MAX_AUDIENCE_LENGTH = 200
SLUG_PART_PATTERN = re.compile(r"[a-z0-9]+")


def _required_string(value: Any, field: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    result = value.strip()
    if len(result) > maximum:
        raise ValueError(f"{field} must contain at most {maximum} characters")
    return result


def slugify(value: str) -> str:
    """Create the stable project slug used by all canonical artifact paths."""

    slug = "-".join(SLUG_PART_PATTERN.findall(value.lower()))
    if not slug:
        raise ValueError("idea must contain at least one letter or number")
    return slug[:80].rstrip("-")


@dataclass(frozen=True)
class LaunchRequest:
    """One user request to create a launch blueprint."""

    idea: str
    audience: str
    constraints: Mapping[str, str]
    project_slug: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "LaunchRequest":
        """Validate request input and derive its canonical project slug."""

        idea = _required_string(raw.get("idea"), "idea", MAX_IDEA_LENGTH)
        audience = _required_string(raw.get("audience"), "audience", MAX_AUDIENCE_LENGTH)
        raw_constraints = raw.get("constraints", {})
        if not isinstance(raw_constraints, Mapping):
            raise ValueError("constraints must be an object")
        constraints: dict[str, str] = {}
        for key, value in raw_constraints.items():
            if not isinstance(key, str) or not key.strip() or not isinstance(value, str) or not value.strip():
                raise ValueError("constraints must contain non-empty string keys and values")
            constraints[key.strip()] = value.strip()
        supplied_slug = raw.get("project_slug")
        if supplied_slug is not None:
            project_slug = _required_string(supplied_slug, "project_slug", 80)
            if project_slug != slugify(project_slug):
                raise ValueError("project_slug must use lowercase hyphenated words")
        else:
            project_slug = slugify(idea)
        return cls(idea=idea, audience=audience, constraints=constraints, project_slug=project_slug)
