# Product discovery and initial challenge report

Status: desk research and synthetic MVP scope, 13 November 2026. No interviews, observed enterprise workflows, willingness-to-pay evidence or measured business impact exist for this project.

## Recommendation

Build an **assisted change-consultation ledger**, not a general autonomous collaboration platform. Use a small LangGraph workflow for durable review and response waits; deterministic code owns permissions, state transitions, dispatch budgets and idempotency. Keep analysis behind a replaceable interface. Start with an explicit, explainable rules baseline and measure it before funding live-model integration. This demonstrates coordination mechanics, not general semantic intelligence.

The likely differentiation to test is finding a genuinely missing owner with useful evidence while creating fewer messages than a checklist. Approval routing and summaries alone are already supplied by established products. A Teams/Jira integration could outperform a new board by removing adoption cost; the local board is a controlled test harness, not a validated distribution strategy.

## Most significant challenges

1. **Ownership knowledge is the scarce input.** A model cannot infer decision authority from a department name. Capture a small responsibility catalog and explicit decision owners. Unknown ownership must remain unresolved rather than be invented.
2. **Communication can become the product's failure mode.** A plausible recommendation is not necessarily necessary. Show the trigger and requested decision, allow rejection, limit one question per department per cycle, and suppress duplicates. Measure unnecessary consultations as seriously as missed ones.
3. **Incumbents already cover much of the vision.** Power Automate supports multi-party approvals and Teams responses; Jira has cross-project automation; Rovo markets organizational context and proactive agents. We have not established that these products fail at the proposed task.
4. **Permissions conflict with completeness.** A relevant stakeholder may lack access to the originating content. Fail closed, show the originator an access restriction and require an authorized sharing path. Do not automatically summarize confidential content for unauthorized recipients.
5. **Consensus is not approval.** Conflicting responses require a named accountable human. An extraction or synthesis must never convert silence, “looks fine,” or conditional agreement into formal approval.
6. **Agentic complexity can hide reliability bugs.** Persistence is useful; a network of autonomous department personas is unnecessary for the MVP. Retry and resume behavior must not resend consultations.
7. **Synthetic success can be misleading.** Keyword tests constructed around the same rules establish mechanics only. Hold-out paraphrases, negation, ambiguous language and contradictory statements are needed before semantic claims.

## Evidence checked

These official pages were fetched over HTTPS on 13 November 2026. Product pages describe capabilities and vendor claims; they do not establish independent efficacy or customer demand for this product.

| Source | Observed capability | Product implication |
| --- | --- | --- |
| [Microsoft Power Automate approvals](https://learn.microsoft.com/en-us/power-automate/get-started-approvals) | Start-and-wait approval action; everyone/first/custom/sequential responses; persisted Dataverse approval history; response through Outlook or Teams | Known approval routes do not need an LLM or new discussion board |
| [Jira automation](https://www.atlassian.com/software/jira/features/automation) | Configurable rules, cross-project/global automation and templates | A rules-based comparator must be included; automation itself is not differentiation |
| [Atlassian Rovo](https://www.atlassian.com/software/rovo) | Vendor describes connected people/projects/decisions, agents and proactive assistance | Organizational-context agents are an existing competitive category; no claim of unique capability is supported |
| [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/durable-execution) | URL redirected to persistence documentation; checkpointers preserve thread state; SQLite development and PostgreSQL production persistence described | Useful for multi-step coordination with human pauses; in-memory checkpoints are insufficient |
| [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) | Pausing for external input, resuming with Command, JSON-serializable interrupt payloads, idempotent pre-interrupt side effects | Human approval and asynchronous responses are appropriate graph boundaries |

## Three implementation approaches

| Approach | Strengths | Weaknesses | Best use / decision |
| --- | --- | --- | --- |
| Conventional workflow + rules | Predictable, cheap, auditable, easy to govern; existing automation products may suffice | Requires maintained taxonomy and rules; misses implied dependencies and unfamiliar phrasing | Baseline and preferred production option where routing is stable |
| LLM-assisted discussion board | Can draft tailored questions, propose stakeholders and extract structured candidates | Hallucinated authority, uncertain recall, privacy boundaries; still needs durable business workflow; new board adds adoption cost | Add only if blinded evaluation shows material improvement over rules |
| LangGraph coordination workflow with bounded analysis tools | Durable human waits, resumable steps, explicit state and controlled follow-up paths | More operational/versioning complexity; checkpointing alone does not guarantee transactional dispatch; many agents can amplify noise | Narrow graph justified for this requested experiment; avoid one autonomous agent per department |

These are qualitative engineering trade-offs, not benchmark results. No comparative latency, cost or quality claims have been measured yet.

## MVP journey and boundary

A synthetic infrastructure architect creates a production-system change discussion. The engine identifies candidate departments from concrete content and catalog responsibilities; each recommendation includes evidence and an editable question. The owner approves a selected set or rejects/stops. Only approved, permission-eligible consultations enter department inboxes. Synthetic users respond asynchronously. The system records source responses, proposed decisions, risks/actions and unresolved contradictions, then presents a consolidated owner view. It never claims that consultation completion authorizes the production change.

Include local durable state, explicit demo identities, owner/recipient access checks, separate department responses, editable/rejectable consultation drafts, deduplication, stop control, audit events and repeatable tests. Exclude external messaging, enterprise SSO, autonomous dispatch, organization-wide knowledge ingestion and arbitrary autonomous agent recursion. Demo identity switching is not production authentication.

## Acceptance criteria and measurement

All thresholds below are proposed engineering gates, not achieved results. Record actual outcomes separately in evaluation artifacts.

| Measure | Definition | MVP gate |
| --- | --- | --- |
| Stakeholder precision / recall | Correct recommended departments / all recommendations; correct recommendations / expected departments | Report per scenario and aggregate; separate matching-rule and hold-out cases; never claim real-world accuracy |
| Important dependency recall | Expected critical dependencies surfaced / annotated critical dependencies | Report misses explicitly; critical omission blocks semantic readiness |
| Question fidelity | Questions introduce unsupported requirements, facts or approvals | Zero invented commitments in curated fixtures; human review mandatory |
| Unnecessary consultations | Recommended or sent departments outside annotated necessary set | Report separately; zero sends before approval and zero duplicate sends on replay |
| Extraction correctness | Structured claims match source and preserve proposed vs approved distinction | Explicit provenance; ambiguous text remains unresolved |
| Permission compliance | Unauthorized read, routing, cross-department response and mutation attempts | All tested attempts denied; no confidential text in denied responses |
| Async reliability | Restart, repeated response, repeated approval and out-of-order response cases | Persisted resume; no duplicated notification or lost accepted response |
| Human control | Edit/reject/select/stop operations | Available before dispatch; stop prevents later workflow progression |
| Time / effort | Review interactions and elapsed time to actionable decision | Instrument in later pilot; no reduction claim from synthetic execution |

## Hypotheses requiring human validation

- Five to eight interviews with change owners and consulted departments can establish recent incidents, cost and current workarounds; do not ask merely whether the idea sounds useful.
- Compare the prototype with a checklist + existing workflow on at least 20 anonymized historical changes, annotated independently by two domain experts. Resolve disagreements before scoring.
- Pilot only after privacy review, with explicit participant consent. Compare unnecessary consultations, missed critical dependencies, reviewer editing time and decision cycle time. Avoid attributing improvements to AI without a comparator.
- Advance beyond rules only if an LLM improves held-out critical dependency recall without reducing precision or increasing review effort beyond an agreed budget.
- Prefer integration over a standalone board if users will not maintain a second source of truth. Abandon autonomous dispatch if recipients see the extra communication as bureaucracy or error rates cannot meet the negotiated threshold.
