## Stage 4a — Foundational Frequency Analysis

**Goal:** Describe what is in the data. Checklist-driven, no modeling.

**Analytical mode: DESCRIBE** — What is in the data?

**Implementation scripts:** When implementing a named pattern from the domain files, load the corresponding script from `references/scripts/[domain]/[pattern-id].py` for the implementation code. Adapt column names and parameters to the current dataset.

### Pre-Flight: Constraint Register Acknowledgment

Before any analysis, load and acknowledge the constraint register (`$PROJECT_ROOT/data/constraint_register.csv` from Stage 2):

1. **Load** the register into the notebook setup cell as a DataFrame.
2. **Print** a summary: count by constraint_type, total affected rows, list of constraint IDs.
3. **For each constraint row**, state in a pre-flight markdown cell how it will be handled during this stage:
   - FLAGGED_POPULATION → "Will split findings that touch [table] with and without [flag column]"
   - DOMINANT_ENTITY → "Will condition findings on [dimension] by excluding [entity] where applicable"
   - REFERENTIAL_INTEGRITY → "Will restrict product-dimension findings to matched rows; will note asymmetric orphan rates by [dimension]"
   - DUAL_SPINE_OVERLAP → "Will not use [cluster] and [official dim] as independent cuts; [cluster] is a proxy"
   - TEMPORAL_INTEGRITY → "Will exclude [period] from trend calculations" or "No temporal constraints — all periods usable"
   - FIELD_RELIABILITY → "Will not use [column] for [analysis type]"
   - ANALYSIS_SCOPE → "Customer-level findings restricted to [population] covering [share] of [table]"
   - SCALE_CONSTRAINT → "Will use pre-computed CSVs from standalone script for [table]"

This acknowledgment is not optional prose — it is a structured checklist that makes downstream omissions traceable. If a finding later fails 4a-V validation because a register constraint was not handled, the pre-flight record shows whether the constraint was acknowledged but mishandled (execution error) or not acknowledged at all (process error).

### Batch Protocol (→ Context Preservation)

**Batch size:** 5–6 findings per pass. The mandatory frequency checklist produces 7 items; with dual-spine segment breakdowns and extensions, total findings can reach 12–15.

**Self-interruption:** After each batch, stop and present the batch summary with context carry-forward before continuing.

**Structural self-check (per finding, before moving to the next):**
- [ ] Narrative markdown cell present (not just code output)
- [ ] Segment classification stated (Uniform / Amplified / Attenuated / Divergent) for each applicable spine dimension, with actual numeric values (not labels alone)
- [ ] Finding stated as fact, not interpretation (4a is DESCRIBE mode)
- [ ] **Register reference block present:** For each applicable constraint_id, a one-line statement of how it was handled (excluded / included with caveat / N/A + reason)

### Segment Status Block Format

Every finding must include a segment status block with this structure. **4a performs single-dimension cuts only** — multi-dimensional crosses (continent × channel, product cluster × customer cluster, etc.) are the responsibility of Stage 4a-V Phase 2.

```
**Segment status:**
- **By [dimension] ([constraint_id if applicable]):** [Status] — [actual values per segment]. [One-sentence interpretation.]
- **By [dimension]:** N/A — [reason this dimension doesn't apply to this finding]

**Register acknowledgment:**
- [constraint_id]: [how handled]
- [constraint_id]: N/A — [reason]
```

The register acknowledgment sub-block replaces the previous ad-hoc approach where constraints were mentioned in prose (or not mentioned at all). Each constraint_id from the register must appear exactly once per finding — either with a handling statement or an N/A reason.

### Large Dataset Architecture (→ L1, L5, L6)

If any table was flagged as ABOVE NOTEBOOK-SAFE THRESHOLD in Stage 1:
1. Write standalone Python scripts (`build_stage4a_data.py`) to produce pre-computed CSVs
2. Process in chunks (5M rows default) using dictionary accumulators
3. Never use lambda aggregations on groupbys with >1M groups (→ L3)
4. Test scripts as plain `.py` before any notebook work
5. The notebook loads and displays the pre-computed CSVs — the heavy computation stays in the script (→ L1)

### Day-of-Month Normalization (→ T6)

When computing day-of-month aggregates, normalize by the number of occurrences of each day in the dataset. Days 29–31 have fewer occurrences than days 1–28 (not all months have 31 days, February lacks a 29th in non-leap years) and will appear artificially low if raw totals are compared without adjustment.

### Mandatory Frequency Checklist

If no customer or user IDs exist in the dataset, mark 'User/customer summary statistics' and 'Reorder/repeat behavior' as N/A. Substitute store-level or entity-level summary statistics and item-level selling-day distributions.

Run through all of these before any advanced analysis:

- [ ] **Top entities by volume across all segmentation spine dimensions** (products, categories, departments, and every other categorical dimension in the spine — ranked lists with cumulative share. Do not skip dimensions with low cardinality; a 3-level dimension can produce the most consequential finding if the levels have divergent trajectories.)
- [ ] **Distribution of key metrics** (basket size, order frequency, reorder rate — full histograms, not just means)
- [ ] **Temporal patterns** (day-of-week, hour-of-day, inter-event intervals — per seasonality scoping from Stage 2)
- [ ] **User/customer summary statistics** (frequency, recency, behavioral ranges)
- [ ] **Reorder/repeat behavior** (rates by entity, by category, by time)
- [ ] **Data coverage** (how many entities contribute what share of volume — Pareto)
- [ ] **Segment breakdowns** for every temporal pattern by primary segmentation dimensions (official categorical variables AND data-derived groupings from the dual spine where available). Classify each as Uniform / Amplified / Attenuated / Divergent before leaving 4a.

### Required Output
- One code cell + one narrative cell per checklist item
- All findings stated as facts, not interpretations
- No statistical tests — only counts, ranks, distributions, and shares

### Canonical Output

After completing all Stage 4a analytical work, write `$PROJECT_ROOT/other/stage4a_findings.md`. This is the Stage 4a canonical output per SKILL.md Rule 7 — the session-portable record Claude Code reads for continuity in later stages. The notebook remains the analyst's full working interface and the primary review surface; `stage4a_findings.md` is what Claude Code reads to re-establish Stage 4a context without opening the notebook.

**This file is a living document.** During Stage 4a-V, findings revised following constraint validation (Phase 1b) or multi-dimensional segment exploration (Phase 2) are updated in place in this file, tagged `[4a-V revised]`. The file always reflects the most current validated state of Stage 4a findings.

`other/stage4a_findings.md` must contain:
- **Declared engagement mode** — Standard or Deep (from `stage1_catalog.md`); no Stage 4a operations change based on mode, but the mode is carried forward for downstream traceability
- **Foundational frequency findings** — one entry per completed checklist item, stated as fact, with key metric values and Pareto or distribution shape where applicable
- **Segment status** — for each finding, the classification (Uniform / Amplified / Attenuated / Divergent) across every applicable spine dimension, with the actual numeric values that drove the classification
- **Register acknowledgment** — for each finding, how each applicable constraint_id was handled (excluded / included with caveat / N/A + reason)

Write the file as structured markdown: one section per finding, suitable for direct reading without executing any code.

### Running Notes Update

Before the checkpoint confirmation, append the completed Stage 4a section to `$PROJECT_ROOT/other/skill_notes.md` with the current date and any qualifying observations. Apply the threshold test and qualifying criteria from SKILL.md § Running Notes Protocol. If no observations qualify, write "No qualifying observations."

### CHECKPOINT — User reviews 4a findings. Hypothesis list may be updated before Stage 4a-V begins.
> "Stage 4a complete. [N] foundational findings produced across [M] checklist items. [K] findings classified by segment status (Uniform / Amplified / Attenuated / Divergent). Canonical output written to `other/stage4a_findings.md` — please review findings alongside the notebook before confirming. The hypothesis list from Stage 3 may be updated based on what Stage 4a revealed; any updates must be finalised before Stage 4a-V begins. Ready to proceed to Stage 4a-V?"

**Mid-Flow Mode Adjustment:** Before confirming, assess whether anything discovered during Stage 4a — a dominant entity whose exclusion produces qualitatively different aggregate profiles across multiple findings, or a finding where every applicable segment dimension shows Divergent status indicating more structural complexity than the declared mode assumes — materially changes the depth warranted for the next stages relative to the declared mode. If so, surface the specific observation and suggest a targeted depth adjustment for the affected stage(s) (e.g., upgrade 4a-V Phase 2 to full cross-dimensional even in Standard mode, or upgrade Stage 4b to all four moves). See SKILL.md § Engagement Modes — Standard and Deep for the asymmetric override rule.
