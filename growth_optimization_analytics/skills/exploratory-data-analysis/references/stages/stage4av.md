## Stage 4a-V — Validation Gate

**Goal:** Verify every Stage 4a finding through two complementary lenses — (1) mechanical constraint validation against the register and (2) multi-dimensional segment exploration to discover interaction effects invisible in single-dimension cuts.

**This stage cannot be skipped or folded back into 4a.** It runs as a separate prompt after the 4a checkpoint is confirmed. Phase 1 is mechanical verification. Phase 2 is analytical exploration. Both phases must complete before 4b can begin.

**Why three phases:** Phase 1a catches register incompleteness — constraints that should have been in the register but weren't anticipated at Stage 2, plus bias direction predictions that turned out to be wrong or underspecified. Phase 1b catches errors of omission — constraints that were in the register but not correctly applied to findings. Phase 2 catches errors of single-dimensional thinking — findings that appear Uniform in every single-dimension cut but reveal interactions, reversals, or amplifications when dimensions are crossed. These are different failure modes requiring different procedures. Phase 1a runs once on the register itself (small-N). Phase 1b scales with register × findings. Phase 2 scales with findings × dimension pairs (always substantial, never skippable).

---

### Input

- The complete set of Stage 4a findings (F1–Fn) with their segment status blocks and register acknowledgment sub-blocks
- The constraint register (`$PROJECT_ROOT/data/constraint_register.csv`)
- The Consultant's First-Day Gate (top 3 findings)

---

## Phase 1a — Register Completeness Review

**Mode:** Analytical. Before validating findings against the register, verify the register itself is complete. The register was built at Stage 2 before any findings existed — it may be missing constraints that only became visible during 4a execution.

**Why this runs first:** Phase 1b (the finding-by-finding validation) assumes the register is authoritative. If the register is incomplete, Phase 1b will produce false "Confirmed" results for findings that should have been flagged — the same class of error as a test suite with missing test cases.

### Three Checks

#### Check 1a.1 — Missing Constraints

For each 4a finding, ask: "Did this finding require handling a data quality issue, population filter, or analytical limitation that is not in the register?"

**Procedure:**
1. For each finding F(i), review its narrative, segment status block, and any caveats noted during 4a execution.
2. Identify any constraint that was handled ad-hoc (e.g., "we excluded these rows because..." or "this metric is unreliable because...") without reference to a register constraint_id.
3. For each identified gap: create a new register row with a constraint_id following the existing numbering scheme, and retroactively check which other findings from 4a touch the same table/column — those findings may also be affected.

**What this catches:** Constraints discovered during analysis that were not anticipated at Stage 2. Common examples: a field that appeared reliable in profiling but broke down under aggregation; a population subgroup whose behavior was only recognized as anomalous when a finding produced an unexpected result; a temporal discontinuity (e.g., an operational event like account closures) that only became visible in the time-series analysis.

#### Check 1a.2 — Underspecified Bias Direction

For each existing register row, compare the stated `bias_direction` against what 4a actually observed when the constraint was encountered.

**Procedure:**
1. For each register row R(j), find all 4a findings where R(j) was acknowledged.
2. Compare the register's predicted bias (e.g., "inflates basket aggregations") against the actual observed effect (e.g., "complete reversal of finding direction").
3. **If the observed effect was materially different from the prediction:** update the register's `bias_direction` field with the observed specifics. The original prediction may have been directionally correct but understated in magnitude, or it may have been wrong entirely.

**Decision rule:**
- Prediction correct in direction and approximate magnitude: no change.
- Prediction correct in direction but magnitude was >3× larger or the effect was qualitatively different (e.g., predicted "moderate inflation" but actual was "complete finding reversal"): update `bias_direction` with observed specifics. Add a `[1a.2 revised]` tag.
- Prediction wrong in direction: update and flag as a register design error for Stage 6 review.

**What this catches:** Register entries written at Stage 2 with generic bias descriptions that don't capture the severity of the actual downstream impact. The register should be a living document that gains specificity as findings are produced.

#### Check 1a.3 — Constraint Interactions

Review whether any pair of constraints interacts in ways that neither individual register entry describes.

**Procedure:**
1. Identify all pairs of constraints that apply to the same table (e.g., FLAGGED_POPULATION on FactOnlineSales + REFERENTIAL_INTEGRITY on FactOnlineSales).
2. For each pair, ask: "Does the combination produce an effect that neither constraint alone describes?" Common interaction patterns:
   - **Compounding:** Orphaned keys + sentinel population may both affect the same finding in the same direction, producing a larger distortion than either alone.
   - **Masking:** One constraint may hide the effect of another — e.g., a sentinel population inflates a metric that orphaned keys would otherwise deflate, making the aggregate look normal when both components are distorted.
   - **Scope narrowing:** Two scope constraints together may reduce the usable population below a meaningful threshold — e.g., customer-level scope (22% of rows) intersected with matched-products-only (86% of rows) leaves only ~19% of rows for customer × product analysis.
3. For any identified interaction: add a new register row of type `CONSTRAINT_INTERACTION` that names the two parent constraints and describes the combined effect.

**What this catches:** Second-order effects invisible when constraints are checked individually. For example, when orphaned foreign keys and sentinel-value populations apply to the same table, their combined effect on a downstream join is more restrictive than either constraint alone — but no single register row captures the interaction.

### Phase 1a Output

1. **Updated register CSV** (if any rows were added, revised, or interaction rows created). The register is append-only — original rows are never deleted, only updated with `[1a.2 revised]` tags.
2. **Completeness log** documenting each check and its result:

```
| Check | Result | Action |
|-------|--------|--------|
| 1a.1 Missing constraints | [N added / None found] | [List of new constraint_ids if any] |
| 1a.2 Bias direction | [N revised / All accurate] | [List of revised constraint_ids if any] |
| 1a.3 Interactions | [N interactions found / None] | [List of new CONSTRAINT_INTERACTION rows if any] |
```

If no changes were made across all three checks: document "Register reviewed: no gaps, no revisions, no interactions. Completeness confirmed." This explicit confirmation ensures completeness was verified, not assumed.

---

## Phase 1b — Finding-by-Finding Constraint Validation

**Mode:** Mechanical. For each row in the (now-verified) constraint register × each finding, verify that 4a handled it correctly. This is the original Phase 1 procedure, renamed to Phase 1b to reflect its position after the completeness review.

### Procedure

1. Load the constraint register (including any rows added in Phase 1a).
2. For each finding F(i), for each register row R(j):
   a. Check whether 4a's register acknowledgment sub-block contains R(j).constraint_id.
   b. If missing: **Process error.** Run the check now and record the result.
   c. If present: verify the handling was correct by re-computing the finding's headline metric under the constraint condition.

3. Apply decision thresholds based on constraint type:

| Constraint Type | Validation Action | Threshold |
|----------------|-------------------|-----------|
| FLAGGED_POPULATION | Re-compute metric with and without flagged rows | <5% change = Confirmed; 5–20% = Revised; >20% = Revised (material) |
| DOMINANT_ENTITY | Re-compute metric excluding the dominant entity | Same thresholds as above |
| REFERENTIAL_INTEGRITY | Verify the finding noted asymmetric loss rates where applicable | Check bias direction matches expectation |
| DUAL_SPINE_OVERLAP | Verify that Redundant pairs were not used as independent cuts | If both members of a Redundant pair appear as separate segment dimensions in the finding, flag as double-counted |
| TEMPORAL_INTEGRITY | Verify that unreliable periods were excluded from temporal findings | Check that flagged periods are not in the computation window |
| FIELD_RELIABILITY | Verify that unreliable fields were not used as key metrics | Check that flagged columns are not the basis of any finding |
| ANALYSIS_SCOPE | Verify that findings respect population coverage limits | Check that customer-level findings note their coverage fraction |
| SCALE_CONSTRAINT | Verify that large-table findings used pre-computed data, not in-notebook processing | Check script provenance |

4. Record the result in the validation log.

### Phase 1b Output: Validation Log Table

One row per finding × register constraint. Every cell filled.

```
| Finding | Constraint ID | Type | 4a Acknowledgment | Validation Result | Evidence |
|---------|--------------|------|-------------------|-------------------|----------|
| F1 | POP-1 | FLAGGED_POPULATION | "Matched products only" | Confirmed (<5% change) | 35.6% vs 37.8% concentration |
| F3 | DOM-2 | DOMINANT_ENTITY | "All rows" | Confirmed (direction holds) | ex-NA: −27.3% decline (vs −18.0%) |
| F5 | POP-1 | FLAGGED_POPULATION | "All orders" | REVISED (material) | Sentinel reversal: 76% single-item |
| F7 | OVERLAP-1 | DUAL_SPINE_OVERLAP | "Store cluster not used" | Confirmed | Correct: cluster is Redundant with continent |
```

**Summary row at bottom:**
```
Total: [N] findings × [M] constraints = [N×M] checks. [P] confirmed, [Q] revised, [R] N/A, [S] process errors.
```

---

## Phase 2 — Multi-Dimensional Segment Exploration

**Mode:** Analytical. This phase is never skippable, even when Phase 1's register produces zero revisions. The value of multi-dimensional exploration is independent of data quality issues.

**Why multi-dimensional crosses matter:** Single-dimension cuts (4a's job) ask "does this finding vary by region?" and "does this finding vary by channel?" separately. But the most consequential patterns are often in the interaction: "does this finding vary differently by region depending on which channel we look at?" A finding reported as "Uniform" in 4a because every single-dimension cut showed the same direction can mask a Simpson's Paradox in which one segment moves one way and other segments move the other — visible only when dimensions are crossed against each other. Phase 2 systematically searches for these interactions.

### Procedure

**Mode-conditional scope.** The set of dimension pairs explored in Phase 2 depends on the declared engagement mode (read from `other/stage1_catalog.md`):
- **Standard mode:** Cross only pairs from the official segmentation spine declared at Stage 1 — categorical and temporal dimensions such as continent, channel, category, and year. Skip any candidate pair involving data-derived cluster groupings from Stage 2.9 (product clusters, customer clusters, behavioral clusters). From the candidate table in step 1, exclude any row whose cross includes a cluster dimension.
- **Deep mode:** Enumerate all applicable dimension pairs, including data-derived cluster groupings from Stage 2.9, as specified below.

1. **Identify candidate crosses.** For each finding, enumerate all applicable dimension pairs within the scope defined above. A cross is applicable if both dimensions can be joined to the finding's data table and each has ≥2 entities per cell of the cross. Typical candidates:

   | Cross | When Applicable | What It Reveals |
   |-------|----------------|-----------------|
   | Continent × Channel | Any multi-channel finding | Geographic channel-mix differences |
   | Continent × Year | Any temporal finding | Whether trends are global or regional |
   | Product cluster × Channel | Any product-level finding | Whether product tiers perform differently across channels |
   | Product cluster × Continent | Any product-level finding | Whether product behavior is geography-dependent |
   | Customer cluster × Product cluster | Online findings with both dimensions | Whether customer segments buy different product tiers |
   | Channel × Year | Any temporal finding | Whether channel trajectories are diverging |
   | Category × Channel | Any category-level finding | Whether categories play different roles by channel |

   Not all crosses are applicable to all findings — a finding about store performance does not need a customer-cluster cross (no customer_key in FactSales). The applicability filter is: can the cross be computed on the finding's source table?

2. **Compute each applicable cross.** For each finding × dimension pair:
   a. Compute the finding's metric broken by both dimensions simultaneously (e.g., margin by continent × channel).
   b. Compare the two-dimensional result to the single-dimension results from 4a.
   c. Classify the interaction:

   | Classification | Criteria | Action |
   |---------------|----------|--------|
   | **No interaction** | The two-dimensional pattern is the additive combination of the two single-dimension patterns. No cell deviates from the expected value by >15% (relative). | Confirmed — single-dimension cuts were sufficient. |
   | **Amplification** | One or more cells in the cross show a stronger version of the pattern than either single-dimension cut alone. | Revised — the finding is more nuanced than reported. Note which combination amplifies. |
   | **Reversal** | At least one cell in the cross shows the opposite direction from the single-dimension pattern. | Revised (material) — Simpson's Paradox detected at the interaction level. Replace the finding with the interaction-aware version. |
   | **New pattern** | The cross reveals a pattern not visible in any single-dimension cut — e.g., a high-margin category in low-margin channel, or a product cluster that over-indexes in one continent but not others. | New finding — add to the 4a-V exploration log and evaluate for promotion to a hypothesis. |

3. **Prioritize crosses by expected information value.** Not all crosses need equal depth. Prioritize:
   - Crosses involving dimensions that showed Divergent status in 4a (these are most likely to produce interaction effects)
   - Crosses involving dominant entities (the interaction of two dominant dimensions — e.g., Home Appliances × North America — can produce especially misleading aggregates)
   - Crosses that directly address a Stage 3 hypothesis (e.g., H14 asks about promotional effectiveness × continent — the continent × promotion cross is a direct pre-test)

4. **Stop when information gain drops.** If three consecutive crosses produce "No interaction" for a finding, remaining crosses for that finding can be marked "Expected no interaction — skipped based on prior results" unless they involve a Divergent or dominant dimension.

### Phase 2 Output: Exploration Log

One entry per cross attempted. The log captures both positive results (interactions found) and negative results (no interaction — confirming that single-dimension cuts were sufficient).

```
| Finding | Cross | Cell with Max Deviation | Deviation | Classification | Action |
|---------|-------|------------------------|-----------|---------------|--------|
| F3 | Continent × Channel | Asia × Store: +57.5% | Reversal from aggregate −30.6% | Reversal | REVISED: F3 is Divergent at interaction level |
| F2 | Category × Channel | HA × Online: 36.3% share vs Store 31.4% | +4.9pp | Amplification | Note: HA over-indexes online/reseller |
| F1 | Product cluster × Continent | — | <5% deviation in all cells | No interaction | Confirmed |
| F8 | Continent × Year | Asia 2007→2009: +41.5% vs NA −29.9% | Reversal | Reversal | REVISED: trend is Divergent by continent |
| — | Customer cluster × Product cluster | Cluster 3 × Cluster 1: $120 AOV vs $580 expected | New pattern | New pattern | NEW FINDING: Budget Explorers avoid Premium Hero products |
```

**New findings from Phase 2** are tagged `[4a-V-P2]` and recorded with:
- The cross that produced them
- The metric values
- A preliminary assessment of whether they are actionable (would they enter the hypothesis floor if discovered at Stage 3?)
- A recommendation: Promote to hypothesis / Note for 4b exploration / Document and move on

---

### Combined Output

All phases produce separate outputs that share a combined summary:

1. **Phase 1a completeness log** (register review: gaps, bias revisions, interactions)
2. **Phase 1b validation log** (finding × constraint → Confirmed / Revised / N/A)
3. **Phase 2 exploration log** (finding × cross → No interaction / Amplification / Reversal / New pattern)
4. **In-place 4a notebook updates** for any finding marked Revised in Phase 1b or Phase 2
5. **New findings list** from Phase 2, with promotion recommendations
6. **Consultant's Gate re-evaluation** if any headline finding changed
7. **Updated constraint register** (if Phase 1a added/revised rows, or Phase 2 discovers new constraints)

---

### Canonical Output

After all three phases are complete, write the following files per SKILL.md Rule 7. The notebook remains the analyst's full working interface and the primary review surface; these files are the session-portable records Claude Code reads for continuity in Stage 4b and beyond.

**1. Write `$PROJECT_ROOT/other/stage4av_validation_log.md`** — the Stage 4a-V canonical output.

`other/stage4av_validation_log.md` must contain:
- **Engagement mode and Phase 2 scope** — Standard or Deep (from `stage1_catalog.md`); in Standard mode, list the dimension pairs excluded; in Deep mode, confirm full cross-dimensional exploration was completed
- **Register completeness review** — the Phase 1a log: results of checks 1a.1 (missing constraints), 1a.2 (bias direction revisions), and 1a.3 (constraint interactions), with any new or revised register rows reproduced in full
- **Validation log table** — the complete Phase 1b table (finding × constraint → Confirmed / Revised / N/A / Process error) with evidence column and the summary row (total checks, confirmed, revised, N/A, process errors)
- **Multi-dimensional exploration log** — the complete Phase 2 table (finding × cross → No interaction / Amplification / Reversal / New pattern) with deviation values and any new findings tagged `[4a-V-P2]`, including their promotion recommendations

Write the file as structured markdown: one section per phase, suitable for direct reading without executing any code.

**2. Update `$PROJECT_ROOT/other/stage4a_findings.md` in place** — apply `[4a-V revised]` tags to every finding revised in Phase 1b or Phase 2, and append any new findings from Phase 2. This is the living document update specified in stage4a.md's Canonical Output section. After this update, `stage4a_findings.md` reflects the fully validated state of all Stage 4a findings.

If Phase 1a added or revised rows in the constraint register, also confirm that `$PROJECT_ROOT/data/constraint_register.csv` has been updated before proceeding.

---

### Batch Protocol

**Phase 1a:** Single pass. The register review is a small-N operation (register rows, not register × findings) and completes quickly.

**Phase 1b:** All findings in a single pass. Mechanical checking scales linearly and does not degrade under context pressure.

**Phase 2:** Batch by finding. Process 3–4 findings per batch, running all applicable crosses for each finding before moving to the next. This keeps the analytical context (what the finding says, what the single-dimension cuts showed) fresh while exploring crosses. Self-interrupt between batches with a summary of crosses attempted and interaction effects found.

If total findings × applicable crosses exceeds 60 cells, split Phase 2 into three batches: highest-priority crosses first (Divergent dimensions, dominant-entity interactions, hypothesis-relevant crosses), then moderate-priority, then low-priority.

---

### Gate Rule

**Stage 4b cannot begin until:**
1. Phase 1a completeness log is complete (all three checks documented)
2. Phase 1b validation log is complete (every finding × every register row, including any rows added in 1a)
3. Phase 2 exploration log is complete (every finding × every applicable cross, or explicitly skipped per the early-stop rule)
4. All Revised findings have been updated in the 4a notebook
5. New findings from Phase 2 have been evaluated for hypothesis promotion
6. The Consultant's Gate has been re-evaluated if any headline finding changed
7. The user has confirmed all logs

**Checkpoint message format:**
> "Stage 4a-V complete. Phase 1a: register reviewed — [A] constraints added, [B] bias directions revised, [C] interactions identified. Phase 1b: validated [N] findings against [M] constraints — [P] confirmed, [Q] revised. Phase 2: explored [X] multi-dimensional crosses — [Y] interactions found, [Z] new findings. Consultant's Gate [unchanged / updated]. Canonical output written to `other/stage4av_validation_log.md` and `other/stage4a_findings.md` updated — please review alongside the notebook before confirming. Ready to proceed to Stage 4b?"

**Mid-Flow Mode Adjustment:** Before confirming, assess whether anything discovered during Stage 4a-V — register gaps found in Phase 1a, constraint interactions, Phase 2 interaction effects, or new findings elevated to hypotheses — materially changes the complexity, reliability, or analytical depth of the engagement relative to the declared mode. If so, surface the specific observation and suggest a targeted adjustment for the affected stage(s). See SKILL.md § Engagement Modes — Standard and Deep for the asymmetric override rule.

---

### Running Notes Update

Before the checkpoint confirmation, append the completed Stage 4a-V section to `$PROJECT_ROOT/other/skill_notes.md` with the current date and any qualifying observations. The validation gate may produce observations about:
- Register rows that consistently produce N/A (trigger conditions may need refinement)
- Multi-dimensional crosses that consistently produce interactions (these dimension pairs should be flagged as "high-interaction" for future engagements)
- The Phase 2 early-stop rule effectiveness (was it invoked? Did it miss anything?)
