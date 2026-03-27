# Skills Mapping

This file maps team roles to project-local skills and reusable external skills.

## Role To Skill Mapping
- Coordinator
  Primary: `.github/skills/coordinator-flow`
  Supporting: `.github/skills/memory-update`
  Supporting: `.github/skills/compaction`
  Runtime: `framework/runtime/team.yaml`, `framework/runtime/workflow.yaml`, `framework/runtime/task-template.md`
- Requirements Engineer
  Primary: `.github/skills/requirements-clarification`
- Architect
  Primary: `.github/skills/architecture-design`
  Optional external: `openai-docs`, `security-threat-model`, `security-best-practices`
- Developer
  Primary: `.github/skills/implementation-clean-code`
  Supporting: `.github/skills/unit-testing`
- Reviewer
  Primary: `.github/skills/code-review`
  Optional external: `security-best-practices`
- Tester
  Primary: `.github/skills/acceptance-testing`
  Optional external: `playwright`, `security-best-practices`

## Shared Support Skills
- Repository exploration: `.github/skills/repository-exploration`
- Repository knowledge compaction: `.github/skills/repository-knowledge-compaction`
- Compaction: `.github/skills/compaction`

## Reusable OpenAI Skills
Based on the current curated OpenAI skill list, these are the best fits for this repository when installed:
- `openai-docs`
- `playwright`
- `security-best-practices`
- `security-threat-model`
- `doc`

## Rule
- Prefer project-local skills for workflow-specific behavior and artifact conventions.
- Use reusable external skills only when they fit without fighting the repository's role and artifact model.
- For runtime orchestration, treat `framework/runtime/` as the machine-readable subagent contract.
