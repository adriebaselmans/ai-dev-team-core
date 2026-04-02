# ai-dev-team-core

Model-agnostic AI dev team framework with:
- flow-driven orchestration as the primary abstraction
- stateless role agents with strict output ownership
- a shared structured state as the single source of truth
- configurable branching, loops, support dispatch, and safe termination
- repository exploration support and reusable repository knowledge storage
- structured requirements/design/review/DoD artifacts for project delivery

## Version
- Current release: `0.9.0`

## What This Repo Is
This repo is a reusable project skeleton.

Copy it for a new project, run `python init.py`, and then give the coordinator a feature request or user need.

The current system is a true orchestration-based AI dev team. It is designed around:
- a coordinator that stays logically in control but remains read-only for product artifacts
- explicit role separation between requirements, design, implementation, review, testing, and DoD validation
- reusable support roles for repository exploration, UX/UI clarification, and external scouting
- data-driven flow definitions in YAML rather than hardcoded agent order
- structured gate results and rework routing instead of string parsing

The default flow supports:
1. coordinator intake and repo-mode classification
2. repository exploration for existing repos
3. requirements clarification
4. optional UX/UI clarification
5. architecture and optional support dispatch
6. development, including optional parallel worker fan-out plus designated integration
7. code review with structured rework decisions
8. testing with automated validation where sensible
9. DoD review against functional and non-functional requirements
10. final coordinator completion

> **WARNING**
> `start.bat` launches Codex with `--ask-for-approval never`. That suppresses approval prompts and can make destructive or unintended actions easier to execute in the wrong workspace. Use it only in a trusted local checkout where you are comfortable with fully autonomous execution.

The coordinator can invoke support roles when work needs repository grounding, UX/UI clarification, or current external research. Roles do not call each other directly; collaboration is mediated through shared state and coordinator-approved support requests.

The active AI-owned project artifacts start empty on purpose:
- `doc_templates/requirements/current.yaml`
- `doc_templates/design/current.yaml`
- `doc_templates/review/current.yaml`
- `doc_templates/dod/current.yaml`
- `framework/memory/*`

Those `doc_templates/*/current.yaml` files stay pristine in the bare skeleton repository. They are populated only in bootstrapped project repositories created from this skeleton, where the active orchestrator writes durable phase artifacts from shared state during real project work.

Structured memory follows the same principle:
- the bare skeleton repo stays pristine
- bootstrapped project repos may persist reusable cross-run knowledge in `framework/memory/records/`
- shared state and phase artifacts remain the source of truth for the active run

Generate user-facing docs only on a release branch with:

```powershell
python -m team_orchestrator.cli export-docs
```

or:

```powershell
pwsh -File framework/scripts/export-release-docs.ps1
```

That writes generated output under `docs/` and is intended to be checked in only when releasing.
In the bare skeleton repository, release-doc export is intentionally disabled. It is enabled only after `init.py` bootstraps a real project repo and records project metadata in `framework/init-metadata.json`.

## Team
- Coordinator
- Requirements Engineer
- UX/UI Designer
- Scout
- Architect
- Developer
- Reviewer
- Tester
- DoD Reviewer
- Repository Exploration Support

## Repo Structure
- `AGENTS.md`: root entry point for Codex.
- `agents/`: stateless role agents and role discovery.
- `team_orchestrator/`: flow execution engine, condition handling, trace logging, and CLI.
- `flows/`: YAML flow definitions.
- `state/`: shared state factory, merge logic, and persistence helpers.
- `framework/config/models.yaml`: role-to-model mapping used by the active orchestrator.
- `.github/skills/`: project-local skills for repeatable role behavior.
- `framework/`: team rules, roles, flow state, memory, and helper scripts.
- `framework/runtime/`: runtime support utilities for state snapshots, artifact export, repository tooling, and optional memory helpers.
- `doc_templates/`: active AI-owned project artifacts.
- `docs/`: user-facing generated documentation output.
- `src/`: implementation code.
- `tests/`: end-to-end and unit coverage for the orchestration system.

## Prerequisites
- Python 3.12+
- `pip`

## Setup
Run the guided bootstrap:

```powershell
python init.py
```

That script checks Python 3.12+, installs dependencies from `pyproject.toml`, validates the repository structure, and captures project metadata for the bootstrap flow.

## How To Use
Start Codex in the repo root.

The root [AGENTS.md](AGENTS.md) tells Codex to use:
- the coordinator workflow in [framework/AGENTS.md](framework/AGENTS.md)
- role mappings in [framework/skills.md](framework/skills.md)
- the runtime support utilities in [framework/runtime/](framework/runtime/)
- the flow-driven orchestration core in `agents/`, `team_orchestrator/`, `flows/`, and `state/`

Example feature request:

```text
Build a small REST API in src for managing tasks with create/list/update/delete, persist data in SQLite, and add tests.
```

Flow orchestration commands:

```powershell
python run_dev_team.py --input "Build a small REST API for tasks"
python -m team_orchestrator.cli --input "Build a small REST API for tasks"
ai-dev-team-run --input "Build a small REST API for tasks"
```

Runtime support commands:

```powershell
python -m team_orchestrator.cli run --input "Build a small REST API for tasks"
python -m team_orchestrator.cli status
python -m pytest framework/runtime/tests -q
```

Generate release-only user-facing docs from `doc_templates/`:

```powershell
python -m team_orchestrator.cli export-docs
pwsh -File framework/scripts/export-release-docs.ps1
```

Repository exploration support is invoked internally by the coordinator when a task needs repository grounding. UX/UI and scout support follow the same coordinator-mediated support-request pattern.

## Runtime Behavior
- The coordinator is the only top-level user-facing agent.
- Flow definitions are data-driven and live in `flows/`.
- Agents are stateless and only return owned state fields.
- Shared state is the single source of truth for execution, trace, and routing decisions.
- Role-to-model assignment is declared in `framework/config/models.yaml` and attached to active orchestration state and trace entries.
- In bootstrapped project repos, the active orchestrator writes durable phase artifacts to `doc_templates/*/current.yaml`; in the bare skeleton repo, those files remain pristine placeholders.
- In bootstrapped project repos, the active orchestrator may also persist reusable cross-run knowledge to `framework/memory/records/`; it does not duplicate current-run state or phase artifacts there.
- Support roles are reusable and coordinator-mediated.
- Review, test, and DoD gates return structured decisions with explicit rework targets.
- The system supports loops, branching, parallel development fan-out, integration, and safe termination.
- Release export and repository support utilities remain in `framework/runtime/`.

## Execution Backends
Execution backend selection is configured in [framework/config/models.yaml](framework/config/models.yaml).

There are two layers:
- `providers`: named provider definitions mapped to concrete backend implementations
- `roles`: role-to-provider and role-to-model assignments, with optional role-level overrides

Built-in backend types:
- `openai_responses`
- `github_copilot_cli`
- `mock`

Provider-level options are merged with role-level options. Role-level options win when both define the same key.

Example configuration:

```yaml
providers:
  openai:
    backend: openai_responses
    env:
      api_key: OPENAI_API_KEY
    options:
      store: false
      reasoning_effort: low
      verbosity: medium

  github-copilot:
    backend: github_copilot_cli
    options:
      executable: copilot
      output_format: text
      silent: true
      no_ask_user: true
      no_custom_instructions: true
      no_auto_update: true
      stream: off

roles:
  scout:
    provider: github-copilot
    model: gpt-5

  architect:
    provider: openai
    model: gpt-5.4
    options:
      reasoning_effort: medium
```

### OpenAI Backend
The OpenAI backend uses the official Responses API with structured JSON-schema output.

Configure it by:
1. setting the provider backend to `openai_responses`
2. exporting the environment variables referenced in that provider's `env` block

Supported environment variables in the default config:
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_ORG_ID`
- `OPENAI_PROJECT_ID`

The default setup now installs the OpenAI Python SDK through `pyproject.toml`.

### GitHub Copilot Backend
The GitHub Copilot backend uses the official `copilot` CLI in programmatic mode.

Configure it by:
1. setting the provider backend to `github_copilot_cli`
2. installing the `copilot` CLI
3. authenticating it on the local machine

Windows install example:

```powershell
winget install GitHub.Copilot
```

Cross-platform npm install example:

```powershell
npm install -g @github/copilot
```

The backend runs `copilot -p` with explicit flags for:
- programmatic prompting
- non-streaming output
- suppressed interactive clarification
- disabled nested repo instruction loading
- least-privilege tool allowances derived from the role tool policy

### How To Switch Backends
Change the `provider` on the relevant role entries in [framework/config/models.yaml](framework/config/models.yaml).

Common patterns:
- keep most roles on OpenAI but move `scout` to GitHub Copilot
- use GitHub Copilot for `developer` while keeping review roles on OpenAI
- point a role back to `mock` while developing the execution layer

The orchestrator and trace metadata record the provider, backend, model, and resolved options for each role.
