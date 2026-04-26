from __future__ import annotations

from typing import Iterable

from .models import ALLOWED_ANALYSTS, SkillDefinition


class SkillValidationError(ValueError):
    """Raised when a skill definition is invalid."""


class SkillValidator:
    """Validate skill definitions loaded from YAML."""

    @staticmethod
    def validate(skill: SkillDefinition) -> None:
        if not skill.name.strip():
            raise SkillValidationError("Skill name must not be empty")
        if skill.version <= 0:
            raise SkillValidationError(f"Skill {skill.name}: version must be > 0")
        if not skill.selectors.task_type.strip():
            raise SkillValidationError(f"Skill {skill.name}: selectors.task_type is required")

        SkillValidator._validate_analysts(skill)
        SkillValidator._validate_tool_policy(skill)
        SkillValidator._validate_execution(skill)

    @staticmethod
    def _validate_analysts(skill: SkillDefinition) -> None:
        enabled = set(skill.analysts.enabled)
        optional = set(skill.analysts.optional)

        SkillValidator._ensure_allowed(
            enabled,
            ALLOWED_ANALYSTS,
            f"Skill {skill.name}: invalid enabled analyst",
        )
        SkillValidator._ensure_allowed(
            optional,
            ALLOWED_ANALYSTS,
            f"Skill {skill.name}: invalid optional analyst",
        )

        if not enabled:
            raise SkillValidationError(f"Skill {skill.name}: analysts.enabled must not be empty")

    @staticmethod
    def _validate_tool_policy(skill: SkillDefinition) -> None:
        enabled = set(skill.analysts.enabled)
        for analyst_name, max_calls in skill.tool_policy.max_tool_calls.items():
            if analyst_name not in enabled:
                raise SkillValidationError(
                    f"Skill {skill.name}: tool_policy.max_tool_calls references non-enabled analyst '{analyst_name}'"
                )
            if int(max_calls) < 0:
                raise SkillValidationError(
                    f"Skill {skill.name}: max tool calls for '{analyst_name}' must be >= 0"
                )

    @staticmethod
    def _validate_execution(skill: SkillDefinition) -> None:
        if skill.execution.debate_rounds < 0:
            raise SkillValidationError(f"Skill {skill.name}: debate_rounds must be >= 0")
        if skill.execution.risk_rounds < 0:
            raise SkillValidationError(f"Skill {skill.name}: risk_rounds must be >= 0")

    @staticmethod
    def _ensure_allowed(values: Iterable[str], allowed: set[str], message: str) -> None:
        for value in values:
            if value not in allowed:
                raise SkillValidationError(f"{message}: {value}")
