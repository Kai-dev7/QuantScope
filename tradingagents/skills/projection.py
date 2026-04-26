from __future__ import annotations

from app.models.analysis import AnalysisParameters

from .models import SkillDefinition


def project_batch_skill_parameters(
    parameters: AnalysisParameters | None,
    skill_definition: SkillDefinition | None,
) -> AnalysisParameters | None:
    """Project a batch skill's lightweight execution policy into a single-task request.

    Phase 1 intentionally keeps this projection narrow and backward-compatible.
    """
    if parameters is None:
        return None

    projected = parameters.model_copy(deep=True)
    if skill_definition is None:
        return projected

    projected.selected_analysts = list(skill_definition.analysts.enabled)

    # Keep the existing runtime behavior for low-cost batch screening:
    # if the batch skill disables debate and the request is still at basic depth,
    # downgrade it to the fast path for each single-stock task.
    if skill_definition.execution.debate_rounds == 0 and projected.research_depth == "基础":
        projected.research_depth = "快速"

    return projected
