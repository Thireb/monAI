# monAI Redesign Plan

Started: 2026-10-14 · Owner: @Thireb

Live plan doc (with drawings): https://claude.ai/code/artifact/6baddb49-f80a-494b-a7bb-9b86137ffe46
UI design canvas: https://claude.ai/artifact/25aMehaz4CRseS77K9MbJB

Use this file to track progress. Tick a box when its work is merged to `main`.
Tick a gate only when every check in it passes.

## Summary

Drop the Flutter app. Rebuild the web UI so that it is fun, has no glitches and works well on a phone.

monAI has 2 problems today:

1. **The web UI is not fun.** Users stop after a short time. The budget pages have glitches, for example a hide button that shows 2 times.
2. **The mobile app is not useful.** Sync is weak and the app gives no reason to open it.

A well-built web app can do the app's job on its own. The web already holds all features, and it can be installed on a phone as a PWA. 1 client means 1 set of rules and no sync.

## Progress

### Phase 0 · Fix the glitches

- [x] Load `modal.js` only 1 time (it loaded 2 times on 4 pages); stop the double handlers
- [x] Lock each toggle while its animation runs, so the label always matches the panel
- [x] Stop the summary refresh from nesting a 2nd summary section (the "2 Hide buttons" glitch)
- [x] Make tall modals scroll, so Save and Cancel are reachable on short screens and phones
- [x] Add a unique `(user, month)` constraint on `Budget`; merge existing duplicates in the migration
- [x] Serve the app over HTTPS (`tailscale serve`); install it on a phone as a PWA (works, 2026-10-14)
- [x] Offline: cache CDN files, cache the 12 latest budget months, 4 s network time limit for pages
- [x] Playwright smoke tests for the budget page (`budgetapp/tests/test_budget_page_browser.py`)
- [x] **Gate:** no double modals or wrong labels · all Django tests pass · a new test for duplicate months · PWA installs over HTTPS

### Phase 1 · Foundation

- [x] Colour tokens on `:root` with a dark set; tabular figures for money values (`static/app/css/tokens.css`)
- [x] Template components: card, money value, progress bar, ring, sheet, toast, empty state (`templates/app/components/`, `static/app/css/components.css`)
- [x] Add HTMX; the new `templates/app/base.html` loads only shared code (`static/app/js/app.js`)
- [x] Service layer for all money figures (`budgetapp/services/`), with unit tests
- [x] **Gate:** `base.html` loads shared JS only · the components work on 1 real page · light and dark themes both read well

### Phase 2 · Home, budget month, quick add

- [x] Home (`/app/`): *Safe to spend today*, streak, the month ring, accounts, day-to-day lines, the next 3 bills, goals
- [x] Budget month (`/app/month/<y>/<m>/`): stats, account cards, lines grouped by category, add-a-line form, HTMX partials
- [x] "Day-to-day" flag on lines (`Expense.is_daily`), toggled on the month page; Safe to spend today uses it
- [x] Day-by-day spend chart against the daily limit (from direction B)
- [x] Quick add: `/` or `+` opens the sheet; amount + line chips, or type `groceries 2500 #cash`
- [x] "Added!" reward moment with confetti and Undo (from direction C)
- [x] Phone-first layout: bottom navigation bar and a floating + button; the installed app opens on `/app/`
- [ ] **Gate:** add an expense in 5 s or less · no money math in JavaScript · the owner uses it for 2 weeks

### Retire the Flutter app (after Phase 2)

- [ ] Stop the APK releases. Add a note to the last GitHub release that points Obtainium users to the web app.
- [ ] Move the agent intent mapping in `docs/agent_intent/README.md` off `/api/mobile/…`. It uses those endpoints today.
- [ ] Remove `mobile/budget_mobile/`, `scripts/release_mobile_apk.sh`, `scripts/build_flutter_apk.sh`, `docs/OBTAINIUM.md` and `docs/PLAY_STORE.md`.
- [ ] Remove the `/api/mobile/*` views, `serializers_mobile.py` and `test_mobile_sync.py`. Keep `/api/health/` if a monitor uses it.
- [ ] Update `README.md`, `AGENTS.md` and `CLAUDE.md`.

This removes about 5,900 lines of Dart and about 2,100 lines of mobile sync code and tests on the server.

### Phase 3 · Goals, debts, bills

- [x] Edit and delete lines, and see, add and delete spends and returns, in a line sheet
- [x] Progress rings for goals; a payoff date for each debt (`/app/goals/`, with add money, repay and borrow)
- [x] Bill timeline on the home page and on the month page, with "Add bills to this month"
- [x] Web Push notifications for bill reminders (see `docs/WEB_PUSH.md`; needs a daily timer)
- [x] Offline quick add: save to IndexedDB, send when the network comes back
- [x] Move all other pages to the components: accounts, categories and bill reminders (`/app/more/`), all months (`/app/months/`), income, transfers, PDF email and delete on the month page, goal and debt history, sign-in pages and profile. `/` and the login now open `/app/`
- [x] **Gate:** no jQuery page code remains · Bootstrap removed · every page works in dark mode. The classic UI (`/minimal/`) was removed on 2026-10-15.

### Phase 4 · Fun and reward

- [x] Streaks (the "days under budget" badge on the home page, done in Phase 2)
- [x] Month recap: on the home page in the first 7 days of a month, and at `/app/month/<y>/<m>/recap/`
- [x] Goal celebrations at 25 %, 50 %, 75 % and 100 %, and when a debt is paid off
- [x] Undo toast in place of confirm dialogs (Undo after a spend, "tap again" for deletes; no confirm dialogs remain)
- [x] "Copy last month?" on a new, empty month (done in Phase 2)
- [ ] **Gate:** used 5 days a week for 1 month

## Current state (audit, 2026-10-14)

Most glitches come from 3 causes: scripts that load 2 times, jQuery code that edits the page by hand, and 1 large file for the budget page.

| Problem | Where | Effect for the user |
| --- | --- | --- |
| `modal.js` loads 2 times | `minimal/base.html` and `budget_detail.html` both include it | Each modal click runs 2 to 3 handlers. Modals open with a double animation. |
| Toggle text can go out of sync | `budget_detail.js` lines 689–775 | A second click during the 300 ms animation starts a new animation. The label then says "Hide" when the panel is hidden. |
| Partials replaced with `.html()` / `.replaceWith()` | `updateCategoryStats()`, `updateTagTotals()` | Event handlers and state on the old nodes are lost after each save. |
| 1 file of 1,632 lines | `budget_detail.js` | Each fix risks a new glitch on the same page. |
| Debt and goal JS on every page | `base.html` lines 63–66 | Slower pages and handlers that run where they do not belong. |
| 73 inline `style=` attributes | `templates/minimal/` | The look is not the same from page to page. |
| Client-side money fallback | `updateTagTotalsClientSide()` | Reads numbers back from table cells. It can disagree with the server rules. |

The visual design is also flat. Every page is a list of glass cards with the same weight. Nothing tells the user how the month is going, and nothing rewards a good month.

## Web UI redesign

Make each page answer 1 question in 1 second: "How much can I spend, and am I on track?" Then make each action fast and give a small reward for it.

**Chosen look (decided 2026-10-14):** direction A, *Soft Garden*, is the base. Add the day-by-day spend chart from B and the "Added!" reward moment from C. See the design canvas linked at the top.

### Design direction: "calm money, small wins"

- **1 big number per page.** The home page shows *Safe to spend today* (remaining ÷ days left in the month). Everything else is smaller.
- **Colour means status.** Green = on track, yellow = close to the limit, red = over. Use no other colours for decoration.
- **Soft and round, not glassy.** Keep the friendly feel of Quicksand. Replace the glass cards with flat cards, 16 px corners and 1 soft shadow.
- **Numbers are easy to read.** Use a font with tabular figures for all money values, so that columns line up.
- **Dark mode from day 1.** Define all colours as CSS tokens on `:root`, with a dark set.
- **Motion has a job.** Use anime.js only to show a change: a number counts to its new value, a progress bar fills. Keep each animation at 300 ms or less.

### Key screens

| Screen | New main element | What goes away |
| --- | --- | --- |
| Home | *Safe to spend today*, a month ring (spent vs. income) and the next 3 bills | The long list of cards with the same weight |
| Budget month | 1 card per account tag with a fill bar; expenses grouped by category under it | The 4 summary cards and the 2 "Hide" buttons |
| Quick add | A command bar: press `/` or `+`, type `groceries 2500 #cash`, press Enter | The multi-field expense modal for the common case |
| Expense line | Swipe or hover shows Edit, Split (sub-expense) and Return | Separate buttons on each row |
| Goals and debts | A progress ring per goal, a payoff date per debt | Tables of raw numbers |
| Month recap | A short story at month end: top category, best week, saved amount | Nothing (this is new) |

### Technical approach

Keep Django templates. Replace the jQuery page code with **HTMX + Alpine.js**:

- The server renders each partial (summary, account cards, expense list). HTMX swaps it after a save. This removes the client-side money math and keeps the rule "logic in the backend".
- Alpine.js keeps only small UI state: open or closed, the active filter.
- 1 JS file per page, loaded only on that page. `base.html` loads only shared code.
- Make 1 set of template components: card, money value, progress bar, modal, toast, empty state.
- Remove Bootstrap step by step. The new token CSS and the components replace it.

## Phone use through the web

The web app becomes the only client. It must work as well on a phone as on a laptop. It is already a PWA (it has a manifest and `static/js/service-worker.js`).

**Why the PWA failed before, and the fix.** The first PWA did not work, so the Flutter app was built instead. The likely cause: browsers run a service worker only over HTTPS or on `localhost`. On `http://192.168.x.x:8000` the phone cannot install the app or use it offline. The fix is a real HTTPS address for the server, for example with `tailscale serve`, which gives a trusted certificate. This is checked in Phase 0.

1. **Design for the phone first.** Build each new screen at 375 px wide first.
2. **Install prompt.** After the 3rd visit, offer "Add monAI to your home screen".
3. **Offline quick add.** Only quick add works offline. All other pages show the cached version as read-only.
4. **Bill alerts on the phone.** Web Push works on Android Chrome, and on iPhone from iOS 16.4 when the app is installed.
5. **Reach the server away from home.** Use Tailscale (a private network for your own devices) or an HTTPS host.

## Recommendations

The biggest gain is less typing: most budget apps lose users at data entry, not at reports.

| # | Recommendation | Why | Size | Done |
| --- | --- | --- | --- | --- |
| 1 | Add the unique `(user, month)` constraint now, before any redesign | It is a data bug today. 1 duplicate month breaks the web budget page. | Small | [x] |
| 2 | Auto-copy recurring expenses into a new month | `Expense.is_recurring` exists but the user still builds each month by hand | Small | [x] |
| 3 | Use 1 grammar for quick add, voice and the agent intent schema | `groceries 2500 #cash` can map to the `expense_upsert` action in `docs/agent_intent/` | Medium | [ ] |
| 4 | Add browser smoke tests (Playwright) for the budget page | They catch double modals and wrong labels. The Django tests do not test the UI. | Medium | [x] |
| 5 | Use `Decimal` for money in all views | 37 `float()` calls in `budgetapp/minimal/views/` can make totals differ by a small amount from the PDF. Done: the classic views are removed and the PDF report (`services/report.py`) uses `Decimal`. | Small | [x] |
| 6 | Encrypt `resend_api_key` in the database | It is a plain `CharField` in `accounts/models.py` | Small | [x] |
| 7 | Remove the old one-time commands and `budgetapp/tests.py` | Old migration helpers add noise. `tests.py` breaks `manage.py test budgetapp.tests`. | Small | [x] |
| 8 | Later: import a bank statement (CSV) to suggest expenses | The user checks a list of suggested expenses and taps "Add". This is much less typing. | Large | [ ] |
| 9 | Measure use before you build more | The request middleware already logs each view. Count which pages people open, then cut or improve. | Small | [ ] |

## Decisions

| Decision | Choice | Status |
| --- | --- | --- |
| Mobile client | Drop the Flutter app; the web (PWA) is the only client | Decided 2026-10-14 |
| UI look | A · Soft Garden, plus B's daily chart and C's reward moment | Decided 2026-10-14 |
| Front-end stack | HTMX + small vanilla JS (Alpine.js not needed so far) | Decided 2026-10-14 (default) |
| Remote access | Tailscale, with `tailscale serve` for HTTPS | Decided 2026-10-14 |
| Who uses monAI | Only the owner and family (default), or public users | Open |
| Bootstrap | Remove it in Phase 3 (default), or keep it and only restyle | Removed with the classic UI (2026-10-15) |
| Flutter code | Delete it from the repo (default), or move it to an archive branch first | Open |
