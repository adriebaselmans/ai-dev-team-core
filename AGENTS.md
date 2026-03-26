# AI Dev Team Entry Point

This repository is a skeleton for a standard AI-driven development team.

When Codex starts in this repo, use the coordinator workflow defined in [framework/AGENTS.md](/C:/github/ai-dev-team-core/framework/AGENTS.md).

## Default Behavior
- Treat the user request as input for the coordinator.
- Move through the coordinator phases defined in `framework/AGENTS.md`.
- Use the project-local skills in `.github/skills/` and the role mapping in `framework/skills.md` where applicable.
- Use the Codex-first runtime contract in `framework/runtime/` for native subagent spawning.
- Use the Explorer when work must be grounded in a specific repository or application.
- Start with the requirements engineer if the request is not fully clear.
- Once the requirements are clear enough, continue autonomously through architecture, development, review, and testing.
- Treat install, build, test, local run, commit, tag, push, and release actions as implicitly approved by default; execute them without pausing for conversational approval when the environment allows it.
- Return to the user only for requirements clarification and for the final Definition of Done review.

## Output Locations
- Requirements: [docs/requirements/current.md](/C:/github/ai-dev-team-core/docs/requirements/current.md)
- Design: [docs/design/current.md](/C:/github/ai-dev-team-core/docs/design/current.md)
- Review: [docs/review/current.md](/C:/github/ai-dev-team-core/docs/review/current.md)
- Source code: [src](/C:/github/ai-dev-team-core/src)
- Team memory: [framework/memory](/C:/github/ai-dev-team-core/framework/memory)

## Team
- Coordinator
- Explorer
- Requirements Engineer
- Architect
- Developer
- Reviewer
- Tester
