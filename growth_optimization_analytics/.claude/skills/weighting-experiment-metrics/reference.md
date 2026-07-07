# Factored Way — Worked Example (Pedagogical)

> **This is a teaching example, not the answer to copy.** It documents one fully
> worked instance of the method — a SaaS company using Total ARR as its North
> Star, three specific drivers, three specific drags, three maturity-phase
> presets, and specific guardrail thresholds. Use it to learn *how the method
> works* and to borrow sensible defaults. The **method invariants** are fixed
> (positives normalize to `Σ wᵢ = 1.0`; penalties are asymmetric with the worst
> drag dominant; guardrails gate the index from outside). **Everything concrete
> below is adaptable** — the North Star, which/how many metrics, the weight
> values, and the thresholds (`pⱼ ≥ 1.0`, SRM `p < 0.001`, `>15%`) should be
> tailored to the user's business per `SKILL.md` Step 1. Do not snap a user's
> answer onto these numbers; follow the user's context.

Condensed from *General Metrics for Experimentation: Strategic Scorecard Taxonomy
& Governance*. The numbers below are this example's values — reason from them,
adapt them; do not treat them as immutable for every business.

## Table of contents
- [1. North Star](#1-north-star)
- [2. The Success Index](#2-the-success-index)
- [3. Driver metrics (accelerators)](#3-driver-metrics-accelerators)
- [4. Negative metrics (decelerators)](#4-negative-metrics-decelerators)
- [5. Few-shot examples: reasoning from a decision to weights](#5-few-shot-examples-reasoning-from-a-decision-to-weights)
- [6. Asymmetric penalty principle](#6-asymmetric-penalty-principle)
- [7. Worked examples](#7-worked-examples)
- [8. Guardrail hierarchy](#8-guardrail-hierarchy)
- [9. Known backlog gaps](#9-known-backlog-gaps)

## 1. North Star
**Primary North Star = Total ARR (Annual Recurring Revenue).** A lagging,
economic indicator of realized, contractually locked enterprise utility.

CLTV is **rejected** on purpose: it is a "mathematical prophecy" reliant on
volatile downstream assumptions (future churn, discount margins, expansion
timelines); modeling inaccuracy introduces systematic bias and corrupts
experiment validity. Total ARR is undeniable, contractually locked, realized
revenue.

ARR moves slowly across multi-month cohorts, so it cannot drive daily experiment
decisions. The Success Index bridges that gap: it rolls the short-term behavioral
inputs that causally drive ARR into one standardized score.

## 2. The Success Index
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
- **pᵢ (penalty weights):** individual weights on negative drags; prevent
  short-term volume from masking structural business decay. They do **not** sum
  to 1.

## 3. Driver metrics (accelerators)
Top- and mid-funnel behavior feeding the long-term ARR engine.

- **Driver 1 — Acquisition (w₁):** velocity of new accounts, contract executions,
  premium-tier upgrades. Examples: B2B contract signatures, SaaS site licenses,
  retail subscription completions, digital-wallet creations. *E-commerce proxy:*
  **Revenue per Session** = ConversionRate (Transactions/Sessions) × AOV
  (Revenue/Transactions) — a blended proxy that counters tests inflating
  conversion volume while crashing order value.
- **Driver 2 — Expansion (w₂):** rate at which active accounts cross critical
  utilization thresholds signaling readiness to upgrade/upsell. Examples: reaching
  80% of allocated seats, 80% storage capacity, or 80% of monthly credits.
- **Driver 3 — Onboarding Milestone Activation (w₃):** Time-to-First-Value (TTFV)
  completion rate — speed/consistency with which a new cohort hits core utility.
  Examples: first live API call, first FinTech account funding, recurring-delivery
  setup. *E-commerce proxy:* Funnel Step Cohorts (Product View → Add to Cart →
  Checkout), tracked on isolated launch cohorts to bypass distortion from
  recurring buyers.

## 4. Negative metrics (decelerators)
Operational penalties; strict boundaries that stop teams gaming index volume.

- **Negative 1 — Attrition Rate & Account Closures (p₁):** leading indicators of
  terminations, cancellation-pipeline entries, non-renewals within the test window.
- **Negative 2 — Bad Unpaid Balances & Involuntary Churn (p₂):** accrued bad debt,
  uncollected receivables, payment-retry failures, bad-collections exposure.
  *E-commerce proxy:* post-checkout cancellation rates on deferred invoices —
  immediate checkout "success" that cancels once the payment window expires.
- **Negative 3 — Technical Friction & Processing Failures (p₃):** system bugs and
  processing failures: involuntary checkout drops, gateway timeouts, invoicing
  sync exceptions, p99 latency spikes, 5xx API errors, telemetry packet drops.

## 5. Few-shot examples: reasoning from a decision to weights
These are **examples of the reasoning**, not phases to classify into or rows to
copy. Each shows a leadership decision, the judgment that follows from it, and a
*resulting* set of weights. Your job for a real user is to run the same kind of
reasoning over *their* decision and *their* metrics — the weights you land on
should fall out of the argument, and there is no requirement that they match any
example here. Note how, in every case, the positives still sum to 1.0 and the
scariest drag gets the dominant penalty.

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

The point of the three is contrast: the *same* metrics, weighted differently
because the *decision* differed. A real user may have other metrics, more or
fewer of them, a different North Star, or a blended mandate — reason from their
words, don't pattern-match to A/B/C.

## 6. Asymmetric penalty principle
Whatever the strategy, penalties for critical drags stay prioritized — a drag
costs more than an equal-sized gain, and the scariest drag's penalty dominates.
In this example that floor lands at **pⱼ ≥ 1.0**; the exact floor is a tunable
default, but the asymmetry itself is the invariant. Introducing customer
attrition, billing failures, or technical degradation is structurally far more
damaging to long-term health than capturing an equal % of new volume.

*E-commerce caution:* altering shipping-fee thresholds can shift product mix
(more heavy, low-margin furniture vs. high-margin shoes). A test can show a
top-line win but be unprofitable; if the cost-drag penalty (pᵢ) is set too low,
the framework wrongly approves it.

## 7. Worked examples

### Example 1 — DEPLOY (retention-weighted scorecard, onboarding wizard)
Weights: w₁=0.2, w₂=0.2, w₃=0.6; p₁=2.0, p₂=1.0, p₃=2.5.
Deltas: Milestone (w₃) +15%, Acquisition (w₁) +3%, Technical Friction (p₃) +1%,
rest 0%.
```
Index = (0.2·3) + (0.2·0) + (0.6·15) − (2.0·0) − (1.0·0) − (2.5·1)
      = 0.6 + 0 + 9.0 − 2.5 = +7.1
```
**DEPLOY** — the 15% onboarding leap overwhelms the small friction penalty.

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

## 8. Guardrail hierarchy
Guardrails are **omitted from the index**; they are absolute external boundaries
forming the pipeline's foundational filter. Check them **before** trusting any
index score.

- **Layer 1 — Data Integrity.** Protects internal validity. Core metrics: Sample
  Ratio Mismatch (SRM) via real-time Chi-squared contingency tests; Data
  Completeness Rates on logging pipelines. **Rule:** if the SRM canary fires a
  critical alert (`p < 0.001`), traffic assignment is corrupted → the Success
  Index is **null and void**, the variant is paused, and the sample is discarded.
- **Layer 2 — Operational.** Protects the org from customer-facing friction,
  support load, and uncapped cost. Core metrics: Customer Support Ticket Creation
  Volatility, Manual Fraud/Risk Review Queue Capacity, CAC Efficiency Caps.
  **Rule:** if the index is positive but an operational guardrail breaches its
  ceiling (e.g. `>15%` baseline spike in support tickets), the rollout is frozen
  and flagged for manual executive review.
  *E-commerce note:* segment secondary metrics like NPS by operational data (e.g.
  pickup radius) — expanding a pickup radius 2→5 miles can lift funnel drivers yet
  damage satisfaction via travel friction.

## 9. Known backlog gaps
Open weaknesses in the raw index — flag the relevant one when it applies and treat
the score as lower-confidence:

1. **Sample noise & early distortion.** Raw % deltas swing randomly at small N /
   early in a test. *Fix:* statistical shrinkage (Bayesian smoothing) toward zero
   when N is low / variance is high, or weight each delta by its confidence.
2. **Volatility imbalance.** Static weights on raw % ignore that metrics have
   different baseline volatility (stable onboarding vs. noisy expansion), so noisy
   metrics drown steady valuable ones. *Fix:* Z-score normalization — weight by
   standard deviations from historical baseline.
3. **Data maturity / reporting lag.** Attrition and bad-debt signals can land
   30–45 days late (e.g. unpaid-invoice expirations need 72+ hours to log), so a
   short window may clear a feature before its true negative impact appears.
   *Fix:* a lag-correction coefficient scaling up delayed-metric penalties in short
   windows, or a mandatory data-maturation freeze before finalizing rollout.
