# Browser validation

Executed `node scripts/browser-test.cjs` against localhost:8000 using installed Playwright and `/usr/bin/chromium`.

Passed: UI discussion creation; four grounded suggestions; exact question edit; explicit approval; four synthetic identity switches and department responses with owners/deadlines; consolidated concern/support disagreement; zero outstanding responses; no JavaScript page errors; desktop screenshot; 390px mobile screenshot and no horizontal page overflow.

Inspected screenshots: `artifacts/desktop.png` and `artifacts/mobile.png`. This is functional/responsive QA, not a full accessibility audit or user study. Test writes only synthetic local records.
