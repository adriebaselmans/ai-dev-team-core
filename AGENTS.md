# AI Dev Team Entry Point

This repository is a skeleton for a standard AI-driven development team.

When Codex starts in this repo, use the coordinator workflow defined in [framework/AGENTS.md](/C:/github/ai-dev-team-core/framework/AGENTS.md).

## Default Behavior
- Treat the user request as input for the coordinator.
- Start with the requirements engineer if the request is not fully clear.
- Once the requirements are clear enough, continue autonomously through architecture, development, and testing.
- Return to the user only for requirements clarification and for the final Definition of Done review.

## Output Locations
- Requirements: [docs/requirements/current.md](/C:/github/ai-dev-team-core/docs/requirements/current.md)
- Design: [docs/design/current.md](/C:/github/ai-dev-team-core/docs/design/current.md)
- Source code: [src](/C:/github/ai-dev-team-core/src)
- Team memory: [framework/memory](/C:/github/ai-dev-team-core/framework/memory)

## Team
- Coordinator
- Requirements Engineer
- Architect
- Developer
- Tester
