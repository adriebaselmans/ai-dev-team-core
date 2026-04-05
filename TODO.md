# TODO

## Highest-Priority Gap

### Prove Native Host Execution End to End
The framework is now designed around native GitHub Copilot in Visual Studio Code execution, with Codex as the compatibility runtime. Current automated coverage validates contracts, flow behavior, runtime metadata, and native agent profile consistency, but it still does not prove real host-native execution end to end.

What is still missing:
- verify GitHub Copilot in Visual Studio Code with the native `.github/agents/*.agent.md` profiles
- verify Codex compatibility against the same role and flow contracts in a real Codex session
- confirm native handoffs, support-role dispatch, and role selection behave as intended in both hosts
- add an opt-in integration validation path that checks host-native behavior without making normal CI depend on an interactive editor or hosted agent environment

Why this matters:
- the orchestration, contracts, prompts, and native agent profiles are now in place
- the main remaining risk is real host-native behavior rather than local framework consistency

Suggested next step:
- add host-gated integration checks that run only when the required native environment is available
