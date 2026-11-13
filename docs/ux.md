# Relay UX decisions

The discussion owner reviews evidence and recipient-specific questions before dispatch. A persistent notice names the deterministic baseline. The workspace prioritizes outstanding consultations and concerns, not message volume. The primary journey is create → review exact messages → switch synthetic identity → respond with explicit stance → owner consolidates and records a proposed or approved decision.

Source access is chosen at creation and shown in discussion detail. Restricted sources cannot be sent cross-department. Recipients see their own consultation; owner sees the consolidated brief. The identity switch is explicitly a local demonstration, not enterprise authentication. All user text is escaped before HTML rendering. Inputs have labels, focus indicators, native validation, live error/status feedback and responsive layouts. Approval and supportive input have distinct terminology.

No automatic consultation loop or external notification channel is presented. Overdue checks explicitly record local escalation only. Empty states explain what must happen next. Workflow stopping preserves audit evidence. Decision override requires a visible explanation field.

Usability remains unvalidated: conduct task-based interviews measuring edits/rejections, clicks to completion, time to actionable decision and perceived noise. Current department selection is deliberately small; large-organisation ownership discovery needs its own validated design.

Review refinements: added an ACL-constrained manual stakeholder control to correct omissions; preserved edited questions and selected approvals when adding. Decision forms appear only after all responses; overdue checks appear while waiting. Question length matches the server's 2,000-character limit. Summary metrics count discussions, explicitly labelled as such.

Browser verification: Chromium loaded the actual local API-backed workspace with no page errors. Desktop screenshot `relay-workspace.png` was visually inspected; 390px mobile viewport reported no horizontal overflow (`relay-mobile.png`). Full mutation workflow verification is recorded separately by the orchestrator.
