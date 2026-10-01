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

This skill (1) builds the weighting matrix (Step 2) and (2) evaluates an experiment
into a DEPLOY / REJECT decision (Step 3).

The framework is **one pipeline with two stages**: the **Index** measures the net
weighted effect (a scalar); the **Deployment Gate** turns that estimate into a
verdict.

### What is fixed vs. adaptable
- **Fixed (the framework):** the North Star (Total ARR); the three drivers and
  three drags and their definitions (`reference.md` §3–§4); the index formula; the
  two-stage Index→Gate split; the significance gate (`p < 0.05`); the
  asymmetric-penalty floor `pⱼ ≥ 1.0`; positives normalize so `Σ wᵢ = 1.0`.
- **Adaptable — weights only:** the actual weight **values** (`wᵢ`, `pⱼ`), derived
  from the user's leadership strategy (Step 2). Nothing else in the taxonomy moves.
- **Guardrails are out-of-band:** data-integrity (SRM) and operational
  (support-load, CAC caps, brand harm) checks are out-of-band experiment hygiene
  owned upstream — **not** part of the index or the gate. Surface a breach as a
  caveat if the user raises one, but never turn it into the skill's verdict. See
  `reference.md`'s out-of-band guardrails section.

## When to use
- Defining or justifying weights for an experimentation scorecard.
- Mapping the fixed drivers/drags onto a specific business or industry (proxies).
- Scoring an experiment's deltas into a go/no-go decision.
- Sanity-checking whether a "win" is a volume mirage hiding revenue/technical decay.

## Step 1 — Map the user's business onto the fixed framework
Read `reference.md` for the taxonomy and the per-metric proxies. Your job: (a) map
the user's instrumentation onto each fixed metric and (b) gather what's needed to set
the weights. Ask **only for what is missing**; state any assumption you fall back on.

1. **North Star — Total ARR.** Confirm how it manifests for the user
   (contract ARR, subscription MRR×12, etc.).
2. **Drivers: Acquisition (w₁), Expansion (w₂), Milestone Activation (w₃).**
   Map each to the user's actual metric (e.g. e-commerce Acquisition = Revenue per
   Session; see `reference.md`'s e-commerce mapping).
3. **Drags: Attrition & Closures (p₁), Bad Balances & Involuntary Churn
   (p₂), Technical Friction (p₃).** Map each to the user's instrumentation (§4).
4. **Strategic priority / weighting intention.** What does leadership want *now*
   (e.g. grab share, monetize the base, harden retention)? This sets which
   drivers get the most weight and which drag is penalized hardest (see the §5
   few-shot examples).
5. **Drag risk ordering.** How damaging is each drag right now? Sets the relative
   size of the penalties.
6. **Evaluation data & significance.** Is per-user (unit-level) data available so
   the index can be tested with a two-sample t-test (`p < 0.05`), or only
   aggregate % deltas? Aggregate-only means you can judge *direction* but not
   *significance* — say so (see `reference.md` §2.1, §7).
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
3. **Output** the matrix as a table — the fixed six rows — with a one-line
   justification each:

   | Weight | Metric | Value | Justification |
   |---|---|---|---|
   | w₁ | Acquisition | … | … |
   | w₂ | Expansion | … | … |
   | w₃ | Milestone Activation | … | … |
   | p₁ | Attrition & Closures | … | … |
   | p₂ | Bad Balances & Involuntary Churn | … | … |
   | p₃ | Technical Friction | … | … |

   Confirm `Σ wᵢ = 1.0` and that penalties are asymmetric (worst drag dominant)
   explicitly below the table.

## Step 3 — Evaluate an experiment
Only when the user supplies experiment deltas (variant vs. control).

1. **Compute the index** with the agreed weights. Show the substituted arithmetic
   in full (mirror the worked Examples in `reference.md`):
   ```
   Index = (w₁·Δd₁) + … − (p₁·Δg₁) − … = <result>
   ```
   If per-user data is available, the rigorous form is the mean of per-user
   `Scoreᵢ` compared across arms with a two-sample t-test (`reference.md` §2.1),
   which yields both the value and a p-value.

   For **exact** numbers — index, Welch t-test p-value, weight checks, gate verdict
   — use `success_index.py` rather than computing by hand: pipe a JSON config to
   `python success_index.py`, or import `compute_index` / `welch_ttest` / `gate`.
2. **Gate on value + significance:**
   - Index `> 0` **and** significant (`p < 0.05`) → **DEPLOY**.
   - Index `≤ 0` → **REJECT**.
   - Index `> 0` but **not** significant (`p ≥ 0.05`) → **do not ship**:
     directionally positive, evidence insufficient — extend the test. Not a true
     negative.
   - **Aggregate deltas only** (no per-user data) → judge *direction* only: report
     the directional DEPLOY/REJECT and flag that a two-sample t-test must confirm
     significance before rollout.
3. **Call out volume mirages:** if a headline driver looks great but a penalty
   drag pulls the index negative, name it explicitly. (This lives *in the index*
   via the asymmetric penalties.)
4. **Guardrails are not a gate here.** If the user raises a data-integrity (SRM) or
   operational condition, record it as a non-gating out-of-band caveat — it does
   **not** change the verdict (`reference.md` out-of-band guardrails section).

## Output format
- The tailored weighting table (Step 2) + the `Σ wᵢ = 1.0` / asymmetry confirmation.
- If evaluating: substituted arithmetic → value + significance → decision line in
  **bold** (DEPLOY / REJECT; or "not significant — extend" when positive but
  `p ≥ 0.05`).
- An **Assumptions & caveats** list: every assumed input (especially any value you
  assumed because the user didn't specify), whether significance
  was tested or only direction judged, any out-of-band guardrail condition you
  surfaced (non-gating), plus any flagged backlog gap (noise, volatility,
  reporting lag).

## References
- `reference.md` — the framework spec (SaaS / Total ARR): symbol definitions, the
  index as a measurement (aggregate vs unit-level + t-test, §2.1), the fixed
  drivers & drags (§3–§4), §5 few-shot examples that reason from a decision to
  weights, the deployment gate (§7), worked Examples 1 & 2, known backlog gaps, and
  the out-of-band guardrails section.
- `success_index.py` — dependency-less (stdlib) exact calculator mirroring
  `reference.md` §2/§2.1/§7: `compute_index`, `user_scores`, `welch_ttest`
  (two-sided p), `validate_weights`, `gate`. Run as a CLI
  (`python success_index.py [config.json]`, or config on stdin) or import the
  functions; `--self-check` verifies it against Examples 1 & 2. Use it for any
  real arithmetic instead of computing by hand.
