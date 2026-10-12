## Stage 4d — Confidence Audit (Mandatory Gate Before Stage 5)

**Goal:** Produce a single audit table covering every finding from all Stage 4 sub-stages. **No visualization work begins until Stage 4d is complete and confirmed.**

### Audit Table Columns

| Column | Description |
|--------|-------------|
| Finding ID | e.g., H1, H2, B1-H1, 4a-3 |
| Finding Tier | A / B / C (assigned in Stage 4c before testing; determines which gates were applied) |
| Finding Name | Descriptive title |
| Effect Size | Metric type + value (e.g., "Cramér's V = 0.23"). Mark "—" for Tier C. |
| Segment Stability | Stable / Qualified / Reversed / Not Tested — evaluated against both official and data-derived groupings. If they agree, report one status. If they diverge, report 'Divergent: [official status] / [derived status]'. |
| Segment Status | Uniform / Amplified / Attenuated / Divergent / Not Tested — reflects both official and data-derived groupings. Report 'Dual-Divergent' if the segment status differs between the two groupings. |
| Temporal Stability | Stable / Qualified / Unstable / Not Applicable. Mode-conditional scope: in Standard mode, populated for Tier A findings only (mark N/A for Tier B and Tier C); in Deep mode, populated for all findings with sufficient temporal history. |
| Bootstrap Stability | Stable / Qualified / Unstable / Skipped — Standard mode / Not Applicable. Populated for Tier A findings with rankings only: read from the mode-dependent gate log in `stage4c_verdicts.md`. Mark "Skipped — Standard mode" when S6 was not run due to Standard mode; mark "Not Applicable" when the finding has no rankings. |
| Dataset Limitation Flags | From standard checklist below |
| Convergent Evidence | Count of independent confirmations — identified actively during Stage 4c, not retrospectively. Mark "—" for Tier C. |
| Confidence Label | HIGH / QUALIFIED / FRAGILE / POPULATION-ONLY |
| One-Line Client Summary | Plain business language |

### Temporal Stability Column Specification

**Temporal Stability:** Did the finding exist in the first half of the data period and in the second half independently?

**Mode-conditional scope:** In Standard mode, apply this procedure to Tier A findings only — mark all Tier B and Tier C findings as "Not Applicable" without running the split-half test. In Deep mode, apply to all findings with sufficient temporal history.

**Procedure:**
1. **Applicability gate:** If the dataset has fewer than 6 distinct temporal periods (months, weeks, or the most granular time unit available), or if it has no absolute dates, mark as "Not Applicable" and continue. Do not attempt to apply the test on data that does not support it.

2. **If the dataset does have sufficient temporal history:** Split into first and second half by date. Re-execute the finding's primary test on each half independently.

3. **Classification:**
   - **Stable:** the finding is significant (with effect size at or above the threshold for its confidence tier) in both halves and in the same direction.
   - **Qualified:** the finding is significant in one half but not the other, or the effect size differs by more than 40% between halves. May reflect seasonal change or a trend rather than a stable pattern.
   - **Unstable:** the finding changes direction between halves. Automatically degrade to FRAGILE regardless of the result on the full dataset.

This column is completed after Segment Stability and before assigning the final label. A temporally Unstable finding cannot receive HIGH even if it passes all other tests.

### Standard Dataset Limitation Checklist

Check every finding against every item. Flag those that apply:

- [ ] No price or revenue data
- [ ] No absolute calendar dates
- [ ] Pre-filtered populations (data was filtered before arrival — e.g., only users with N+ orders)
- [ ] Structural scope gaps (a dimension exists for only a subset of the data — e.g., customer IDs on one channel only). Distinct from pre-filtering: the data was not removed, it was never collected for that subset.
- [ ] Right-censored or capped fields
- [ ] Competition or ML split artifacts
- [ ] Availability vs. preference confounding
- [ ] Cumulative metrics biased toward older/more active records

### Confidence Label Assignment Rules

- **HIGH:** Effect size meets threshold (see SKILL.md table), segment stability confirmed under both official and data-derived groupings (if dual spine is active), no material limitations
- **QUALIFIED:** Effect size 0.10-0.20 range, majority segment stability, or one constraining limitation
- **FRAGILE:** Effect size below threshold regardless of p-value, or population-level only without segment breakdown. **FRAGILE findings are excluded from Stage 5 entirely.**
- **POPULATION-ONLY:** Simpson's Paradox reversal detected. Must be rendered with segment-specific treatment in Stage 5.

**Tier-specific rules:**
- A **Tier B** finding cannot receive HIGH based on effect size alone if it has not been tested for Simpson's Paradox — the Simpson check is mandatory for Tier B.
- A **Tier C** finding can receive HIGH based on data coverage and sample size alone — it is a fact, not a hypothesis. No statistical gates are required.
- A **Tier A** finding that skipped any gate it should have run cannot receive HIGH — in Standard mode, S11 and S6 are legitimately excluded; verify the mode-dependent gate log in `stage4c_verdicts.md` shows these as Standard-mode skips, not process errors. For any other skipped gate, return to Stage 4c and complete it before finalizing.

### Meta-Summary (closing paragraph)

Count per confidence tier, identify the strongest convergent-evidence findings, and name which limitation affects the most findings. Name the single limitation that affects the most findings and state its impact in one sentence.

### Canonical Output

After completing the full confidence audit, write `$PROJECT_ROOT/other/stage4d_audit.md`. This is the Stage 4d canonical output per SKILL.md Rule 7 — the session-portable record Stage 5 reads to build the finding-to-chart mapping table without opening the notebook. The notebook remains the analyst's full working interface and the primary review surface.

`other/stage4d_audit.md` must contain:
- **Declared engagement mode and gate coverage** — Standard or Deep (from `stage1_catalog.md`); temporal stability scope applied: Tier A only [Standard] / all findings [Deep]; bootstrap stability coverage: per mode-dependent gate log in `stage4c_verdicts.md`
- **Confidence audit table** — one row per finding from all Stage 4 sub-stages, with all columns populated: finding ID, finding tier, finding name, effect size, segment stability, segment status, temporal stability, bootstrap stability, dataset limitation flags, convergent evidence count, confidence label, and one-line client summary
- **Temporal stability results** — the split-half test results for every finding where temporal stability was applied (Tier A only in Standard mode; all findings in Deep mode), with the half-period boundaries used and the classification (Stable / Qualified / Unstable)
- **Final finding inventory** — the definitive list of findings entering Stage 5, grouped by confidence label (HIGH, QUALIFIED, POPULATION-ONLY), with all FRAGILE findings listed separately as excluded from Stage 5

Write the file as structured markdown: one section per content area above, suitable for direct reading without executing any code.

### Running Notes Update

Before the checkpoint confirmation, append the completed Stage 4d section to `$PROJECT_ROOT/other/skill_notes.md` with the current date and any qualifying observations. Apply the threshold test and qualifying criteria from SKILL.md § Running Notes Protocol. If no observations qualify, write "No qualifying observations."

### CHECKPOINT — DO NOT PROCEED TO STAGE 5 WITHOUT USER CONFIRMATION
> "Stage 4d complete. [N] findings audited across all Stage 4 sub-stages. Confidence labels: [A] HIGH, [B] QUALIFIED, [C] FRAGILE (excluded from Stage 5), [D] POPULATION-ONLY. [E] findings flagged with dataset limitations. Canonical output written to `other/stage4d_audit.md` — please review the full audit table alongside the notebook before confirming. **No visualization work begins until the audit table is confirmed.** Ready to proceed to Stage 5?"

**Mid-Flow Mode Adjustment:** Before confirming, assess whether anything surfaced in the audit — a QUALIFIED finding without temporal stability that is a strong candidate for elevation, or a pattern across multiple findings where the same unrun gate drives multiple QUALIFIED labels — warrants targeted depth upgrades before Stage 5 begins. If so, surface the specific observation and the gate(s) to run. See SKILL.md § Engagement Modes — Standard and Deep for the asymmetric override rule.
