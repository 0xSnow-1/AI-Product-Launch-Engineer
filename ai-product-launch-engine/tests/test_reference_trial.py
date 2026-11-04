"""The known-good reference trial must pass every artifact grader."""

from __future__ import annotations

import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from evals.evaluators import (
    ArchiveGrader,
    ArtifactExistsGrader,
    ArtifactSchemaGrader,
    DeprecatedPathGrader,
    ManifestGrader,
    PlaceholderGrader,
    SectionCoverageGrader,
    SourceCitationGrader,
)
from evals.task_loader import load_tasks


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET = PROJECT_ROOT / "evals" / "datasets" / "capability" / "b2b_recruiting_meeting_assistant.json"
REFERENCE_ROOT = PROJECT_ROOT / "evals" / "reference" / "b2b_recruiting_meeting_assistant"
ARCHIVE_FILES = (
    "research/market_research.json",
    "research/customer_research.json",
    "strategy/gtm_strategy.json",
    "blueprint.md",
    "manifest.json",
)
ARTIFACT_GRADERS = (
    ArtifactExistsGrader(),
    DeprecatedPathGrader(),
    ArtifactSchemaGrader(),
    SectionCoverageGrader(),
    SourceCitationGrader(),
    ManifestGrader(),
    ArchiveGrader(),
    PlaceholderGrader(),
)


class ReferenceTrialTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = load_tasks(DATASET)[0]
        self.project_relative = Path("projects") / self.task.expected.project_slug

    def _build_trial(self, trial_root: Path) -> None:
        shutil.copytree(REFERENCE_ROOT, trial_root, dirs_exist_ok=True)
        project_root = trial_root / self.project_relative
        with zipfile.ZipFile(project_root / "deliverable.zip", "w") as archive:
            for name in ARCHIVE_FILES:
                archive.write(project_root / name, arcname=name)

    def test_reference_trial_passes_every_artifact_grader(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            trial_root = Path(temporary_directory)
            self._build_trial(trial_root)
            results = tuple(grader.grade(self.task, trial_root) for grader in ARTIFACT_GRADERS)
        failures = [result.to_dict() for result in results if not result.passed]
        self.assertFalse(failures, failures)
        self.assertEqual(
            [result.grader_name for result in results],
            [
                "artifact_exists",
                "deprecated_path",
                "artifact_schemas",
                "section_coverage",
                "source_citations",
                "manifest",
                "archive",
                "placeholders",
            ],
        )

    def test_reference_trial_does_not_commit_a_zip(self) -> None:
        project_root = REFERENCE_ROOT / self.project_relative
        self.assertFalse((project_root / "deliverable.zip").exists())


if __name__ == "__main__":
    unittest.main()
