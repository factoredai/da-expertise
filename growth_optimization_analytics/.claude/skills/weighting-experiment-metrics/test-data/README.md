# Test data — weighting-experiment-metrics

Synthetic eval sets for the skill:
- `scenarios.json` — 10 general/cross-industry cases (C1–C10).
- `scenarios-marketing.json` — 10 marketing-mapped cases (M1–M10): campaign
  acquisition, lifecycle/retargeting expansion, welcome-flow activation;
  unsubscribe attrition, promo-abuse bad debt, tracking/deliverability friction.
  Includes a `metric_glossary` mapping each generic metric to its marketing analog.

## Structure
Each case has:
- `query` — the user message to feed a fresh Claude session with the skill loaded.
- `leadership_context` / `experiment` — the inputs implied by the query (for reference).
- `expected` — fixed answers where they exist (phase mapping, anchor weights, index, decision).
- `expected_behavior` — observable outcomes that define a pass; the case passes only if **every** item is met.
- `deterministic` — `true` cases have a single correct index/decision and serve as regression checks; `false` cases test reasoning quality.

## Coverage (general — scenarios.json)
- **C1** no context → must ask Step 1 questions first.
- **C2–C4** → map each maturity phase, return Σw=1.0 + pᵢ≥1.0 with justification.
- **C5** → reproduces doc Example 1: index +7.1, DEPLOY.
- **C6** → reproduces doc Example 2: index −7.0, REJECT, names the volume mirage.
- **C7** → SRM breach (p<0.001) → INVALID, index null (Layer 1 gate beats a +20% win).
- **C8** → +28% support-ticket spike → FREEZE despite a positive index (Layer 2 gate).
- **C9** → reporting-lag product → flag Backlog gap #3, treat DEPLOY as low-confidence.
- **C10** → custom blend → adjust + renormalize to Σw=1.0, attrition as dominant penalty.

## Coverage (marketing — scenarios-marketing.json)
- **M1** no context → ask Step 1 questions first.
- **M2** demand-gen land-grab → Market Capture, w1 dominant.
- **M3** lifecycle upsell, promo-refund fear → Monetization, p2 largest.
- **M4** list health / deliverability → Product Health, w3 + p3 elevated.
- **M5** landing-page creative → index +6.2, DEPLOY.
- **M6** 40%-off promo mirage → index −11.0, REJECT (upsell drained by promo bad debt).
- **M7** UTM/redirect bug → SRM p<0.001 → INVALID.
- **M8** higher send frequency → +22% spam complaints → FREEZE despite +5.0 index.
- **M9** BNPL promo, 7-day window → flag reporting lag, low-confidence.
- **M10** broad-match bidding → CAC cap breached → FREEZE despite +7.0 index.

## Running
No automated runner. For each case: start a fresh session, ask `query`, then a
human (or judging Claude) checks the response against `expected_behavior`.

The deterministic index values were verified arithmetically:
`C5 = 0.6+9.0−2.5 = +7.1`, `C6 = 7.0−12.0−2.0 = −7.0`, `C8 = 0.5·12 = +6.0`;
`M5 = 8.0+1.2−3.0 = +6.2`, `M6 = 6.0−15.0−2.0 = −11.0`, `M8 = 0.5·10 = +5.0`,
`M10 = 0.5·14 = +7.0`.
