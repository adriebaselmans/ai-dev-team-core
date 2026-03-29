# Decisions

Use this file for important project decisions that future agents must understand.

## Entry Format
- Date
- Decision
- Context
- Reason
- Consequence

## Rules
- Record only meaningful decisions.
- Prefer one clear decision entry per topic.
- Include why the decision was made, not only what was chosen.
- Update this file when a decision changes; do not silently overwrite the old rationale.

## Entries
- No project decisions yet.
- 2026-03-29
  Decision: Keep doc_templates/ untouched this iteration and record phase outcomes in framework/memory/ instead.
  Context: The user requested code-quality improvements across export rendering, task input derivation, and model placeholder handling while preserving skeleton artifacts.
  Reason: The repository policy for this iteration explicitly prioritizes source/runtime changes and memory updates over generated workflow artifacts.
  Consequence: Architecture and later phases should treat framework/memory/project-log.md as the phase record, and development must not rely on doc_templates/current.yaml artifacts being updated.
- 2026-03-29
  Decision: Make markdown_sections the single source of truth for export_docs rendering.
  Context: The export path currently uses generic key-value rendering, which can drift from schema-defined document structure.
  Reason: Schema-driven rendering removes per-artifact branching and keeps output shape co-located with the schema.
  Consequence: Any artifact missing markdown_sections must be fixed in its schema rather than patched in the renderer.
- 2026-03-29
  Decision: Derive task_builder available inputs from actual artifacts, role specs, and skill contracts.
  Context: Hardcoded input strings are prone to drift as skills and roles change.
  Reason: Derivation from ARTIFACT_FILES, team.yaml writes, and skill contract required_inputs makes validation reflect the real repository state.
  Consequence: Missing inputs should produce clear validation errors that name both the missing input and the requiring skill.
- 2026-03-29
  Decision: Treat placeholder model names as explicit mock-only configuration.
  Context: The mock backend currently accepts non-real model identifiers without distinguishing intentional placeholders from accidental misconfiguration.
  Reason: A placeholder flag makes mock configuration deliberate and fail-fast when a real provider wiring is expected.
  Consequence: Mock dispatch must reject roles lacking placeholder: true, and tests must stop asserting only on raw model name strings.
- 2026-03-29
  - Decision: Keep `doc_templates/` untouched for this iteration and record phase outcomes in `framework/memory/` instead.
  - Context: The current improvement pass needs requirements, architecture, review, testing, and DoD phase tracking without editing the generated workflow artifacts.
  - Reason: This preserves the repository skeleton while still capturing phase outcomes and delivery history.
  - Consequence: The coordinator and specialist flow should treat `framework/memory/project-log.md` as the persistence target for this iteration.
- 2026-03-29
  Decision: Resolve skill contracts by explicit declared path, not basename aliasing.
  Context: The current loader collapses skill references to the final path segment, which can alias distinct contract locations.
  Reason: A multi-agent automation skeleton needs deterministic contract resolution and clear missing-contract errors.
  Consequence: Contract loading and its tests should treat the declared path as authoritative unless an alias is explicitly part of the contract.
- 2026-03-29
  Decision: Stage startup validation before committing the initial runtime state.
  Context: `cmd_start` can currently leave the runtime in a started state even if the first dispatch envelope cannot be built.
  Reason: An autonomous orchestrator should fail before committing state when the launch payload is invalid.
  Consequence: The start flow should validate or build the first envelope first, then persist state only on success or roll back on failure.
- 2026-03-29
  Decision: Keep the artifact-versus-memory boundary explicit and narrow for this iteration.
  Context: The runtime still uses artifacts for phase artifacts and memory for coordination support.
  Reason: The review finding called for an explicit guardrail, not a full architecture rewrite.
  Consequence: Consumers should document and enforce the canonical source for phase data without redesigning the entire memory model.
