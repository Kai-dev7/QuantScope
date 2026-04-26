from __future__ import annotations

from typing import Optional

from .models import SkillDefinition, SkillMatchContext
from .registry import SkillRegistry, get_default_skill_registry


class SkillSelector:
    """Select the most suitable skill for the current task context."""

    def __init__(self, registry: SkillRegistry | None = None) -> None:
        self.registry = registry or get_default_skill_registry()

    def select_for_context(self, context: SkillMatchContext) -> Optional[SkillDefinition]:
        candidates = []
        for skill in self.registry.all():
            if skill.selectors.task_type != context.task_type:
                continue
            if skill.selectors.market_scopes and context.market_scope not in skill.selectors.market_scopes:
                continue
            if skill.selectors.research_depths and context.research_depth not in skill.selectors.research_depths:
                continue
            candidates.append(skill)

        if not candidates:
            return None

        # 第一版选择策略：按 version 降序，优先最新定义
        candidates.sort(key=lambda s: (s.version, s.name), reverse=True)
        return candidates[0]
