# Native Agents

These custom agent profiles are the primary execution surface for this skeleton in GitHub Copilot in Visual Studio Code.

The canonical framework contract still lives in:
- `framework/AGENTS.md`
- `framework/runtime/team.yaml`
- `flows/software_delivery.yaml`
- `framework/roles/*.md`
- `framework/prompts/*`

Each agent profile mirrors one framework role. The coordinator owns user-facing intake and handoffs. Support roles are only used through coordinator-mediated handoffs.
All workspace agent profiles are explicitly targeted at VS Code. Only the coordinator is intended to be user-selectable; specialist roles stay hidden from the picker and are reached only through coordinator-mediated subagent dispatch.
