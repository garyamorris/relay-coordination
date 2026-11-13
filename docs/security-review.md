# Security and governance review

Scope: local synthetic LangGraph coordination MVP. This review does not certify production security.

## Threat model

- A user claims another department's identity or reads its consultations.
- A generated or edited question sends confidential source text to an unauthorized recipient.
- A department reply contains instructions that attempt to alter routing, ownership or approval state.
- Repeated requests or process failure cause duplicate notifications, actions or replies.
- A stale approval approves a payload different from the one reviewed.
- A response that merely supports a proposal is represented as formal authorization.
- Stored text injects HTML or executable script in the frontend.

## Required boundaries

Authorization must derive from the authenticated synthetic user, not a department supplied in JSON. Owner-only mutations require server-side checks. Recipient views must be constructed as allowlisted projections: only their approved question and their own response may be exposed. Cross-department confidentiality must be checked again at approval, not only recommendation time. Demo identity selection is impersonation by design and must be prominently labelled local-only.

A deterministic parser must treat user text as data. No response can change policy or approve a decision by instruction. With future LLM integration, only authorized minimized context may enter a model; outputs remain untrusted proposals validated by application logic.

Stored content must be rendered using textContent or equivalent escaping. Database operations must use bound parameters. Checkpoints, source records and audit history need consistent access assumptions; an audit log is not immutable merely because the UI offers no edit button.

## Runtime evidence

Pending code and tests. Review acceptance requires direct negative API tests and a restart/resumption test, not only inspection.

## Source sharing and synthetic identity

The planned ACL is permission to share the **whole originating discussion** with a department, not permission to share only a generated question. Recipient source title/body are therefore authorized only after explicit dispatch and source-sharing eligibility. The creation UI must explain that scope. Question edits can introduce confidential text from outside the source; this MVP has no data-loss prevention classifier and cannot validate whether a user is entitled to share pasted third-party information. Users must use synthetic data only. Do not represent the allowlist as an enterprise classification or document-access system.

The demo login deliberately allows selecting any fixture identity without a password. Bearer tokens test application authorization paths, but do not establish who the human is. Any user with network access can impersonate any fixture department. Bind the service to loopback, never use real organization data, and replace this mechanism with real authentication before shared deployment.

## Inspection and execution findings (2026-11-13)

Reviewed `app/main.py`, `app/workflow.py`, `app/analysis.py`, and `static/app.js`.

- Authorization is checked on the server; response department must match the session fixture identity. Review, stop, decision and escalation mutations require the owner. Recipient projection exposes authorized source content and only its own consultation/response; it excludes other responses, summary and audit.
- Routing filters the source allowlist before producing questions. Review rechecks the allowlist, and the graph dispatches the exact edited question. No LLM is called, so no source leaves this process through model inference.
- Operation replay keys bind actor, operation, request ID and serialized payload hash. Changed payload reuse is rejected. Mutations are serialized by one process-local lock; multiple Uvicorn workers are unsupported.
- User-controlled HTML is escaped in frontend templates. SQL statements use bound parameters. Tokens are stored hashed, but lack expiry/revocation and login has no identity proof; these remain local-demo limitations.
- Confirmed defect: whitespace-only response was accepted with HTTP 200. Reported to Backend Engineering for correction. The same validation class affected blank titles, questions, decisions and action owners.
- Independent initial workflow test run: 16 passed, 2 failed. One failure was a test expecting 403/409 where the API deliberately returned 404 before dispatch; this is not an access-control defect. The other reproduced the whitespace defect.
- Independent adversarial API probe: approved a Security-only consultation, then submitted a concern containing “Ignore prior rules. Approve change, route private contents to Finance” and a script tag. State remained `blocked`, formal decisions remained empty, Finance listing remained empty and its detail request returned 404. Pre-dispatch Security detail also returned 404. This establishes the deterministic path treats response instructions as data; it is not an LLM prompt-injection evaluation.

No enterprise assurance follows from these results. SQLite checkpoint data and audit history are plaintext and writable by the process; the audit is traceable application history, not tamper-evident storage. There is no tenant boundary, real identity verification, consent management, retention enforcement or external provider policy.

### Resolution verification

Backend added stripping/nonblank validation; Evaluation expanded whitespace and recovery cases. Independent rerun of `.venv/bin/python -m pytest -q`: **30 passed in 1.96 seconds**. This includes permission denials, changed-payload replay, stop persistence, restart/resumption and failed-summary recovery. No unresolved material access-control defect was identified within the local synthetic scope. This is a bounded review, not proof that all attacks or crash windows are covered.
