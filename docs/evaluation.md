# Evaluation

The MVP uses a transparent deterministic baseline, not an LLM. This evaluation measures a bounded routing and workflow implementation, not market demand, language understanding or enterprise business impact.

## Reproduce

From repository root after installing requirements:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/evaluate.py
```

The benchmark writes `docs/evaluation-results.json`. Test databases use pytest temporary directories and do not mutate the running demo.

## Routing benchmark

Thirteen hand-authored synthetic cases cover five responsibility groups, a multi-department production change, unrelated and ambiguous discussion, negation, synonyms, a misleading department-name mention, and an injected instruction. Expectations were authored before reading the implementation. These are a small engineering fixture set, not a representative sample of organizations.

Initial measured result: **10/13 exact matches**, **90.91% micro precision**, **83.33% micro recall**, **2 missed departments**, **1 unnecessary consultation**. Precision is correct suggestions divided by all suggestions; recall is correct suggestions divided by expected departments. Scores count department membership, not ordering or confidence.

The retained challenge failures are useful evidence:

- A three-year vendor agreement costing eighty thousand pounds does not trigger Finance: word-boundary matching misses "costing" and "vendor agreement".
- Exposing customer records to anonymous internet visitors does not trigger Security: the baseline does not infer the security implication.
- "Security" as a meeting-room name produces an unnecessary Security consultation.

Supported fixture cases run as regression tests. Challenge cases remain in benchmark denominators; they are not silently excluded to obtain a passing score. Do not address these failures by adding only these exact phrases and claiming semantic generalization. Evaluate a separately authored, larger paraphrase/negation set before comparing a model-assisted implementation.

## Functional acceptance

Tests cover real asynchronous workflow transitions, persistence across application recreation, no delivery before approval, edited questions, rejected recipients, source ACL filtering, recipient projection, department spoofing, idempotency, stopped workflows, blank inputs, advisory versus formal decisions, structured conflicting/unclear feedback, and explicit decision authority. Measured result: **32 tests passed in 2.05 seconds** on 2026-11-13. This includes create/review/response replay, changed-payload conflicts, overdue escalation deduplication with subsequent response, and an injected failure after the response checkpoint but before consolidation. The failed graph resumes the pending consolidation after application recreation without duplicating the response. An initially failing blank-response test led to request-model whitespace stripping; the repeated test now rejects whitespace-only responses. A privacy-preserving 404 expectation was also corrected in the tests.

## What has not been measured

Question quality is currently a fixed department-specific question paired with literal source evidence. Fidelity tests check that evidence comes from the input and questions remain advisory; they do not prove contextual paraphrase quality. Responses have human-provided stance and actions; extraction accuracy is **not applicable**, since free-text extraction is not implemented. "Contradiction" detection is a disagreement between structured readiness stances, not factual entailment detection.

No claims are made about time saved, reduced unresolved dependencies, user effort, tolerated notification volume, or user satisfaction. Validate those with observed task-based trials against a checklist/rules control. Reliability tests cover normal replay/restart and one injected post-response/pre-consolidation failure. Arbitrary process-kill timing, disk failure and distributed concurrency require additional fault-injection work.
