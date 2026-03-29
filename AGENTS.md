# AI Dev Team Entry Point

This repository is the entry point for the AI dev team framework.

When Codex starts in this repo, use the coordinator workflow defined in [framework/AGENTS.md](framework/AGENTS.md).

## Default Behavior
- Treat the user request as input for the coordinator.
- Move through the coordinator phases defined in `framework/AGENTS.md`.
- Use the project-local skills in `.github/skills/` and the role mapping in `framework/skills.md` where applicable.
- Use the model-agnostic runtime contract in `framework/runtime/` for bounded specialist dispatch.
- Treat the coordinator as read-only with respect to implementation work and delegate file-writing work to specialist roles or shared tools.
- Use repository exploration support when work must be grounded in a specific repository or application.
- Start with the requirements engineer if the request is not fully clear.
- Once the requirements are clear enough, continue autonomously through architecture, development, review, and testing.
- Treat install, build, test, local run, commit, tag, push, and release actions as implicitly approved by default; execute them without pausing for conversational approval when the environment allows it.
- Return to the user only for requirements clarification and for the final Definition of Done review.

## Output Locations
- Requirements: [doc_templates/requirements/current.yaml](doc_templates/requirements/current.yaml)
- Design: [doc_templates/design/current.yaml](doc_templates/design/current.yaml)
- Review: [doc_templates/review/current.yaml](doc_templates/review/current.yaml)
- User-facing generated docs: [docs](docs)
- Source code: [src](src)
- Team memory: [framework/memory](framework/memory)

## Team
- Coordinator
- Requirements Engineer
- Architect
- Developer
- Reviewer
- Tester
- Repository exploration support
