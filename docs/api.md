# Local API contract
All mutation bodies JSON; all routes except login/users require `Authorization: Bearer <token>`. Local demo login intentionally has no password; never expose beyond localhost.

- GET `/api/users` -> `[{id,name,department,role}]`; POST `/api/login` `{user_id}` -> `{token,user}`.
- GET `/api/departments` -> `[{id,name,responsibility}]`.
- GET `/api/discussions` -> array of visible discussion summaries `{id,title,status,owner_id,created_at}`.
- POST `/api/discussions` `{title,body,allowed_departments?:[department IDs]}` -> owner detail.
- GET `/api/discussions/{id}` -> detail.
- POST `/api/discussions/{id}/review` `{consultations:[{department,question,approved}],request_id?:string}` -> detail. Owner only, once, explicitly approve or reject each recommendation; added departments permitted only with source ACL. Max five.
- POST `/api/discussions/{id}/responses` `{department,text,stance:'support'|'concern'|'unclear',actions?:[{text,owner,due_date?}],request_id?:string}` -> detail. Only authenticated department recipient, only dispatched question, once per department.
- POST `/api/discussions/{id}/stop` `{}` -> detail. Owner only.
- POST `/api/discussions/{id}/decision` `{text,status:'proposed'|'approved',request_id?:string}` -> detail. Owner designated decision authority; approved requires all responses and no concern/unclear (or explicit `override_reason`).
- POST `/api/discussions/{id}/escalate` `{}` -> detail. Owner only; marks unanswered overdue consultation once; no external delivery.

Detail owner: `{id,title,body,owner_id,status,allowed_departments,created_at,consultations:[{department,department_name,reason,evidence,question,approved,status,due_at}],responses:[{id,department,text,stance,actions,created_at}],summary:{text,risks,actions,contradictions,outstanding,decisions,assumptions,dependencies},audit:[{at,event,actor,detail}],analysis_mode:'deterministic-baseline'}`.
Recipient detail includes source title/body (only when source ACL authorizes) and own dispatched consultation/responses. `summary` and `audit` are not included. Recipient role cannot approve/review/stop. GET list only includes dispatched discussions for recipient.

Statuses: `review_required`, `awaiting_responses`, `ready_for_decision`, `blocked`, `closed`, `stopped`. User IDs: `maya` (infrastructure), `sam` (security), `finn` (finance), `alex` (support), `olivia` (operations). Any logged-in user may create a discussion and owns it.

Implementation notes: application binds demo sessions to server-issued random bearer tokens (hashes stored in SQLite); login is deliberately passwordless and does not establish real identity. Request IDs are scoped to actor and operation, with payload fingerprints: retries are returned without duplicate effects and changed payloads receive 409. Create supports `request_id` and `escalation_hours` (1–720, default 48). Escalation is explicitly checked by the owner and only records a local dashboard event; no scheduler or external notification transport exists. Run one Uvicorn worker only. Reads resume checkpointed pending computation, but never automatically resume a human interrupt.

Structured response stance/actions are supplied by recipients rather than inferred by a model. A concern/support disagreement flags readiness for human review; it does not establish a factual contradiction. Consultation scope is capped at five departments and one reviewed batch. No automatic recursive outreach is implemented.
