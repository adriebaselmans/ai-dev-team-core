# TODO

## Highest-Priority Gaps

### Prove Native Host Execution End to End
Automated coverage validates contracts, flow behavior, runtime metadata, phase artifacts, memory behavior, and native profile consistency. It still does not prove real host-native execution end to end.

Acceptance items:
- verify `.github/agents/*.agent.md` profiles in a native project-agent host
- verify instruction-file fallback behavior in a second host without adding provider-specific rules
- confirm handoffs, support-role dispatch, role selection, and hidden specialist profiles behave as intended
- add opt-in integration validation that runs only when the required host environment is available

### Tighten RTK Token Controls
The skeleton now declares phase context profiles, but runtime enforcement can go further.

Acceptance items:
- keep loader/validator coverage for `.ai-team/context/policy.yaml` and `.ai-team/context/adapters.yaml`
- add optional state trace entries for context profile, compact mode, and budget decisions
- keep wiki reads index-first and profile-scoped
- measure token policy results without storing raw transcripts
