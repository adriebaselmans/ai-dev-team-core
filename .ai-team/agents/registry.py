from __future__ import annotations

from agents.roles import (
    ArchitectAgent,
    CoordinatorAgent,
    DeveloperAgent,
    DodReviewerAgent,
    ExplorerAgent,
    RequirementsEngineerAgent,
    ReviewerAgent,
    ScoutAgent,
    TesterAgent,
    UXUIDesignerAgent,
)


def build_default_agent_registry() -> dict[str, object]:
    return {
        "coordinator": CoordinatorAgent(),
        "requirements-engineer": RequirementsEngineerAgent(),
        "ux-ui-designer": UXUIDesignerAgent(),
        "explorer": ExplorerAgent(),
        "scout": ScoutAgent(),
        "architect": ArchitectAgent(),
        "developer": DeveloperAgent(),
        "reviewer": ReviewerAgent(),
        "tester": TesterAgent(),
        "dod-reviewer": DodReviewerAgent(),
    }
