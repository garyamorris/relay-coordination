# Autonomous engineering organisation

Executive orchestrator: integration, acceptance, demonstration, durable handoff.

| Worker | Accountabilities | Owned artifacts |
|---|---|---|
| Product discovery / strategy | Research, challenge assumptions, prioritise | discovery.md, backlog.md |
| Solution architecture / LangGraph specialist | ADRs, state lifecycle, independent graph review | architecture.md |
| Backend engineering | API, data, access boundaries, graph | app/, requirements.txt, api.md |
| UX / frontend engineering | Journeys, responsive working interface | static/, ux.md |
| AI evaluation | Synthetic reference cases, security and workflow regressions | tests/, scripts/evaluate.py, evaluation.md |
| Independent critical / security review | Challenge implementation and product value | critical-review.md, security-review.md |

Roles share bounded workers where separation adds no value. Runtime graph nodes are not engineering agents. Reviewers do not own implementation. Shared checkout uses disjoint file ownership; only the orchestrator integrates and commits after checks. No external messages or enterprise integrations are dispatched.

## Acceptance gate

Working local UI/API: create discussion → evidence-backed recommendations → human edits/rejection/approval → department-scoped inbox → asynchronous replies → consolidated evidence/conflicts/actions. Durable checkpoint waits survive recreation. Duplicate submissions do not create duplicate notifications. Unauthorized recipients cannot read the original. Stop prevents further progress. Deterministic analysis is explicitly labelled and evaluated as a baseline, not semantic AI capability. Documentation records limitations and unvalidated demand.
