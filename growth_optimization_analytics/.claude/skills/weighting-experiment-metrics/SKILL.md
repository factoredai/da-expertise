---
name: weighting-experiment-metrics
description: Builds a weighted Success Index tailored to the user's business and leadership strategy, then evaluates A/B experiment results into a DEPLOY/REJECT decision. Use when defining metric weights, scoring an experiment, choosing how to balance growth drivers against penalty drags, or sanity-checking a "winning" experiment.
---

# Weighting Experiment Metrics

## Overview
Applies the **Factored Way method**: a weighted **Success Index** that translates
a slow-moving North Star into a fast, per-experiment score by balancing positive
growth **drivers** against negative penalty **drags**.

```
Index = Σ wᵢ·Δ(driverᵢ)  −  Σ pⱼ·Δ(dragⱼ)   →  ascends toward the North Star
```

This skill (1) builds a weighting matrix tailored to the user's actual business
and leadership strategy, and (2) evaluates experiment results into a
DEPLOY / REJECT / FREEZE decision.

`reference.md` is **pedagogical, not prescriptive.** It documents one fully
worked instance — a SaaS company using Total ARR, three specific drivers, three
specific drags, three maturity-phase presets, and specific guardrail thresholds.
Treat all of that as a teaching example that shows *how the method works*, not as
the answer to copy. Adapt every concrete choice (North Star, which metrics, how
many, the weights, the thresholds) to the context the user gives you. When their
business differs from the example, follow the user.

### What is fixed vs. adaptable
- **Method invariants (keep):** positive weights normalize so `Σ wᵢ = 1.0`;
  penalties are **asymmetric** — a drag costs more than an equal-sized gain, so
  the worst drag's penalty clearly dominates; guardrails sit *outside* the index
  as hard gates; show the substituted arithmetic.
- **Everything else is adaptable:** the North Star, the set and number of drivers
  and drags, the metric definitions, the actual weight values, and the guardrail
  thresholds. The example's `pⱼ ≥ 1.0`, `p < 0.001` SRM, and `>15%` support spike
  are *defaults to reason from*, not laws.

## When to use
- Defining or justifying weights for an experimentation scorecard.
- Tailoring the index (metrics, North Star) to a specific business or industry.
- Scoring an experiment's deltas into a go/no-go decision.
- Sanity-checking whether a "win" is a volume mirage hiding revenue/technical decay.

## Step 1 — Understand the user's context, then model it
Skim `reference.md` for the method and an example of each piece. Then build the
model around the user's reality. Ask the user **only for what is missing**; for
anything they cannot answer, fall back to the example's analog and **state the
assumption**.

1. **North Star.** What lagging, hard-to-game outcome is the experiment program
   ultimately serving? (The example uses Total ARR; a media app might use
   retained DAU, a marketplace GMV, a nonprofit recurring donors.) Use the user's.
2. **Drivers (positives).** Which short-term, causal behaviors push toward that
   North Star? Use the user's real funnel metrics — not necessarily three, not
   necessarily the example's Acquisition/Expansion/Activation. Define each.
3. **Drags (penalties).** Which negatives must not be masked by driver volume —
   churn, bad debt, technical failures, or domain-specific harms? Define each.
4. **Strategic priority / weighting intention.** What does leadership want *now*
   (e.g. grab share, monetize the base, harden retention)? This sets which
   drivers get the most weight and which drag is penalized hardest. The few-shot
   examples in `reference.md` §5 show this *reasoning* (decision → judgment →
   weights) — study how the weights fall out of the argument, do not classify the
   user into one of them.
5. **Drag risk ordering.** How damaging is each drag right now? Sets the relative
   size of the penalties.
6. **Guardrails.** Which hard gates apply, at what thresholds (data-integrity
   like SRM; operational like support-load, cost caps, brand harm)? Adapt
   thresholds to the user; fall back to the example defaults only if unspecified.
7. **Reporting lag & sample maturity.** Do any drags surface late (e.g. 30–45 day
   bad-debt/churn)? Is the sample small/early? If so, flag the relevant backlog
   gap and treat the score as lower-confidence (see `reference.md` §9).

## Step 2 — Derive & justify the weights
1. **Reason from priority to weights.** Translate leadership's intention into a
   weight ordering, the way the §5 few-shot examples reason from a decision to a
   set of weights. **Derive** values that fit *this* business and argue why each
   one follows from the stated strategy — do not classify into an example or copy
   its numbers. Two different businesses with the same mandate may land on
   different weights; that is expected.
2. **Enforce the method invariants:** normalize positives so `Σ wᵢ = 1.0`; keep
   penalties asymmetric with the most-damaging drag dominating; penalties do NOT
   sum to 1.
3. **Output** the matrix as a table — one row per driver/drag *the user actually
   has* — with a one-line justification each:

   | Weight | Metric | Value | Justification |
   |---|---|---|---|
   | w₁ | (driver 1) | … | … |
   | … | … | … | … |
   | p₁ | (drag 1) | … | … |
   | … | … | … | … |

   Confirm `Σ wᵢ = 1.0` and that penalties are asymmetric (worst drag dominant)
   explicitly below the table.

## Step 3 — Evaluate an experiment
Only when the user supplies experiment deltas (variant vs. control, in %).

1. **Guardrails FIRST** (outside the index):
   - **Data-integrity breach** (e.g. SRM below the agreed p-threshold, broken
     tracking) → the index is **null and void**; verdict = **INVALID**, discard
     the sample. Stop here.
   - **Operational breach** (an agreed ceiling exceeded — support load, cost cap,
     brand/compliance harm) → verdict = **FREEZE for manual review**, even if the
     index is positive.
2. **Compute the index** with the agreed weights. Show the substituted arithmetic
   in full (mirror the worked Examples in `reference.md`):
   ```
   Index = (w₁·Δd₁) + … − (p₁·Δg₁) − … = <result>
   ```
3. **Decide:**
   - Index `> 0` and guardrails clear → **DEPLOY**.
   - Index `≤ 0` → **REJECT**.
   - Guardrail breach → **INVALID** (data integrity) or **FREEZE** (operational).
4. **Call out volume mirages:** if a headline driver looks great but a penalty
   drag pulls the index negative, name it explicitly.

## Output format
- The tailored weighting table (Step 2) + the `Σ wᵢ = 1.0` / asymmetry confirmation.
- If evaluating: guardrail check → substituted arithmetic → decision line in
  **bold** (DEPLOY / REJECT / FREEZE / INVALID).
- An **Assumptions & caveats** list: every assumed input (especially where you
  fell back to the example because the user didn't specify), plus any flagged
  backlog gap (noise, volatility, reporting lag).

## References
- `reference.md` — a fully worked **example instance** of the method (SaaS / Total
  ARR): symbol definitions, sample drivers & drags, §5 few-shot examples that
  reason from a decision to weights, worked Examples 1 & 2, guardrail hierarchy,
  and known backlog gaps. Read it to learn the mechanics and borrow defaults —
  adapt, do not copy verbatim.
