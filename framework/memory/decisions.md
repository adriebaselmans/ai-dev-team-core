# Decisions

Legacy or exported readable decision summary derived from structured memory when needed.

## Entry Format
- Date
- Decision
- Context
- Reason
- Consequence

## Rules
- Treat this file as optional readable output, not the canonical write path.
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
- 2026-03-29
  Decision: Make the structured local memory store the machine-readable source of truth and keep the markdown memory files as human-readable projections.
  Context: The memory redesign needs a first-class local subsystem that stays inspectable, deterministic, and integrated into the dev-team workflow.
  Reason: A structured store enables deterministic querying, supersession, and role-scoped retrieval while preserving the readable narrative layer in markdown.
  Consequence: Development should add record, query, and projection helpers and keep `project-log.md`, `decisions.md`, and `known-context.md` synchronized with the structured records.
- 2026-03-29
  Decision: Use a small v1 record taxonomy of fact, decision, brief, question, and contradiction.
  Context: The memory subsystem needs enough structure to support stable facts, phase summaries, open issues, and explicit conflict handling without growing into a general-purpose platform.
  Reason: A narrow taxonomy keeps the implementation bounded and deterministic while still covering the dev-team workflow needs.
  Consequence: Query and projection helpers should understand these record kinds explicitly, and future record kinds should be added only when a concrete use case appears.
- 2026-03-29
  Decision: Drive role memory through named context-slice recipes instead of a single hardcoded brief lookup.
  Context: The runtime now needs role-specific memory bundles that can combine phase briefs, decisions, facts, questions, and contradictions.
  Reason: Named recipes keep memory retrieval declarative, deterministic, and easy to extend without scattering selection logic across the runtime.
  Consequence: Future memory changes should update `context_slices.yaml` and the query helper, not embed ad hoc memory selection in specialist code.
- 2026-03-29
  Decision: Separate memory capture, retrieval, and markdown projection as distinct runtime responsibilities.
  Context: The memory subsystem must become first-class without turning the runtime into a tightly coupled monolith or reintroducing markdown scraping as the operational API.
  Reason: Explicit boundaries keep the subsystem local-first and deterministic while making orchestration, phase compaction, and context slicing integrate through stable interfaces.
  Consequence: Phase flow should capture through the structured store first, context slicing should retrieve through query helpers, and human-readable memory files should be refreshed through projection helpers instead of being edited as the primary source.
- 2026-03-29
  Decision: Retire synchronized markdown projections and treat human-readable memory files as optional on-demand exports only.
  Context: The architecture correction removed the requirement to keep markdown outputs synchronized with the structured memory store.
  Reason: A single durable memory source avoids dual-write drift and keeps the runtime contract simpler and more deterministic.
  Consequence: `project-log.md`, `decisions.md`, and `known-context.md` are no longer part of the canonical memory write path; if a readable snapshot is needed, a separate export path may generate it from structured records.
