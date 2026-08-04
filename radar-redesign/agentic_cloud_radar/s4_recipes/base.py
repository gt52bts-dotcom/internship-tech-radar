"""Skill 4 recipe contract.

Skill 4 creates real AWS resources, so it never improvises. Every deployable
implementation is declared here as a ``RecipeDefinition`` with the full contract
filled in, and a candidate that matches no definition stops at
``needs_new_recipe`` instead of receiving a template someone guessed at.

The contract exists because the dangerous failure is not "no recipe found" — it
is a plausible-looking recipe assembled on the spot. Declaring cleanup strategy,
success criteria, IAM actions and stop conditions up front means a reviewer sees
what will be created, how it will be torn down, and what would make the run stop,
all before anything is deployed.

A definition may be registered as a draft (``deployable=False``). Drafts record
the design work for a candidate that is worth evaluating but not yet safe to
deploy; the registry refuses to hand them to the deployer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


RISK_LEVELS = ("low", "medium", "high")

# Every field a deployable recipe must fill in before the registry will release
# it to Skill 4. Drafts are exempt: they exist precisely to record what is still
# missing.
REQUIRED_FOR_DEPLOYABLE = (
    "estimated_cost_model_id",
    "deployable_resource_types",
    "required_iam_actions",
    "deployment_inputs_schema",
    "success_criteria",
    "evidence_to_collect",
    "cleanup_strategy",
    "cleanup_verification",
)


@dataclass(frozen=True)
class RecipeDefinition:
    """One candidate family's deployable (or drafted) PoC implementation."""

    recipe_id: str
    display_name: str
    supported_candidate_patterns: tuple[str, ...]
    required_aws_services: tuple[str, ...]
    required_region_capabilities: tuple[str, ...]
    estimated_cost_model_id: str | None
    deployable_resource_types: tuple[str, ...]
    required_iam_actions: tuple[str, ...]
    approval_required_fields: tuple[str, ...]
    deployment_inputs_schema: dict[str, Any]
    success_criteria: tuple[str, ...]
    evidence_to_collect: tuple[str, ...]
    cleanup_strategy: str | None
    cleanup_verification: tuple[str, ...]
    risk_level: str
    stop_conditions: tuple[str, ...]
    unsupported_conditions: tuple[str, ...]

    # Deployability. A draft carries the same contract but is refused by the
    # registry, and records what still has to be resolved.
    deployable: bool = True
    poc_directory: Path | None = None
    needs_region_confirmation: bool = False
    needs_environment_preparation: bool = False
    needs_cost_model: bool = False
    draft_notes: tuple[str, ...] = field(default_factory=tuple)
    display_name_zh: str = ""

    # ---- contract checks -------------------------------------------------

    def contract_gaps(self) -> list[str]:
        """Return the contract fields a deployable recipe is still missing."""

        gaps: list[str] = []
        for name in REQUIRED_FOR_DEPLOYABLE:
            value = getattr(self, name)
            if not value:
                gaps.append(name)
        if self.risk_level not in RISK_LEVELS:
            gaps.append("risk_level")
        if self.deployable and self.poc_directory is None:
            gaps.append("poc_directory")
        return gaps

    def blocking_flags(self) -> list[str]:
        """Return the unresolved preconditions that keep a recipe undeployable."""

        flags: list[str] = []
        if self.needs_region_confirmation:
            flags.append("needs_region_confirmation")
        if self.needs_environment_preparation:
            flags.append("needs_environment_preparation")
        if self.needs_cost_model:
            flags.append("needs_cost_model")
        return flags

    def is_deployable(self) -> bool:
        return self.deployable and not self.contract_gaps() and not self.blocking_flags()

    def matches(self, haystack: str, services: set[str]) -> bool:
        """Match a candidate by title/url text or by its detected services."""

        text = haystack.lower()
        lowered_services = {s.lower() for s in services}
        for pattern in self.supported_candidate_patterns:
            token = pattern.lower()
            if token.startswith("service:"):
                if token.split(":", 1)[1].strip() in lowered_services:
                    return True
            elif token in text:
                return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Serialise for artifacts and reports."""

        return {
            "recipe_id": self.recipe_id,
            "display_name": self.display_name,
            "display_name_zh": self.display_name_zh or self.display_name,
            "supported_candidate_patterns": list(self.supported_candidate_patterns),
            "required_aws_services": list(self.required_aws_services),
            "required_region_capabilities": list(self.required_region_capabilities),
            "estimated_cost_model_id": self.estimated_cost_model_id,
            "deployable_resource_types": list(self.deployable_resource_types),
            "required_iam_actions": list(self.required_iam_actions),
            "approval_required_fields": list(self.approval_required_fields),
            "deployment_inputs_schema": dict(self.deployment_inputs_schema),
            "success_criteria": list(self.success_criteria),
            "evidence_to_collect": list(self.evidence_to_collect),
            "cleanup_strategy": self.cleanup_strategy,
            "cleanup_verification": list(self.cleanup_verification),
            "risk_level": self.risk_level,
            "stop_conditions": list(self.stop_conditions),
            "unsupported_conditions": list(self.unsupported_conditions),
            "deployable": self.is_deployable(),
            "declared_deployable": self.deployable,
            "contract_gaps": self.contract_gaps(),
            "blocking_flags": self.blocking_flags(),
            "draft_notes": list(self.draft_notes),
            "poc_directory": str(self.poc_directory) if self.poc_directory else None,
        }
