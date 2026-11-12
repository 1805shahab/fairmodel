# Recording-studio ledger redesign

Frontend-only work, November 12, 2026. Backend, API contracts, provider adapters, environment files, database and Postman collection are protected by a 60-file SHA-256 inventory in ignored `.tmp/ledger-redesign/protected.json`.

## Audit and baseline

- Baseline: 370 backend tests; TypeScript, ESLint, production Webpack build; all 28 Edge browser tests passed.
- Captured 21 routes/views at 375, 768 and 1280px (63 screenshots) before implementation. Files and overflow manifest: `.tmp/ledger-redesign/before/`. QA uses a separate database, blank provider keys and explicit offline fixtures. No private runtime records were modified.
- Problems: five competing palette layers, repetitive rounded panels, low hierarchy between provider commentary and financial eligibility, long unbounded citations, oversized dashboard headers and small secondary controls.
- Accessibility gaps to address: status relied on colored dots, undersized sculpture controls, no theme choice, inconsistent muted text and a custom dialog lacking a primitive-backed focus boundary.

## System and sequence

1. Shared shell, semantic tokens, local typography and theme choice.
2. Contract source/terms review, mobile view switching and activation consequences.
3. Recording controls and evidence hierarchy, advisory content separated from deterministic conclusions.
4. Ledger/grid presentation, exact decimal text, pinned amount column and compact record cards.
5. Provider-labelled invoices, awaiting-confirmation wording and existing explicit financial controls.
6. Consistency across uploads, reviews, passports, audit and integration settings; component reference at `/design-system`.

Paper/ink/vermilion tokens live in `frontend/app/ledger-theme.css`, exposed to Tailwind v4 through `frontend/tailwind.config.ts`. Historical CSS retains structural layouts but references semantic colors. Instrument Serif, Geist and JetBrains Mono are self-hosted with their open-source licenses. Motion is limited to short interaction feedback; existing reduced-motion and off-screen Three.js safeguards remain. The sculpture is original art and never biometric evidence.

## Behavior boundaries

- Existing API calls, payloads, types and workflow state remain in place. Presentation does not infer paid status or recalculate money. The display formatter keeps backend decimal text unchanged.
- The API supports approval of a complete version, not durable per-term approvals or a version-decline operation. The interface allows editing individual fields and withholding activation, and explicitly describes whole-version approval. It does not invent saved term approvals.
- Generation is one explicit provider operation followed by the existing analysis workflow. The progress copy describes actual local request state, not invented server stages or guaranteed duration.
- Source highlights use actual verified quotations. They do not create PDF annotations or invent missing citations.
- Sandbox payment actions and confirmations remain unchanged. Mock completion remains explicitly simulated; it is never described as verified PayPal settlement.

## Verification

Final verification on November 12:

| Check | Result |
|---|---|
| Backend regression suite | 370 passed; one existing Starlette deprecation warning |
| Frontend TypeScript / ESLint | Passed |
| Production Webpack build | Passed; 22 generated pages |
| Edge browser suite | 33 passed, including all 28 existing workflow regressions |
| axe AA scans | No violations on seven main surfaces in both themes; no violations in eight mocked Sandbox invoice states |
| Responsive screenshots | 63 after captures at 375/768/1280px; zero horizontal overflow |
| Additional states | 24 captures: studio generation, source highlight, dark mode, invoice states, loading/empty/error and 200% reflow |
| 1080p demo captures | Five priority screens plus read-only ledger details captured at 1920×1080 |
| Read-only grid inspection / CSV | Passed; zero backend write requests |
| Protected source inventory | All 60 SHA-256 hashes unchanged |

The intentional HTTP 503 error fixture produces the expected browser resource-error message; other state captures have no page or console errors. The 200% reflow check uses a 640-CSS-pixel layout at device scale 2, equivalent to the available layout width of a 1280px browser at 200%. A preliminary CSS `zoom` experiment did not trigger media queries and overflowed; it is not represented as a successful browser-zoom test.

The existing exact RGB assertions were updated to the requested paper/ink palette. Existing role, label and test-id selectors remain intact. New tests cover verbatim decimal display (including precision beyond two decimals), persistent theme selection, launcher focus restoration, accessible grid headers, both-theme axe scans and compact reflow. Initial failures from the changed landing heading/dialog name were corrected by preserving those accessible names. The component reference intentionally includes a persistent loading specimen; the new test now accounts for that demonstration.

### Grid visibility fix

During the accessibility audit, AG Grid's delayed flex-sizing guard left headers and rows hidden. Explicit resizable column widths remove that startup dependency. Pagination, sorting, numeric financial filters, text search and CSV remain available. `ensureDomOrder` and disabled row/column virtualisation keep the paginated DOM available for assistive technology. The viewport is keyboard-focusable; the grid is labelled through its supported API. No test rule is disabled or excluded to pass axe. Guidance: [AG Grid accessibility documentation](https://www.ag-grid.com/react-data-grid/accessibility/).

### Artifacts

- [Before/after comparison gallery](../.tmp/ledger-redesign/comparison.html): five priority views plus analytics.
- Before and after responsive inventories: `.tmp/ledger-redesign/before/manifest.json`, `.tmp/ledger-redesign/after/manifest.json`.
- Additional states and their verification: `.tmp/ledger-redesign/after-states/manifest.json`.
- 1920×1080 captures, CSV and read-only request evidence: `.tmp/ledger-redesign/demo-1080p/`.
- Source snapshot and protected inventory: `.tmp/ledger-redesign/before-source/`, `.tmp/ledger-redesign/protected.json`.

Artifacts stay ignored and contain only isolated fictional fixture records. Full-page screenshots are visual review artifacts; scrolling/sticky source columns and lazy grid rendering are also checked interactively.

### Remaining limits

- This is automated accessibility and developer keyboard/visual QA, not WCAG certification or external user research. Native browser/audio/PDF controls retain browser-specific behavior.
- Whole-version contract activation remains the existing API boundary. No durable per-term approval/decline API, PDF annotation engine or new generation-stage telemetry was invented.
- All provider/financial browser verification uses explicit fixtures or mocked HTTP. No live Gemini/Groq/Fish/PayPal operation was performed or newly verified by this redesign.
- Installation reported eight moderate dependency advisories. Broad dependency upgrades were not attempted in this frontend-only change. A non-blocking module-type warning from Tailwind configuration remains; the verified build continues to use Webpack for Windows compiler compatibility.
- No schema migration, environment change, runtime-data reset, push or deployment occurred. Existing demo-persona authentication limitations remain.

## Run and check on Windows

Keep the existing backend running with its current provider/write permissions. In a frontend terminal from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\frontend.ps1
```

Open `http://127.0.0.1:3000` and `/design-system`. Restart an already-running frontend in its own terminal if it needs to load the newly installed packages; do not start a second process on the same port.

```powershell
Push-Location .\frontend
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
Pop-Location
.\backend\.venv\Scripts\python.exe -m pytest backend/tests -q
```

Browser tests must target the isolated QA backend with blank keys and mock payments, as documented in `docs/TESTING.md`; never point fixture-seeding tests at private runtime records or a Sandbox-writing server. The run for this milestone used backend 8102 / production frontend 3101 and `PLAYWRIGHT_BASE_URL=http://127.0.0.1:3101`.

## Follow-up: spacing, scroll narrative and footers

The November 12 follow-up addresses the owner's spacing and footer feedback:

- `layout-refinement.css` shares a 1440px centered content frame and responsive gutters across the header, pages and footers. Single-form pages fill that frame rather than stopping at an inconsistent 880px width.
- Studio generation uses a bounded, keyboard-scrollable history column when records exist. Empty history stacks below a full-width form, avoiding a blank sidebar. A regression test caught and corrected a legacy panel overflow rule that otherwise prevented scrolling.
- `ProductWalkthrough` advances License → Analyze → Evaluate → Authorize → Invoice from native scroll position, with a sticky scene, short text transitions and a progress line. It reverses on upward scrolling. No wheel events are intercepted, no timers advance tabs, and no provider/API request is triggered by scrolling.
- Click and keyboard selection remain available. Reduced motion and short viewports use the compact static alternative. Reserved scene height prevents differences in copy length from clipping the final mobile step.
- `SiteFooter` provides a public directory and compact workspace footer with matching content edges, real app links, the brand/tagline and explicit demo/test labels. It adds no fabricated legal/contact pages and is omitted from print snapshots.

Verification: 370 backend tests and the full 37-case browser regression suite passed. The final 18 targeted checks also pass after the subsequent scene-height and empty/populated-history refinements. TypeScript, ESLint and the 22-page Webpack build pass. Both-theme axe checks remain active. Twenty-four screenshots at 375/768/1280/1920px and the developer verification manifest are saved under `.tmp/layout-refinement/`; the 12 route/width combinations show no overflow, the landing axe scan has no violations, and no console/page errors were recorded. All 60 protected source hashes remain unchanged. No environment, backend, provider, financial or private-runtime-data changes were made.
