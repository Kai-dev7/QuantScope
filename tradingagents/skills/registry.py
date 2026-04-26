from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional

from .loader import load_skill_from_yaml
from .models import SkillDefinition, normalize_skill_name
from .validator import SkillValidator


class SkillRegistry:
    """Registry for built-in skill definitions."""

    def __init__(self) -> None:
        self._skills: Dict[str, SkillDefinition] = {}

    def register(self, skill: SkillDefinition) -> None:
        SkillValidator.validate(skill)
        self._skills[normalize_skill_name(skill.name)] = skill

    def get(self, name: str) -> Optional[SkillDefinition]:
        return self._skills.get(normalize_skill_name(name))

    def all(self) -> Iterable[SkillDefinition]:
        return self._skills.values()

    def load_directory(self, directory: str | Path) -> None:
        directory = Path(directory)
        if not directory.exists():
            return
        for path in sorted(directory.glob("*.yaml")):
            self.register(load_skill_from_yaml(path))


_default_registry: Optional[SkillRegistry] = None


def get_default_skill_registry() -> SkillRegistry:
    global _default_registry
    if _default_registry is None:
        registry = SkillRegistry()
        registry.load_directory(Path(__file__).parent / "schemas")
        _default_registry = registry
    return _default_registry
