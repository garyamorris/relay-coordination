# Reproducible synthetic demonstration

Start the application using the repository README. Keep the passwordless demo server on localhost. Then, in a second terminal from the repository root:

```sh
python scripts/demo.py --base-url http://127.0.0.1:8000
```

The script uses only the Python standard library. It creates a new discussion on each run and retains its state for UI inspection. It performs local demo sign-ins; it does not contact real departments or external messaging services.

Expected flow:

1. Maya proposes replacing a production system, mentioning customer data/access controls, budget/vendor contract, support/runbooks and outage/business hours.
2. Four department suggestions appear, each with matching evidence and a tailored question. No consultation is dispatched yet.
3. Maya explicitly approves the four consultations. Replaying the same request ID must not create duplicates.
4. Sam responds with a Security concern. Finn, Alex and Olivia provide advisory support. Each response contains one explicit action. Recipient reads must exclude the owner summary/audit and other departments' consultations.
5. Response replay must leave exactly four recorded responses.
6. Maya sees one concern, four actions, zero unanswered consultations and a readiness-disagreement signal. The status is `blocked`. There are no inferred formal approvals.

A failed assertion or HTTP error returns exit status 1. Success returns 0 and prints the discussion ID. Sign in as Maya in the browser to inspect its consolidated view and audit trail; switch to a recipient to inspect their consultation.

This demonstrates durable coordination mechanics with synthetic identities and deterministic analysis. The disagreement flag compares explicit stances; it is not a general factual-contradiction detector. Actions and stances are submitted as structured fields, not autonomously inferred from arbitrary text. Passing the demo does not establish stakeholder accuracy on unseen language, reduced decision time or real-world business impact.
