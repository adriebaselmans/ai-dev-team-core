# ai-dev-team-core

Simple skeleton for an AI-driven development team.

## Structure
- `AGENTS.md`: root entry point for Codex.
- `.github/skills/`: project-local skills for repeatable role behavior.
- `framework/`: team rules, roles, flow state, memory, and helper scripts.
- `docs/`: current requirements and design.
- `src/`: implementation code.

## Team
- Coordinator
- Requirements Engineer
- Architect
- Developer
- Reviewer
- Tester

## Expected Flow
1. Start Codex in the repo root.
2. Give the coordinator a user need or feature description.
3. The requirements engineer asks questions if the request is unclear.
4. Once clear, the team works autonomously through design, implementation, review, and testing.
5. The tester prepares a Definition of Done review.
6. User feedback starts the next iteration.

## Skills
- Roles define ownership and decision boundaries.
- Skills define how recurring work is performed.
- Project-local skills live in `.github/skills/`.
- Role-to-skill mapping lives in `framework/skills.md`.
