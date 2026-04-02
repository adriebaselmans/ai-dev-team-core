# TODO

## Highest-Priority Gap

### Prove Live Backend Execution End to End
The framework now supports real execution backends for OpenAI and GitHub Copilot, but current coverage is still based on mocked backend tests rather than full live-provider runs.

What is still missing:
- verify OpenAI execution with a real configured `OPENAI_API_KEY`
- verify GitHub Copilot CLI execution on a machine with `copilot` installed and authenticated
- confirm model identifiers, auth handling, and structured-output behavior against real providers
- add an opt-in integration test path for live backend validation without making normal CI depend on external credentials

Why this matters:
- the orchestration, contracts, and backend adapters are now in place
- the main remaining risk is runtime behavior in real provider environments rather than local framework consistency

Suggested next step:
- add provider-gated integration checks that run only when the required credentials or CLI are available
