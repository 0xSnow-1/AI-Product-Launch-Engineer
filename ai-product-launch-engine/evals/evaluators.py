"""
Evaluators for AI Product Launch Engineer.

This module contains all the grading logic for evaluating the agent system
according to the contract defined in spec.md.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

from langchain_aws import ChatBedrockConverse

from evals.spec import TaskContract


class GradingResult:
    """Result of grading a single aspect of the evaluation."""
    
    def __init__(
        self,
        grader_name: str,
        score: float,
        details: Dict[str, Any],
        passed: bool
    ):
        self.grader_name = grader_name
        self.score = score
        self.details = details
        self.passed = passed


class Evaluator:
    """Base class for all evaluators."""
    
    def __init__(self, name: str):
        self.name = name
        self.llm = ChatBedrockConverse(
            model="anthropic.claude-haiku-4-5-20251001-v1:0",
            region_name="us-east-1"
        )
    
    def grade(self, task: TaskContract, result: Dict[str, Any]) -> GradingResult:
        """Grade the result for the given task."""
        raise NotImplementedError
class ArtifactExistsGrader(Evaluator):
    """Check that all required artifacts exist at the correct paths."""
    
    def __init__(self):
        super().__init__("ArtifactExists")
    
    def grade(self, task: TaskContract, result: Dict[str, Any]) -> GradingResult:
        """Check that required artifacts exist."""
        required_paths = task.expected_artifacts
        workspace = result.get("workspace")
        
        if not workspace:
            return GradingResult(
                grader_name=self.name,
                score=0.0,
                details={"error": "No workspace provided"},
                passed=False
            )
        
        missing_artifacts = []
        for expected_path in required_paths:
            # Convert virtual path to physical path
            physical_path = workspace / expected_path.lstrip("/")
            
            if not physical_path.exists():
                missing_artifacts.append(expected_path)
        
        if missing_artifacts:
            return GradingResult(
                grader_name=self.name,
                score=0.0,
                details={
                    "missing_artifacts": missing_artifacts,
                    "workspace": str(workspace)
                },
                passed=False
            )
        
        # Check for old path schema (contract violation)
        old_paths_found = []
        for artifact in result.get("artifacts", []):
            if artifact.get("path", "").startswith("/workspace/research/"):
                old_paths_found.append(artifact.get("path"))
        
        if old_paths_found:
            return GradingResult(
                grader_name=self.name,
                score=0.5,  # Partial score, but still a failure
                details={
                    "old_paths_found": old_paths_found,
                    "warning": "Using deprecated /workspace/research/ path schema"
class SectionCoverageGrader(Evaluator):
    """Check that required sections are present in artifacts."""
    
    def __init__(self):
        super().__init__("SectionCoverage")
    
    def grade(self, task: TaskContract, result: Dict[str, Any]) -> GradingResult:
        """Check section coverage in artifacts."""
        required_sections = task.expected.get("sections", [])
        artifacts = result.get("artifacts", [])
        
        coverage_details = {}
        total_covered = 0
        
        for artifact in artifacts:
            artifact_path = artifact.get("path", "")
            if not artifact_path:
                continue
            
            # Read artifact content
            workspace = result.get("workspace")
            if not workspace:
                continue
                
            physical_path = workspace / artifact_path.lstrip("/")
            if not physical_path.exists():
                continue
            
            content = physical_path.read_text()
            covered_in_artifact = []
            
            for section in required_sections:
                if self._section_present(content, section):
                    covered_in_artifact.append(section)
            
            if covered_in_artifact:
                coverage_details[artifact_path] = covered_in_artifact
                total_covered += len(covered_in_artifact)
        
        # Calculate score (minimum 70% for pass)
        min_sections = len(required_sections)
        if min_sections == 0:
            score = 1.0
        else:
            score = total_covered / min_sections
        
        passed = score >= 0.7
        
        return GradingResult(
            grader_name=self.name,
            score=score,
class SourceQualityGrader(Evaluator):
    """Check source quality and credibility."""
    
    def __init__(self):
        super().__init__("SourceQuality")
    
    def grade(self, task: TaskContract, result: Dict[str, Any]) -> GradingResult:
        """Check source quality in market research artifact."""
        # Find market research artifact
        market_research_artifact = None
        for artifact in result.get("artifacts", []):
            if "market" in artifact.get("path", "") or "research" in artifact.get("path", ""):
                market_research_artifact = artifact
                break
        
        if not market_research_artifact:
            return GradingResult(
                grader_name=self.name,
                score=0.0,
                details={"error": "No market research artifact found"},
                passed=False
            )
        
        # TODO: In real implementation, this would parse sources.json
        # For now, return a simulated score based on artifact properties
        artifact_path = market_research_artifact.get("path", "")
        size = market_research_artifact.get("size", 0)
        
        # Score based on artifact size and presence of URLs
        score = min(size / 1000.0, 1.0)  # Larger files likely have more content
        
        # Check for required source quality indicators
        workspace = result.get("workspace")
        if workspace:
            physical_path = workspace / artifact_path.lstrip("/")
            if physical_path.exists():
                content = physical_path.read_text()
                url_count = len(re.findall(r'https?://[^\s"\'<>]+', content))
                score = min(score + (url_count / 10.0), 1.0)
        
        passed = score >= 0.6  # At least 60% for passing
        
        return GradingResult(
            grader_name=self.name,
            score=score,
            details={
                "artifact_path": artifact_path,
                "artifact_size": size,
                "url_count": url_count if 'url_count' in locals() else 0,
                "calculated_score": score
            },
class TranscriptValidatorGrader(Evaluator):
    """Check transcript for required agent activities."""
    
    def __init__(self):
        super().__init__("TranscriptValidator")
    
    def grade(self, task: TaskContract, result: Dict[str, Any]) -> GradingResult:
        """Validate transcript completeness."""
        transcript = result.get("transcript", [])
        
        if not transcript:
            return GradingResult(
                grader_name=self.name,
                score=0.0,
                details={"error": "No transcript found"},
                passed=False
            )
        
        # Check for required agent activities
        required_agents = ["market_researcher", "customer_researcher", "gtm_strategist", "supervisor"]
        agent_activities = {}
        
        for entry in transcript:
            agent = entry.get("agent")
            if agent:
                if agent not in agent_activities:
                    agent_activities[agent] = 0
                agent_activities[agent] += 1
        
        # Check that all required agents are present
        missing_agents = [agent for agent in required_agents if agent not in agent_activities]
        
        # Check for minimum activity levels
        low_activity_agents = [agent for agent, count in agent_activities.items() if count < 2]
        
        # Calculate score
        if len(agent_activities) == len(required_agents):
            score = 0.8  # High score for correct agents
            
            if not low_activity_agents:
                score = 1.0  # Perfect score for adequate activity
            else:
                score = 0.6  # Reduced score for low activity
        else:
            score = 0.3  # Very low score if agents missing
        
        passed = score >= 0.6
        
        return GradingResult(
            grader_name=self.name,
            score=score,
class StateCheckGrader(Evaluator):
    """Check final state and blueprint assembly."""
    
    def __init__(self):
        super().__init__("StateCheck")
    
    def grade(self, task: TaskContract, result: Dict[str, Any]) -> GradingResult:
        """Check final state and blueprint assembly."""
        success_indicators = []
        
        # Check if trial was marked successful
        if result.get("success", False):
            success_indicators.append("trial_success")
        
        # Check if artifacts have valid paths
        for artifact in result.get("artifacts", []):
            path = artifact.get("path", "")
            if path and path.startswith("/projects/"):
                success_indicators.append("virtual_path_correct")
            elif path and path.startswith("/workspace/research/"):
                success_indicators.append("old_path_used")
        
        # Check for required metrics
        metrics = result.get("metrics", {})
        if metrics:
            if metrics.get("n_turns", 0) > 0:
                success_indicators.append("transcript_complete")
            
            if metrics.get("n_tool_calls", 0) >= 0:
                success_indicators.append("tool_calls_recorded")
        
        # Calculate score based on success indicators
        score = len(success_indicators) / 4.0  # Max 4 success indicators
        
        # Penalize for old path usage
        if "old_path_used" in success_indicators:
            score *= 0.5  # Heavy penalty for using old path
        
        passed = score >= 0.6
        
        return GradingResult(
            grader_name=self.name,
            score=score,
            details={
                "success_indicators": success_indicators,
                "total_score": score,
                "passed": passed
            },
            passed=passed
        )


# Backward compatibility
if __name__ == "__main__":
    # This allows the module to be imported directly
    print("Evaluation evaluators loaded successfully")
            details={
                "total_entries": len(transcript),
                "agents_present": list(agent_activities.keys()),
                "agent_activities": agent_activities,
                "missing_agents": missing_agents,
                "low_activity_agents": low_activity_agents
            },
            passed=passed
        )
            passed=passed
        )
            details={
                "required_sections": required_sections,
                "coverage_by_artifact": coverage_details,
                "total_covered": total_covered,
                "total_required": min_sections
            },
            passed=passed
        )
    
    def _section_present(self, content: str, section: str) -> bool:
        """Check if a section is present in content."""
        # Convert section name to markdown header pattern
        section_patterns = [
            f"# {section}",
            f"## {section}",
            f"### {section}",
            section.lower()
        ]
        
        # Clean section name for matching
        section_clean = section.lower().replace(" ", "_")
        
        # Check for exact matches or common variations
        content_lower = content.lower()
        
        if section_clean in content_lower:
            return True
        
        # Check for header patterns
        for pattern in section_patterns:
            if pattern.lower() in content_lower:
                return True
        
        return False
                },
                passed=False
            )
        
        return GradingResult(
            grader_name=self.name,
            score=1.0,
            details={
                "total_artifacts": len(required_paths),
                "all_present": True,
                "virtual_paths_used": True
            },
            passed=True
        )