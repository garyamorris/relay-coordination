# Mission backlog

Owner: Executive Orchestrator. This file records product priorities; implementation status is also tracked in the project's state/evaluation artifacts. Check evidence before changing a task to validated.

## Completed discovery

- [x] Inspect official competitor and LangGraph documentation.
- [x] Publish initial challenge report and three-approach comparison in `discovery.md`.
- [x] Define narrow, human-approved change-consultation MVP and proposed acceptance gates.
- [x] Separate synthetic engineering evidence from unvalidated business hypotheses.

## Active MVP work

- [x] Durable LangGraph review/response workflow with restart and retry checks.
- [x] Functional discussion → editable recommendation → approved consultation → department response → consolidated feedback journey.
- [x] Deterministic access checks and explicit local demo identities.
- [x] Auditable stop/reject controls, proposed decision distinction and duplicate suppression.
- [x] Synthetic evaluation dataset with observed results and known semantic weaknesses.
- [x] Independent security, critical and LangGraph reviews; material finding resolution.
- [x] Reproducible local run and end-to-end demonstration.

## Next after functional validation

1. Add independently annotated hold-out paraphrases, negations and unknown-owner cases; do not tune on the entire evaluation set.
2. Validate product problem with actual change owners and recipients before expanding orchestration.
3. Compare rules against a bounded, permission-filtered LLM adapter only with configured API access and explicit evaluation budget.
4. Assess Teams/Jira integration using a narrowly scoped adapter and reviewable outbox, before committing to standalone adoption.
5. Add enterprise identity, tenant isolation, retention policy and deployment hardening before any sensitive real data.
6. Consider configurable escalation and follow-up only after notification budgets and recipient burden are measured.

## Blockers / limitations

No user research, enterprise integration or production authentication is available. These block claims of business validation and enterprise readiness, not the local synthetic MVP. Deterministic matching cannot establish general language understanding. No external-model quality claims are permitted without a real adapter and held-out evaluation.
