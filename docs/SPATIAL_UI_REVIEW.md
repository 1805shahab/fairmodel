# Spatial workspace correction — November 11, 2026

The owner rejected the retained sidebar and repeated dashboard treatment. This increment replaces those structures in the real application rather than adding another preview. Source snapshot: ignored `.tmp/spatial-before-20261111T003131`.

## Concrete changes

- Removed the desktop sidebar element. Full-width module navigation and a searchable Ctrl+K launcher expose all existing pages. Background content is inert while the launcher is open; Escape restores focus. Role selection keeps the original cookie/API behavior.
- Replaced the overview composition: large artist/studio-specific headings, real 3D voice artwork, unboxed record counts, a prioritized review desk, an ivory financial panel, saved submission objects and compact agreement/invoice records. All counts, cases and amounts come from the existing API. No new business status or fake activity stream was introduced.
- Added `voice-sculpture.tsx` and lazy `voice-stage.tsx`: genuine Three.js closed harmonic tube geometries, directional lighting, pointer/keyboard rotation, pause/play and reset. This is original generative art, explicitly not a voiceprint or identity/usage measurement. It consumes no audio or contract data.
- Added `stage-theme.css`: graphite/ice/chrome surfaces with an ivory financial focal point, shared across public entry and the real working app. AG Grid uses its supported dark color-scheme part. No new package or external model/texture/font download.
- Retained audio timeline/transcript playback, provider provenance, citations, approvals, overlap review, invoice safeguards, backend validation and deterministic money calculations. Source preservation and 37 protected backend/API contract hashes distinguish UI work from business logic changes.

## Interaction and performance

Automatic rotation is capped at 30 rendered updates per second; manual input renders on demand. Pixel ratio is capped at 1.5 on desktop and 1 on explicitly enabled small-screen 3D. Geometry count is reduced on small screens. Offscreen/hidden-tab rendering pauses. Unmount disposes geometry, material, renderer and context. No postprocessing, voice-model weights, microphone capture or continuous financial animation is used.

Small screens start with an SVG still and an explicit Explore in 3D action. Reduced motion stops automatic rotation; manual orientation remains available. A failed/lost WebGL context removes the canvas and displays an honest static fallback while the workflow remains usable. This is not a hardware-performance certification or a cross-browser benchmark.

## Verification

The first complete build passed TypeScript, ESLint and the 17-page production build; all 173 backend tests and Ruff passed. All 16 Playwright checks passed (2.1m), including the four new structural/WebGL cases: no sidebar plus real launcher navigation; successful WebGL rendering and changed rendered pixels after rotation; small-screen opt-in/reduced motion; and a deliberately unavailable WebGL context with working workflow controls.

Existing tests still cover actual local PDF/media/VAD with explicit fixture AI, artist/studio permissions, citation filtering, timestamp seek/highlighting/speed, overlap decisions, royalty approval and simulated settlement. PayPal UI tests mock HTTP responses. No new live Gemini/Groq request, PayPal financial operation, schema change or original-runtime-record write was performed for this UI work.

The first responsive pass completed 76 route/panel checks at 1440/1024/768/390px with zero document overflow/page errors, 44px native players and passing mobile focus trap/Escape return. Screenshots used isolated QA fixture records with keys blanked in the QA process. Original configuration/records were not accessed. Visual inspection found remaining inherited light backgrounds/low-contrast details; those were corrected, and final checks are recorded in PLAN.md.

Final verification: TypeScript, ESLint and the 17-page production Webpack build pass. All **16 Playwright checks pass (2.8m)**; the final input-color correction is additionally covered by **two passing affected form tests (1.4m)**, including the full contract/media/review/simulated-payment workflow and actual computed background/text-color assertions. Backend **173 tests/Ruff pass**, with one existing Starlette deprecation warning. All 37 protected backend/API files remain hash-identical.

The final **76-case responsive pass** again has zero overflow/page errors, actual 44px native players at all four widths and passing mobile focus behavior. Four additional visible-ledger checks confirm ten rendered rows per viewport; offscreen virtualization is not mistaken for missing data. QA captures/reports are under ignored `.tmp/spatial-ui/`, including the actual desktop model in `artist.png`, public entry in `landing.png`, contract/compliance/royalty panels, mobile layouts and visible-ledger screenshots. Main visual findings fixed: remaining inherited light evidence/review/calculation panels, dim summary text and a more-specific legacy field selector overriding the new input theme. No financial behavior was changed to fix presentation.

Final targeted capture `mobile-3d-enabled.png` verifies the actual opt-in WebGL view on a 390px screen. `final-details.json` records correct input colors (background rgb(16,23,34), text rgb(237,242,248)) and no upload-page overflow at all four widths; desktop/mobile upload screenshots were refreshed after that correction. Owned QA servers were stopped after verification. No push or deployment was performed.

The Taste design skill informed this work. Its standalone checker failed to execute in the earlier build; that ERROR is not a passing audit and was not rerun. Project Edge tests and actual screenshot inspection are separate evidence.

## Landing hydration repair

The owner's detailed React warning was reproduced in the development server in Edge. `Still()` regenerated 26 SVG polylines during SSR and browser hydration, serializing unrestricted floating-point coordinates. A direct comparison found 154 of 9,360 coordinates differed between Node and Edge (maximum difference 5.684341886080802e-14). React compares attribute strings exactly, even when the visual difference is imperceptible. Previous checks captured `pageerror` but missed React's console errors.

The fallback is now `frontend/public/voice-sculpture-still.svg`, original static artwork generated offline by `scripts/generate-voice-still.mjs`. A fixed image reference is identical in server/client markup; geometry is not recalculated during hydration. `object-fit: contain` preserves its aspect ratio. The real Three.js renderer, mobile opt-in, reduced-motion controls, failure fallback and workflow behavior remain intact. No new hydration-warning suppression or removal of SSR was used. The new console checks also caught a missing favicon request; `app/icon.svg` supplies the same AudioLines brand mark already used in the app.

Three new Edge checks pass against the development server (18s): desktop/mobile with no console or runtime errors and successful WebGL hydration; and a visible, loaded illustration with JavaScript disabled. All **19 production browser checks pass (2.7m)**, including existing contract/media/review/overlap/payment safeguards. The mobile fallback screenshot was visually inspected (`.tmp/hydration-still-390.png`). TypeScript, ESLint and the 18-page production build pass; all 37 protected backend/API hashes remain unchanged. Backend tests were not rerun for this frontend-only repair. No private configuration, schema, original records, live AI or PayPal operation changed. Static asset regeneration produces identical bytes on this environment. Owned QA servers were stopped; the owner's existing development server was left running.

## Local preview commands

Restart the frontend from the repository root if an old process is serving stale assets:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\frontend.ps1
```

Open `http://127.0.0.1:3000/dashboard`. Desktop loads the sculpture automatically. Drag it or use its rotate/pause/reset controls. On a small window or phone, choose Explore in 3D. The existing backend launch command and provider configuration remain unchanged; no automatic invoice action is added. The public `/` entry uses the same sculpture and leads to this same workspace.
