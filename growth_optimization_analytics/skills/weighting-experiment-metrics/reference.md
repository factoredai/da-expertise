# Metric Analysis Framework

> **The taxonomy is fixed.** The North Star is **Total ARR**; the drivers are
> **Acquisition, Expansion, Milestone Activation**; the drags are **Attrition &
> Closures, Bad Balances & Involuntary Churn, Technical Friction**; the index
> formula, the Index→Gate split, the significance gate, and the thresholds
> (`pⱼ ≥ 1.0`, `p < 0.05`) are all fixed. Positives normalize to `Σ wᵢ = 1.0` and
> penalties stay asymmetric with the worst drag dominant. The **only**
> per-engagement choice is the **weight values** (`wᵢ`, `pⱼ`), derived from the
> user's leadership strategy (§5, `SKILL.md` Step 2). Map a business onto the fixed
> metrics using §3–§4 and the e-commerce mapping below.

The framework is one pipeline: the **Index** (§2) measures the net weighted
effect; the **Deployment Gate** (§7) turns it into a DEPLOY/REJECT verdict.
Guardrails sit outside both (final section).

## Table of contents
- [1. North Star](#1-north-star)
- [2. The Success Index — the measurement](#2-the-success-index--the-measurement)
- [3. Driver metrics (accelerators)](#3-driver-metrics-accelerators)
- [4. Negative metrics (decelerators)](#4-negative-metrics-decelerators)
- [Worked mapping: e-commerce](#worked-mapping-e-commerce)
- [5. Few-shot examples: reasoning from a decision to weights](#5-few-shot-examples-reasoning-from-a-decision-to-weights)
- [6. Asymmetric penalty principle](#6-asymmetric-penalty-principle)
- [7. The deployment gate](#7-the-deployment-gate)
- [8. Worked examples](#8-worked-examples)
- [9. Known backlog gaps](#9-known-backlog-gaps)
- [Out-of-band guardrails (informational)](#out-of-band-guardrails-informational)

## 1. North Star
**Primary North Star = Total ARR (Annual Recurring Revenue).** A lagging,
economic indicator of realized, contractually locked enterprise utility.

The North Star must be a realized, contractually locked outcome, not a
forward-looking modeled one. Values like CLTV rely on volatile downstream
assumptions (future churn, discount margins, expansion timelines); the modeling
inaccuracy introduces systematic bias and corrupts experiment validity. Total ARR
is undeniable, contractually locked, realized revenue.

ARR moves slowly across multi-month cohorts, so it cannot drive daily experiment
decisions. The Success Index bridges that gap: it rolls the short-term behavioral
inputs that causally drive ARR into one standardized score.

## 2. The Success Index — the measurement
The index is a **measurement**: a weighted scalar capturing *how big* and *in
which direction* the net effect is, after penalizing the scary drags. Turning it
into a ship / don't-ship call is the gate (§7).
```
Index = w₁·Δ Acquisition + w₂·Δ Expansion + w₃·Δ Milestone Activation
        − p₁·Δ Attrition & Closures
        − p₂·Δ Bad Balances & Churn
        − p₃·Δ Technical Friction
```
Symbol definitions:
- **Δ (Delta):** the % lift or drop of the active variant relative to the
  baseline control group.
- **wᵢ (strategic weights):** positive fractional weights on growth drivers.
  Structural constraint: **w₁ + w₂ + w₃ = 1.0**.
- **pⱼ (penalty weights):** individual weights on negative drags; prevent
  short-term volume from masking structural business decay. They do **not** sum
  to 1.

### 2.1 Estimating the index: aggregate Δ% vs unit-level
The *same* formula can be evaluated at two fidelities:

- **Aggregate Δ% (point estimate).** Plug each metric's group-level % lift into
  the formula. One number, **no error bar**. Fast, good for a quick read — but it
  cannot tell a real lift from noise (Backlog gap #1).
- **Unit-level aggregation (proper estimate).** Compute the index per user, then
  compare groups statistically:
  1. **User-level indexing.** For every user *i*:
     `Scoreᵢ = w₁·Acqᵢ + w₂·Expᵢ + w₃·Onbᵢ − p₁·Attrᵢ − p₂·Badᵢ − p₃·Fricᵢ`
  2. **Two-sample test.** Aggregate `Scoreᵢ` across Control and Treatment; run a
     two-sample t-test on the mean scores.

  This yields both a **value** (mean lift) *and* a **p-value** — the index and its
  confidence together. This is what the deployment gate (§7) consumes.

## 3. Driver metrics (accelerators)
Top- and mid-funnel behavior feeding the long-term ARR engine.

- **Driver 1 — Acquisition (w₁):** velocity of new accounts, contract executions,
  premium-tier upgrades. Examples: B2B contract signatures, SaaS site licenses,
  retail subscription completions, digital-wallet creations.
- **Driver 2 — Expansion (w₂):** rate at which active accounts cross critical
  utilization thresholds signaling readiness to upgrade/upsell. Examples: reaching
  80% of allocated seats, 80% storage capacity, or 80% of monthly credits.
- **Driver 3 — Onboarding Milestone Activation (w₃):** Time-to-First-Value (TTFV)
  completion rate — speed/consistency with which a new cohort hits core utility.
  Examples: first live API call, first FinTech account funding, recurring-delivery
  setup.

## 4. Negative metrics (decelerators)
Operational penalties; strict boundaries that stop teams gaming index volume.

- **Negative 1 — Attrition Rate & Account Closures (p₁):** leading indicators of
  terminations, cancellation-pipeline entries, non-renewals within the test window.
- **Negative 2 — Bad Unpaid Balances & Involuntary Churn (p₂):** accrued bad debt,
  uncollected receivables, payment-retry failures, bad-collections exposure.
- **Negative 3 — Technical Friction & Processing Failures (p₃):** system bugs and
  processing failures: involuntary checkout drops, gateway timeouts, invoicing
  sync exceptions, p99 latency spikes, 5xx API errors, telemetry packet drops.

## Worked mapping: e-commerce
A business instantiates each fixed metric with its own instrumentation. Worked
example for an e-commerce business:

| Metric | E-commerce instrumentation |
|---|---|
| Acquisition (w₁) | **Revenue per Session** = ConversionRate (Transactions/Sessions) × AOV (Revenue/Transactions) — a blended proxy that counters tests inflating conversion volume while crashing order value |
| Expansion (w₂) | maps directly (utilization / repeat-purchase thresholds) |
| Milestone Activation (w₃) | **Funnel Step Cohorts** (Product View → Add to Cart → Checkout), tracked on isolated launch cohorts to bypass distortion from recurring buyers; score a deep stage like Checkout as the quality signal |
| Attrition & Closures (p₁) | maps directly (subscription cancellations, opt-outs) |
| Bad Balances & Involuntary Churn (p₂) | **post-checkout cancellation rates on deferred invoices** — immediate checkout "success" that cancels once the payment window expires |
| Technical Friction (p₃) | maps directly (checkout drops, gateway timeouts, 5xx) |

Two cautions this mapping surfaces:
- **Shipping-fee thresholds shift product mix** (e.g. more heavy, low-margin
  furniture vs. high-margin shoes). A test can show a top-line win but be
  unprofitable; if the cost-drag penalty (pⱼ) is set too low, the framework
  wrongly approves it.
- **Segment NPS by operational data.** Expanding a store pickup radius 2→5 miles
  can lift funnel drivers yet damage satisfaction via travel friction — so a
  secondary metric like NPS must be segmented (e.g. by pickup radius) to catch it.

## 5. Few-shot examples: reasoning from a decision to weights
Three leadership decisions and the weights that follow from each.

**Example A — "We're a young company; this year is pure land-grab."**
Leadership is willing to trade some churn and margin for raw new-logo velocity.
So acquisition should carry most of the positive weight, with expansion and
onboarding sharing the rest. Because reckless growth that bleeds customers is the
real failure mode, attrition is the most-feared drag and gets the heaviest
penalty; billing and technical issues are tolerable for now but still penalized.
*One defensible result:* w(acq)=0.5, w(exp)=0.2, w(onb)=0.3; p(attrition)=3.0,
p(bad-debt)=1.5, p(technical)=1.0.

**Example B — "Mature base; the mandate is to monetize and expand — and finance
got burned by bad debt last year."** Expansion/upsell behavior earns the largest
positive weight. The decisive constraint is that aggressive monetization not be
funded by uncollectable revenue, so bad-debt/involuntary-churn becomes the
dominant penalty — larger even than attrition. *One defensible result:*
w(acq)=0.2, w(exp)=0.5, w(onb)=0.3; p(attrition)=2.0, p(bad-debt)=3.0,
p(technical)=1.0.

**Example C — "We have a churn and reliability problem; this year is retention
and stability."** Getting new users to durable first value (onboarding/activation)
carries the most positive weight. The two things that destroy retention —
customers leaving and the product breaking — get the heaviest penalties, with
technical friction elevated well above its land-grab level. *One defensible
result:* w(acq)=0.2, w(exp)=0.2, w(onb)=0.6; p(attrition)=2.0, p(bad-debt)=1.0,
p(technical)=2.5.

## 6. Asymmetric penalty principle
Whatever the strategy, penalties for critical drags stay prioritized — a drag
costs more than an equal-sized gain, and the scariest drag's penalty dominates.
That floor is **pⱼ ≥ 1.0**, and the asymmetry itself is the invariant. Introducing
customer attrition, billing failures, or technical degradation is structurally far
more damaging to long-term health than capturing an equal % of new volume.

## 7. The deployment gate
The gate is the **decision** layer. It reads the index estimate from §2 — the
`(value, p-value)` pair — and emits the verdict.

- Index value **> 0 and statistically significant (`p < 0.05`)** → **DEPLOY**.
- Index value **≤ 0** → **REJECT**.
- Index value **> 0 but not significant (`p ≥ 0.05`)** → **do not ship**:
  directionally positive, evidence insufficient — extend the test / gather more
  units. This is *not* a true negative.

When only **aggregate Δ%** is available (no per-user data), the gate can judge
**direction only** (the sign of the value); significance is unverified. Report the
directional DEPLOY/REJECT and flag that a two-sample t-test must confirm it before
rollout.

**Volume-mirage check.** A headline driver can look spectacular while a penalty
drag pulls the index negative. That exposure lives inside the index via the
asymmetric penalties (§6), so call it out explicitly when it happens (see
Example 2).

## 8. Worked examples
Both examples use the **aggregate Δ%** form (§2.1): they demonstrate the index
computation, the mirage check, and a **directional** gate verdict. Significance is
assumed (no per-user data is given); with unit-level data you would additionally
confirm `p < 0.05` before a DEPLOY.

### Example 1 — DEPLOY (retention-weighted scorecard, onboarding wizard)
Weights: w₁=0.2, w₂=0.2, w₃=0.6; p₁=2.0, p₂=1.0, p₃=2.5.
Deltas: Milestone (w₃) +15%, Acquisition (w₁) +3%, Technical Friction (p₃) +1%,
rest 0%.
```
Index = (0.2·3) + (0.2·0) + (0.6·15) − (2.0·0) − (1.0·0) − (2.5·1)
      = 0.6 + 0 + 9.0 − 2.5 = +7.1
```
**DEPLOY** — the 15% onboarding leap overwhelms the small friction
penalty.

### Example 2 — REJECT (monetization-weighted scorecard, credit-allocation prompt)
Weights: w₁=0.2, w₂=0.5, w₃=0.3; p₁=2.0, p₂=3.0, p₃=1.0.
Deltas: Expansion (w₂) +14%, Bad Balances (p₂) +4%, Technical Friction (p₃) +2%,
rest 0%.
```
Index = (0.2·0) + (0.5·14) + (0.3·0) − (2.0·0) − (3.0·4) − (1.0·2)
      = 0 + 7.0 + 0 − 12.0 − 2.0 = −7.0
```
**REJECT** — a +14% expansion looks spectacular, but heavy bad-debt penalty
(p₂=3.0) drains it. The index exposes the volume mirage and blocks deployment.

## 9. Known backlog gaps
Open weaknesses in the raw index — flag the relevant one when it applies and treat
the score as lower-confidence:

1. **Sample noise & early distortion.** Raw % deltas swing randomly at small N /
   early in a test. The **unit-level t-test (§2.1)** is the first-line fix: it
   only clears a lift that is statistically significant. Further refinement:
   statistical shrinkage (Bayesian smoothing) toward zero when N is low / variance
   is high, or weighting each delta by its confidence.
2. **Volatility imbalance.** Static weights on raw % ignore that metrics have
   different baseline volatility (stable onboarding vs. noisy expansion), so noisy
   metrics drown steady valuable ones. *Fix:* Z-score normalization — weight by
   standard deviations from historical baseline.
3. **Data maturity / reporting lag.** Attrition and bad-debt signals can land
   30–45 days late (e.g. unpaid-invoice expirations need 72+ hours to log), so a
   short window may clear a feature before its true negative impact appears.
   *Fix:* a lag-correction coefficient scaling up delayed-metric penalties in short
   windows, or a mandatory data-maturation freeze before finalizing rollout.

## Out-of-band guardrails (informational)
> Guardrails are **not** part of the Success Index and do **not** drive the
> deployment gate (§7). They are experiment hygiene owned upstream: data-integrity
> (SRM, logging completeness) is an assignment-validity precondition the skill
> assumes holds; operational limits (support load, CAC caps, brand/NPS) are
> separate monitors. If the user raises one, surface it as a caveat to resolve
> upstream — it is not a verdict here.

- **Layer 1 — Data Integrity.** SRM (real-time Chi-squared contingency tests) and
  logging-completeness rates protect internal validity. SRM is an upstream
  data-validity check: if the user reports a breach (e.g. `p < 0.001`), warn that
  the deltas may be untrustworthy and should be fixed at the source.
- **Layer 2 — Operational.** Support-ticket volatility, manual fraud/risk queue
  capacity, CAC efficiency caps. An operational ceiling breach (e.g. a `>15%`
  support-ticket spike) is a separate concern for the owning team.
