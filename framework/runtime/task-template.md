# Subagent Task Template

Use this template when the coordinator spawns a specialist subagent.

## Role
`<role-name>`

## Objective
`<bounded task objective>`

## Owned Outputs
- `<artifact or files this subagent owns>`

## Inputs
- `<required docs, code areas, memory, and role/skill files>`

## Constraints
- Stay within current requirements and design.
- Follow the assigned role definition.
- Follow the assigned skill instructions.
- Reuse provided repository knowledge when it exists instead of rediscovering the same context.
- Do not communicate with the user.
- Do not edit files outside the owned output set unless explicitly required.

## Completion Criteria
- `<what must be true for the task to be complete>`

## Return Format
- Summary of what was done
- Risks or blockers
- Explicit completion status
