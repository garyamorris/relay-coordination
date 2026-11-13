# Relay — cross-department coordination experiment

Local, synthetic coordination platform using **real LangGraph interrupts and SQLite checkpoints**. Human-approved consultation, department inboxes, asynchronous replies, decisions and an audit trail.

**Analysis is a deterministic baseline, not an LLM.** This experiment tests coordination mechanics and establishes a comparator. It does not prove semantic understanding, market demand or business impact. See [discovery](docs/discovery.md) for the challenge report and competing approaches.

## Run locally

```bash
cd /workspace/coordination
python -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Keep one server worker. Login uses synthetic identities with no password and is **for loopback-only demonstration**. Do not enter confidential or real enterprise data.

## Demonstration

1. Select Maya (Infrastructure). Create the example production replacement discussion.
2. Inspect the evidence and department-specific questions. Edit a question or reject a recommendation, then explicitly approve delivery.
3. Switch identities to Finance, Security, Support or Operations. Each sees only their authorized, dispatched consultation. Submit a response and explicit stance; optional actions name an owner and deadline.
4. Return to Maya. Inspect outstanding dependencies, evidence, concerns, contradictory stances and the audit history. A supportive reply is not a formal decision.
5. Propose a decision. Formal approval requires completed, clear feedback or a recorded human override. Stop is available to prevent further consultation progress.
6. Restart the server while a workflow is waiting, then continue from the same discussion.

All inbox deliveries stay in this application; no email, Teams, Slack or other external messages are sent.

## Validation and project records

```bash
.venv/bin/python -m pytest -q
.venv/bin/python scripts/evaluate.py
```

- [Architecture and decision register](docs/architecture.md)
- [API contract](docs/api.md)
- [Team and acceptance gate](docs/team.md)
- [Current status](docs/status.md) and [backlog](docs/backlog.md)
- [Synthetic evaluation](docs/evaluation.md)
- [Independent critical review](docs/critical-review.md) and [security review](docs/security-review.md)

Production identity, tenant isolation, external integrations, autonomous dispatch and semantic model inference are outside this local experiment. Additional consultation rounds are bounded out of the first slice to prevent notification loops. Evaluate a conventional workflow implementation alongside this before investing further.

Browser acceptance (requires Node Playwright and Chromium):

```bash
node scripts/browser-test.cjs
```

The supplied environment already has both. Override `CHROMIUM_PATH` or `BASE_URL` when needed. The browser test creates synthetic data and verifies creation, edited approval, four department replies, disagreement consolidation, desktop/mobile layout and absence of browser errors. Screenshots are in `artifacts/`.

Reproduce the HTTP scenario with `.venv/bin/python scripts/demo.py`; see [demo instructions](docs/demo.md).
