---
name: eda-analytics
description: >
  Multi-stage EDA pipeline (6 major stages with sub-stages) for turning raw business
  data into validated, confidence-labeled analytical notebooks. Use this skill whenever the user asks for
  exploratory data analysis, data investigation, business analytics, dataset profiling,
  hypothesis testing on tabular data, multi-table analysis, customer segmentation,
  market basket analysis, or any multi-step analysis workflow — even if they don't say
  "EDA" explicitly. Trigger on: "analyze this data", "what can we learn from this CSV",
  "profile this dataset", "find insights in this data", "help me understand this data",
  "run analytics on", "build an analysis notebook", inventory analysis, sales analysis,
  churn analysis, cohort analysis, any request involving CSV/Excel/Parquet data where the
  user wants business-actionable findings, any request involving multiple related tables,
  or any request where the user provides a dataset and asks open-ended questions about it.
  Also trigger when the user references a Kaggle dataset, competition data, or any
  structured analytical project with more than one data file.
---

# EDA Analytics Pipeline — v2

A rigorous, multi-stage exploratory data analysis pipeline (Stages 1–6, with Stage 4 subdivided into 4a, 4a-V, 4b, 4c, 4d) that transforms raw business data into validated, confidence-labeled analytical notebooks with actionable findings.

## Core Philosophy

### Simplicity Before Complexity

At every stage, exhaust simple, visually clear, and directly actionable insights before increasing analytical complexity. A ranked bar chart of the top 20 products is more valuable to a consulting client than a clustering silhouette score if the bar chart can drive a decision tomorrow.

This principle applies at every stage:
- **Stage 1** describes before it analyzes
- **Stage 3** proposes Tier 1 frequency questions before any statistical hypothesis
- **Stage 4a** runs descriptive passes before modeling
- **Stage 4b** explores surprising patterns before formal testing
- **Stage 5** visualizes the simplest findings first

Complexity is not a signal of quality — **actionability is**. The test for every output at every stage:

> **Could a smart business owner with no data background read this and know what to do on Monday?**

If yes: include with full treatment. If no: either simplify, move to Analysis Alternatives, or exclude.

### The 12-Month Revenue Test

Every analytical decision must pass:

> **"Can a decision-maker act on this finding in the next 12 months to protect or grow revenue?"**

This test applies at **hypothesis design time** (Stage 3), not just at finding time (Stage 4). Every hypothesis must have a "if confirmed, the client does X on Monday" action written alongside it. If the action requires further modeling before anyone can act, the hypothesis belongs in Analysis Alternatives, not the hypothesis floor.

### Context Preservation

Long analytical passes degrade output quality through three mechanisms that compound silently:

1. **Context pressure.** As accumulated output pushes original instructions further back in the context window, structural compliance drops. Required template elements that were followed perfectly in the first item begin disappearing.
2. **Planning dilution.** Later items in a large batch receive shallower planning attention than early items. The first hypothesis gets a full gate battery; the eighth gets a summary paragraph.
3. **Template simplification.** Claude Code establishes the correct template on the first 1–2 items, then silently drops required elements for all subsequent items. This is not gradual — it appears as a cliff, typically between item 1 and item 3, and never recovers within the same execution pass.

The only reliable mitigation is **batch discipline**: self-interrupt after a calibrated number of items, report results, receive confirmation, and then continue with fresh attention.

**Whose responsibility:** Claude Code's, not the user's. When this skill specifies a batch size for a stage, Claude Code must stop execution after completing that batch, present results, and wait for user confirmation before proceeding to the next batch. This is a hard rule. It applies even if the user's prompt says "run all of Stage 4c" or "complete Stage 5" — the batch limit overrides the scope of the prompt.

**Self-check protocol (per-item, not per-batch):** Before moving to the next item within a batch, verify that the current item contains all required structural elements for that stage. If an element is missing, fix it before proceeding. This catches template simplification within a batch. The structural checklist for each stage is specified in the corresponding `references/stages/stage[N].md` file under that stage's Batch Protocol section.

**Self-interruption message format:**
> "Batch [N] complete: [item IDs]. [1-2 sentence summary]. Context carry-forward: [any cross-references or analytical threads that the next batch should pick up]. Proceeding to batch [N+1] ([item IDs]). Confirm or provide corrections."

The context carry-forward note preserves analytical momentum across batch boundaries — findings that build on prior findings, hypotheses that share a causal thread, or patterns that emerged mid-batch and should inform the next batch's interpretation.

**Batch boundary thematic grouping:** Where possible, batch related items together — temporal hypotheses in one batch, segmentation hypotheses in another; Tier C charts in one batch, Tier A charts in another. Arbitrary count-based splits lose analytical continuity. The batch size is a maximum, not a target — if a thematic group contains fewer items than the batch limit, complete the group and self-interrupt.

See the corresponding `references/stages/stage[N].md` file for the calibrated batch size, structural checklist, and protocol for each stage.

### Script-Primary Execution and Read/Write Boundary

Scripts handle what notebooks should not: heavy computation that would strain notebook execution, reusable utility functions shared across stages, and outputs that downstream stages need to reference by file. Analytical logic lives in notebooks — scripts are a relief valve and a shared library, not the analytical home.

**Claude Code's read/write boundary** governs session continuity, not where analysis lives:

| File type | Read | Write |
|-----------|------|-------|
| `.ipynb` | Never (for state checking) | Yes (cells during execution) |
| `.py` | Yes | Yes |
| `.md` | Yes | Yes |

Claude Code writes code cells to notebooks during execution. It never reads a `.ipynb` file to check analytical state, recover findings, or establish where a session left off. For continuity between stages and sessions, Claude Code reads the canonical stage output files in `other/` (→ Project File Structure Rules, Rule 7) and the relevant `.py` scripts.

This boundary holds because notebook state is volatile — outputs captured at a prior execution time cannot reliably represent current analytical state. The canonical `.md` stage outputs are the durable, session-portable record of what was found and decided.

---

## Pipeline Overview

The pipeline has seven stages with mandatory checkpoints. **Never proceed to the next stage without explicit user confirmation.**

Checkpoint message format:
> "Stage [N] complete. [2-3 sentence summary]. Ready to proceed to Stage [N+1]? Please confirm or provide corrections."

| Stage | Name | Goal | Key Output |
|-------|------|------|------------|
| 1 | Data Source Inventory | Complete map of every data source | Field-level catalog, relationship map, scale flags, segmentation spine |
| 2 | Data Quality & Preparation | Identify and treat every quality issue | Clean master DataFrame(s), quality log, **constraint register** |
| 3 | Research Brief & Hypothesis Floor | Define guaranteed analysis scope via three-tier system | Tiered hypothesis list, boundary check, research context |
| 4a | Foundational Frequency Analysis | Describe what is in the data | Ranked lists, distributions, foundational metrics |
| 4a-V | Validation Gate | Verify every 4a finding against contamination, segments, dominance, overlap | Validation log table, in-place 4a revisions |
| 4b | Autonomous Exploration | Interrogate the data for surprises | Four-move exploration findings |
| 4c | Formal Hypothesis Testing | Test confirmed hypotheses in batches | Verdicts + actions per hypothesis |
| 4d | Confidence Audit | Label every finding before visualization | Audit table: one row per finding, segment status per finding |
| 5 | Dashboard-Ready Notebook | Plotly visual assets for confirmed findings | Chart + narrative pairs |
| 6 | Skill Update | Harvest reusable lessons into the EDA skill | Updated SKILL.md, stages/, lessons.md, industry/ domain files, scripts/ |

Certain operations within stages run at different analytical depths depending on the declared engagement mode (Standard or Deep). See → Engagement Modes — Standard and Deep.

**Stage 4a-V is a mandatory validation gate between 4a and 4b.** It cannot be skipped or folded back into 4a. It runs in two phases:

- **Phase 1a — Register Completeness Review:** Verify the register itself is complete (missing constraints, underspecified bias directions, constraint interactions). Phase 1b then validates each finding against the (now-verified) register. Produces a validation log table.
- **Phase 2 — Multi-Dimensional Segment Exploration (analytical):** For each finding, cross it against relevant combinations of segment dimensions (continent × channel, product cluster × continent, etc.) to discover interactions that single-dimension cuts miss. Phase 2 is never skippable, even when Phase 1's register is clean — the value of multi-dimensional exploration is independent of data quality issues.

See `references/stages/stage4av.md` for the full specification.

**Stages 4a-V, 4b, and 4a all feed back into the hypothesis list before Stage 4c begins** — the pipeline is not purely linear. See the checkpoint sections in `references/stages/stage4a.md`, `references/stages/stage4av.md`, and `references/stages/stage4b.md` for the feedback loop specification.

**Before beginning any stage, read `references/stages/stage[N].md`** for the detailed specification of that stage only. Do NOT preload other stage files — they are irrelevant to the current stage and waste context budget. Each stage file contains the required outputs, sub-steps, batch protocol, and quality gates for that stage.

---

## Engagement Modes — Standard and Deep

Every engagement runs in one of two modes — **Standard** or **Deep** — declared by the analyst at Stage 1. The mode determines the depth of specific operations at specific stages; the overall pipeline structure remains identical in both modes. All stages run, all checkpoints fire, and all canonical outputs are written regardless of which mode is active.

### Mode Reference Table

| Stage | Feature | Standard | Deep |
|-------|---------|----------|------|
| 4a-V | Multi-dimensional segment exploration (Phase 2) | Primary dimensions only | Full cross-dimensional |
| 4b | Autonomous exploration moves | Two moves (Condition & Compare, Cross Two Metrics) | Four moves (adds Distributions Not Averages, Challenge an Assumption) |
| 4c | Causal direction test (S11, Tier A only) | Flag causal claim in the finding; do not run the formal two-step protocol | Full two-step protocol (mechanical plausibility + conditional Granger test if temporal data available) |
| 4c | Bootstrap stability (S6, Tier A rankings only) | Skip; do not present as a stability-tested ranking | Full 200x resample with stability classification |
| 4d | Temporal stability split-half | Tier A findings only | All findings with sufficient temporal history |
| 3 | Macro data menu (§3.3) | Skip | Produce the macro data menu |
| 5 | Narrative depth graduation by convergent evidence count | Single narrative depth for all HIGH findings | Graduated depth based on convergent confirmation count |

Everything not listed in this table runs identically in both modes. The table is exhaustive for mode-dependent behavior — absence from the table means no mode dependency.

### Mid-Flow Mode Adjustment

At each stage checkpoint, Claude Code assesses whether anything discovered during that stage materially changes the complexity, reliability, or analytical depth of the engagement relative to what was assumed when the mode was declared. If so, it surfaces the specific observation and suggests a targeted depth adjustment for the affected stage(s) only — not a wholesale mode switch.

**Illustrative triggers (examples, not an exhaustive list):**
- Stage 4a reveals a dominant entity whose exclusion produces qualitatively different segment profiles across multiple dimensions → suggests upgrading 4a-V Phase 2 to full cross-dimensional even in Standard mode.
- Stage 4c Tier A findings generate action recommendations in a domain where causal direction is genuinely contestable (e.g., promotional spend driving revenue vs. revenue driving promotional budget) → suggests running the S11 two-step protocol for those specific findings even in Standard mode.
- After Stage 3, the hypothesis floor contains only Tier 1 descriptive questions with no Tier A findings expected — this is a null case. S11, S6, and temporal stability are not applicable regardless of mode; the mode distinction has no practical effect on gate execution for this engagement. Note the observation at the Stage 3 checkpoint; no adjustment is needed in either direction.

**Asymmetric override rule:** Upgrades to Deep-level depth for a specific stage are always available on request. Downgrades from the declared mode require a one-line justification from the analyst, logged in the canonical output for that stage.

---

## Project File Structure

Every engagement must use this standard folder structure. Claude Code creates it at the start of Stage 1, before writing any file.

```
[project-name]/
  data/           — all input files: CSVs, Excel, Parquet, database exports,
                    any raw or processed data files
  notebooks/      — full analytical interface: stage1_, stage2_,
                    stage3_, stage4a_, stage4b_, stage4c_, stage4d_,
                    stage5_ notebooks containing code cells, markdown
                    narrative, and outputs — the analyst's primary
                    working and review surface
  scripts/        — standalone heavy computation offloaded from
                    notebooks, shared utility functions, and pre-built
                    outputs consumed by downstream stages
  dashboard/      — the complete Dash application: app.py, data_prep.py,
                    assets/, components/, sections/
  other/          — canonical stage output files (stage[N]_*.md),
                    running notes (skill_notes.md), and catch-all
                    files: PDFs, client references, exported charts,
                    zip files, README notes
```

### Rules

1. **Create at Stage 1 start.** If the project folder already exists with files in it, organize existing files into the correct subfolders before proceeding.
2. **Notebook naming:** `stage[N][letter]_[descriptor].ipynb` — e.g., `stage4a_foundational_frequency.ipynb`, `stage4c_hypothesis_testing.ipynb`. The stage sequence must be visible from the filesystem without opening any file. **Stage 4a-V does not produce its own notebook** — it updates the 4a notebook in place (adding `[4a-V revised]` tags to changed findings) and produces its validation and exploration logs as the canonical `other/stage4av_validation_log.md` (→ Rule 7); key summary findings may also be added as markdown cells in the 4a notebook.
3. **Script naming:** `build_[descriptor].py` for data preparation scripts, `utils_[descriptor].py` for reusable utilities. This distinguishes one-time build scripts from reusable helpers.
4. **data/ is read-only after Stage 2.** No script or notebook may modify or overwrite files in `data/` after the quality treatment is complete. Derived or transformed files go into `data/` only during Stages 1 and 2, and are then frozen.
5. **dashboard/ is created only when Stage 5 begins.** It does not exist as an empty placeholder during earlier stages.
6. **other/ is a catch-all, not a dump.** Canonical stage output files (Rule 7) and the running notes file (`skill_notes.md`) belong there by design and are exempt from the comment requirement. Any other file placed in `other/` (PDFs, client reference files, exported charts, zip files, README notes) must have a one-line comment in the Stage 1 notebook explaining what it is and why it doesn't belong in the other folders.
7. **Canonical stage outputs.** Each stage produces a canonical markdown output file written to `other/`. These files are the working memory of the engagement — Claude Code reads them for continuity between stages and sessions, not notebooks. Naming convention: `stage[N][letter]_[descriptor].md`. Canonical file for each stage:

   | Stage | File | Contents |
   |-------|------|----------|
   | 1 | `other/stage1_catalog.md` | Field-level catalog, relationship map, segmentation spine, impossible questions, scale flags |
   | 2 | `other/stage2_quality_log.md` | Quality issues log, constraint register, dual-spine groupings, declared engagement mode (traceability) |
   | 3 | `other/stage3_research_brief.md` | Selected hypothesis floor (§3.6 filtered), declared mode and filtering parameters, boundary check, research context |
   | 4a | `other/stage4a_findings.md` | Foundational frequency findings (living document, updated through 4a-V) |
   | 4a-V | `other/stage4av_validation_log.md` | Validation log table, multi-dimensional segment findings |
   | 4b | `other/stage4b_exploration.md` | Autonomous exploration findings |
   | 4c | `other/stage4c_verdicts.md` | Hypothesis verdicts, confidence labels, recommended actions, mode-dependent gate log (S11/S6 per Tier A) |
   | 4d | `other/stage4d_audit.md` | Full confidence audit table |
   | 5 | `other/stage5_chart_manifest.md` | Chart-narrative pairs, final deliverable map |
   | 6 | `other/stage6_skill_update.md` | Skill update candidate table, discarded candidates list, closing inventory |

---

## Confidence Labeling System

Every finding must carry exactly one label, justified with specific test results:

| Label | Criteria | Action |
|-------|----------|--------|
| **HIGH** | Cramér's V ≥ 0.20 (or equivalent effect size), segment stability confirmed, no material dataset limitations | Act with full confidence |
| **QUALIFIED** | Cramér's V 0.10–0.20, majority segment stability, or one constraining limitation | Act with stated caveats |
| **FRAGILE** | Cramér's V < 0.10 regardless of p-value, or population-only without segment breakdown | Do not act — monitor only. **Excluded from Stage 5.** |
| **POPULATION-ONLY** | Simpson's Paradox reversal detected across segments | Withdraw population recommendation; replace with segment-specific actions |

### Effect Size Thresholds by Test Type

| Test Type | HIGH | QUALIFIED | FRAGILE |
|-----------|------|-----------|---------|
| Cramér's V | ≥ 0.20 | 0.10–0.20 | < 0.10 |
| Cohen's d | ≥ 0.50 | 0.20–0.50 | < 0.20 |
| Spearman r | ≥ 0.30 | 0.10–0.30 | < 0.10 |
| Percentage point gap* | ≥ 10pp | 5–10pp | < 5pp |

*Percentage point gap thresholds are skill conventions calibrated for business consulting contexts, not published statistical standards. Cramér's V, Cohen's d, and Spearman r rows follow Cohen's published conventions.

### Critical Rule: Statistical Significance on Large Datasets

On datasets above 1 million rows, **statistical significance is guaranteed for any real effect**. p-value alone is never a valid confidence criterion. Effect size and practical significance must always be the primary basis for the confidence label.

### Simpson's Paradox Detection (Mandatory)

After **every** population-level correlation or proportion finding, explicitly check whether the finding holds direction across all primary segments — both official categorical variables and data-derived groupings from the dual spine (→ stages/stage2.md § 2.9). If the finding holds under official segments but reverses under data-derived segments (or vice versa), this is a segmentation divergence finding. If it reverses in any segment:
1. Reclassify immediately as POPULATION-ONLY
2. Withdraw any population-level recommendation
3. Replace with segment-specific recommendations
4. Flag for POPULATION-ONLY visualization treatment in Stage 5

This check is mandatory in every hypothesis test, not optional.

### Incomplete Finding Rule

A finding reported without its segment breakdown is incomplete regardless of effect size. Every finding in Stage 4c must carry a segment status (Uniform / Amplified / Attenuated / Divergent) before it can receive a final confidence label.

When the dual spine is active (i.e., data-derived groupings were produced in Stage 2.9), the segment status must reflect testing against both official and data-derived groupings. If both agree, report a single status. If they diverge, report both with an explicit note identifying the divergence.

---

## Finding Validation Tiers

Every finding is classified into one of three tiers at the moment it is first documented in Stage 4. The tier determines which validation gates are applied — not every finding warrants the full nine-gate battery.

### Tier Definitions

**Tier A — Strategic Findings.** Findings that will directly drive investment decisions, major operational changes, resource reallocation, or appear as primary recommendations in the client deliverable. These are findings a client will act on with meaningful cost or risk. **Apply the full nine-gate validation battery.**

**Tier B — Supporting Findings.** Findings that provide context, explain mechanisms, or support a Tier A finding. Directional signals that inform but do not directly drive decisions. **Apply five gates:** effect size, Simpson's Paradox, commercial subset, multiple comparisons, and convergent evidence. Skip confound control, causal direction, bootstrap stability, and temporal stability unless the finding is being elevated to Tier A.

**Tier C — Descriptive Findings.** Tier 1 frequency outputs — top N lists, distribution shapes, basic counts and shares, temporal patterns. Facts derived directly from the data, not tested hypotheses. **No statistical gates.** Report with full narrative but without validation machinery.

### Classification Rule

Assign the tier when a finding is first documented in Stage 4, before running any tests. The tier can be **elevated** (C→B or B→A) if subsequent analysis reveals the finding is more consequential than initially assessed. The tier **cannot be lowered** after tests have been run — a finding that failed a gate stays at its tier with its degraded label.

### Gate Map

| Gate | Tier A | Tier B | Tier C |
|------|--------|--------|--------|
| Effect size (S3, S9) | ✓ | ✓ | — |
| Commercial subset (S4, P6) | ✓ | ✓ | — |
| Confound control (S10) | ✓ | — | — |
| Causal direction (S11) | ✓ | — | — |
| Simpson's Paradox (S8) | ✓ | ✓ | — |
| Multiple comparisons (S2) | ✓ | ✓ | — |
| Bootstrap stability (S6) | ✓ | — | — |
| Temporal stability (4d) | ✓ | — | — |
| Convergent evidence (4c) | ✓ | ✓ | — |

Three Tier A operations are mode-dependent. Causal direction (S11) and bootstrap stability (S6) are execution-time gates applied during Stage 4c; temporal stability is an audit-time column applied during Stage 4d and is not a Stage 4c gate. In Standard mode, S11 and S6 are skipped during Stage 4c; the temporal stability column in Stage 4d covers Tier A findings only. In Deep mode, S11 and S6 run during Stage 4c for applicable findings — S6 applies specifically to rankings that inform investment, inventory, or prioritization decisions, not to all Tier A findings; the temporal stability column in Stage 4d covers all findings with sufficient temporal history. See → Engagement Modes — Standard and Deep.

---

## The Four Autonomous Exploration Moves

These four analytical moves are the conceptual engine of Stage 4b. They are the core mental model for data interrogation. Stage 4b applies Moves 1 and 2 in Standard mode, all four in Deep mode (→ Engagement Modes — Standard and Deep).

### Move 1: Condition on a Variable and Compare Groups
For any entity whose presence is large enough that excluding it would materially change an aggregate finding, compare observations with vs. without it. Example: orders with bananas vs. without — do basket sizes differ? Data-derived cluster assignments from Stage 2.9 are conditioning candidates alongside official categorical variables — conditioning on a data-derived grouping that captures behavioral structure the official segmentation misses can reveal the most distinctive 4b findings.

### Move 2: Cross Two Metrics Examined Independently
The intersection of two metrics reveals what neither reveals alone. Example: cross reorder rate × basket size to find the quadrant of high-loyalty, large-basket users.

### Move 3: Look at Distributions, Not Averages
For every aggregate metric reported as a mean, examine the full distribution shape. Bimodal distributions and heavy tails are more actionable than means. Example: "average basket size is 10" hides that the distribution is bimodal (quick-trip vs. stock-up).

### Move 4: Challenge an Assumption by Testing the Opposite
Identify what a smart person would assume about the business and test whether the data contradicts it. Example: "organic products must have higher reorder rates" — test it; the answer may surprise.

---

## Second-Order Analysis Checklist

After Stage 4a single-variable frequencies, mandate these moves before hypothesis testing:

- [ ] **Conditional splits** on any entity whose presence is large enough that excluding it would materially change an aggregate finding
- [ ] **Lifecycle curves** plotting key metrics as a continuous function of any sequence variable
- [ ] **Quadrant analysis** crossing the two most important metrics, examining all four quadrants
- [ ] **Distribution shapes** for every aggregate metric reported as a mean
- [ ] **Feature cross-correlation matrix** across all entity-level features, flagging unexpected sign directions
- [ ] **Dual-spine divergence check** on any finding where official and data-derived groupings are both available — does the finding's segment status change depending on which grouping is used?

---

## Segmentation Spine and Default Segmentation Protocol

Segmentation is default analytical behavior, not a response to a specific condition. Every aggregate finding is a starting point, not a conclusion. An aggregate number reported without its segment breakdown is an incomplete finding.

### Stage 1: Identify Spine Dimensions

After completing the field-level catalog, identify all dimensions available for segmentation and document them explicitly as the **segmentation spine** for the analysis. The spine typically includes:

- **Product dimension:** family, category, class, perishable flag — whichever levels have enough entities to be meaningful
- **Store/location dimension:** store type, format, geography (city, state, region), cluster
- **Time dimension:** year, half, quarter — for temporal stability checks
- **Customer dimension:** tier, segment, channel — if customer IDs exist
- **Behavioral dimension:** any binary flag that creates natural splits (promoted vs. not, perishable vs. not, new vs. established)

The spine is identified at Stage 1 and finalized at Stage 2 after data-derived segmentation candidates are produced (→ stages/stage2.md § 2.9).

### Stage 2.9: Data-Derived Segmentation and the Dual Spine

**Source-of-truth hierarchy:** This section (SKILL.md) is authoritative for principles (what and why). `references/stages/stage2.md` § 2.9 is authoritative for procedural details (how — method selection, cluster count, interpretability gate steps). If they ever conflict, the principles here govern.

After data cleaning is complete (2.1–2.8), derive a data-driven grouping for every categorical dimension in the spine and compare it against the official classification. See `references/stages/stage2.md` § 2.9 for the full procedure. The key principles:

- **Dual spine:** Both the official and data-derived groupings travel through the rest of the analysis. When the skill specifies "split by segmentation spine dimension," both are tested.
- **Interpretability gate:** Every cluster must be nameable in business language. A cluster that cannot be named is merged with its nearest neighbor. "Cluster 3" is not a deliverable.
- **Comparison is mandatory:** For every dimension, report variance explained by both groupings. The comparison itself — the gap — is part of the deliverable, regardless of which grouping wins.
- **Method is situation-dependent:** No single clustering approach is prescribed. The method selection framework in stages/stage2.md § 2.9 matches method to data characteristics.
- **Cluster count is data-derived:** Silhouette analysis or elbow method, constrained by domain sense. Never a hardcoded default.

The dimension menus by entity type and sector are documented in `references/industry/statistical-methods.md` § P7.

**Dominant entity detection within the spine:** For each dimension, compute the volume share distribution. Flag an entity as a dominant entity candidate when its volume share is visibly disproportionate relative to other entities in the same dimension — meaning its inclusion could plausibly change aggregate statistics in a materially different direction than the rest of the population. The test is: "Is the gap between this entity and the next large enough that its inclusion could materially change aggregate statistics?" When in doubt, flag with a sidenote reporting the share gap and let the analyst decide before Stage 4a begins. The assessment is qualitative and distribution-relative — no fixed threshold applies. Check all primary dimensions, not just the most obvious one.

### Stages 4a–4c: Segment in Parallel, Not Post-Hoc

For every confirmed aggregate finding, produce the segment breakdown as a standard paired output:

1. **Compute the aggregate.** This is the headline number.
2. **Immediately split by each relevant spine dimension.**
3. **Classify the result:**
   - **Uniform:** All segments tell the same story. The finding is robust. One sentence confirms it.
   - **Amplified:** Some segments show a stronger version. Report the segment finding as primary — the aggregate was understating it.
   - **Attenuated or reversed:** Some segments show a weaker or opposite pattern. The segment finding replaces the aggregate as the reportable result.
   - **Divergent:** Different segments tell different stories. They are different business problems and must be reported separately.

Every finding in the Stage 4c phase summary table must carry a segment status: Uniform / Amplified / Attenuated / Divergent.

### The Dominant Entity Case

When one entity represents a disproportionate share of total volume, it gets priority in the segmentation pass. Excluding the dominant entity is the most important single split. But — critically — the simple binary check ("does the finding hold?") is the floor, not the ceiling. If time allows, run the excluded population as a distinct analytical pass through the relevant 4a/4b/4c questions. The most valuable insights are often what the excluded population reveals that the aggregate suppressed.

A finding that holds only because of the dominant entity is a finding about that entity, not a general finding. A finding that is stronger without the dominant entity is a finding about the rest of the business that was being suppressed. A finding that shows different mechanisms in the two populations is the most actionable of all — it tells the client they are running two businesses under one roof.

### Minimum Segment Size

A segment is only worth reporting if a client could act on a finding about it. Do not apply a fixed minimum size threshold. A segment representing a negligible share of volume with no operational independence is not independently actionable — but it may be actionable as part of a group or as a mechanism explanation. Document the size and business relevance of each segment before reporting findings about it.

### Category Launch Detection

When an entity shows growth that is extreme relative to its peers in the same dimension, check its base-period volume. Growth from a near-zero base is a category launch or new-entity introduction, not organic growth of an established business, and must be reported differently. The test is not a fixed growth percentage — it is whether the base-period volume is negligible relative to the entity's current-period volume.

### Segmentation Variable Evaluation

When evaluating segmentation variables for explanatory power, test them against multiple dependent variables, not just one. A variable that explains traffic may not explain assortment mix, and vice versa. The most useful segmentation variable may differ depending on the business question being asked.

This evaluation is the conceptual foundation of the Stage 2.9 dual-spine comparison. The same principle — test against multiple dependent variables, report the one that explains most — applies to the choice between official and data-derived groupings throughout Stages 4a–5.

---

## Consultant's First-Day Gate

After completing foundational frequency analysis (4a), pause and ask:

> **If you had 30 minutes with a client who knows their business but has never seen this data, what 3 findings would make them lean forward?**

If the current findings would not surprise anyone, the interrogation pass (4b) has not gone deep enough. Apply the four autonomous exploration moves and the second-order checklist before proceeding.

---

## Describe vs. Interrogate — Two Named Analytical Modes

| Mode | Stage | Mindset | Question |
|------|-------|---------|----------|
| **Describe** | 4a | What is in the data? | Frequencies, rankings, distributions — the facts |
| **Interrogate** | 4b | What is surprising, contradictory, or actionable? | Contrasts, paradoxes, reversals — the insights |

Both are necessary and require different mindsets. The hypothesis floor is written after both passes, because the best hypotheses come from interrogation, not description. **Never skip 4b to rush to 4c.**

---

## Lesson Index

These lessons encode hard-won methodological principles. They are referenced by ID throughout the pipeline. **Do NOT preload `references/lessons.md` at the start of any stage.** The Lesson Index below contains sufficient context for most execution — the ID and one-line description are enough to apply most lessons correctly. Load `references/lessons.md` only when you need the full procedural detail for a specific lesson (e.g., S10's confound control procedure, S11's causal direction protocol, S6's bootstrap specification) or during Stage 6's learning harvest. When you do load it, read only the specific lesson section you need, not the entire file.

### Metric Design
- **M1** — No arbitrary composite weights (require theory + collinearity test)
- **M2** — No arbitrary thresholds (derive from data: percentiles, elbows, industry standards)
- **M3** — Cumulative metrics carry age/time bias (normalize or use rates)
- **M4** — Platform/system metrics carry structural bias (validate against independent signal)
- **M5** — Composite indices must be sensitivity-tested (two alternative weightings)

### Data Quality
- **Q1** — Variables that appear to measure X may measure Y (cross-validate meaning)
- **Q2** — External datasets require source validation (methodology, source, vintage)
- **Q3** — Sentinel values masquerade as real data (scan extremes, replace with NaN)
- **Q4** — Binary flags have error rates that change conclusions (estimate error direction)
- **Q5** — Missing data patterns determine valid analyses (test missingness vs. outcome)
- **Q6** — String/encoding issues in legacy regional data are the norm (treat in Stage 2)
- **Q7** — Mid-dataset schema introductions create structural analysis windows (identify boundary, restrict analyses)
- **Q8** — Dominant placeholder entities in dimension tables (flag any entity whose row count is visibly disproportionate relative to other entities in the same dimension table — contamination risk for order-level, basket-level, or customer-level analyses; assessment is distribution-relative, no fixed multiplier applies — then split-test downstream)
- **Q9** — Return-only rows are a distinct record type (cross-reference return fields before flagging zero-sales as sentinels)
- **Q10** — Referential integrity losses must be profiled by segmentation spine (asymmetric orphan rates across dimensions)

### Statistical Validity
- **S1** — Correlation requires causal interrogation before strategic translation
- **S2** — Multiple comparisons require correction (Bonferroni or BH-FDR)
- **S3** — Effect size matters more than significance on large datasets (report Cohen's d, rho, Cramér's V)
- **S4** — Findings must survive restriction to commercially significant subset
- **S5** — Trend lines require R-squared reporting (>=0.25 directional, >=0.60 actionable)
- **S6** — Bootstrap stability for rankings and thresholds (resample 200x, classify by stability ≥80%/60-80%/<60%) (→ Engagement Modes)
- **S7** — Confounds must be explicitly named and tested
- **S8** — Simpson's Paradox: always check segment-level direction after any population finding
- **S9** — On datasets >1M rows, p-value is never sufficient — effect size is the primary criterion
- **S10** — Confound test requires a control procedure: OLS with/without covariates, attenuation percentage, automatic degradation rule
- **S11** — Causal direction: two-step protocol (mechanical plausibility test + conditional Granger test) before action recommendations (→ Engagement Modes)
- **S12** — Detrend before cross-series correlation on multi-year datasets (confounded time trends are the norm)
- **S13** — Silhouette-maximizing k requires η² validation (η² < 0.10 = outlier separation, not segmentation)
- **S14** — Pre-screen clustering features by between/within variance ratio (ratio < 1.0 = exclude before clustering)
- **S15** — Behavioral vs demographic prediction has a temporal horizon (early behavioral ≠ full behavioral)
- **S16** — POPULATION-ONLY dual-component labeling (magnitude vs direction under Simpson's Paradox)

### Temporal Analysis
- **T1** — Seasonality must be detected before any trend claim
- **T2** — Macro event decomposition mandatory when the dataset spans a known structural break
- **T3** — Period comparisons require complete data on both sides
- **T4** — Cumulative vs. rate metrics in temporal analysis
- **T5** — Seasonality scoping: specify four types (weekly, daily, DoW×HoD, ordering cadence) before declaring "not applicable"
- **T6** — Day-of-month normalization: normalize by occurrence count, not uniform denominator
- **T7** — Seasonal promotion structures require period-size validation (verify both promo states coexist within each period)

### Large Dataset Architecture
- **L1** — Move heavy computation to standalone scripts when it would strain notebook execution; notebooks load and display the pre-built results; the criterion is execution weight, not a fixed row threshold
- **L2** — Check available libraries before choosing serialization (default CSV, never assume parquet/feather)
- **L3** — No lambda aggregations on groupbys >1M groups (use built-in aggs only)
- **L4** — If nbconvert fails: check cell-by-cell output (kernel crash = ALL cells empty, different from single error)
- **L5** — Test heavy computation scripts as standalone Python scripts before wiring their calls into notebook cells
- **L6** — State data scale at Stage 1 checkpoint; flag tables above notebook-safe threshold
- **L7** — Large-table profiling recipe: five-step procedure for tables above notebook-safe threshold
- **L8** — Cross-chunk nunique requires set accumulation (chunked groupby nunique silently overcounts)

### Notebook Hygiene
- **N1** — Pandas-first, Python-last (vectorized operations, no iterrows)
- **N2** — Narrative in markdown cells, not print() (two-cell pattern)
- **N3** — Every insight cell: title, confidence, metric basis, evidence, implication, caveat
- **N4** — Quality filter before every cell (the 12-month actionability test)
- **N5** — Autonomous findings must be flagged with trigger reason
- **N6** — Dropped analyses must be documented in exclusion log
- **N7** — Reserved DataFrame names: all DataFrames loaded in setup cell are reserved — never shadow with loop variables
- **N8** — Batch insertion: 3+ cells use single batch script, tracked positions, write once
- **N9** — Re-execute full notebook top-to-bottom after adding cells — state leaks between cells
- **N10** — Cell source lines must end with `\n` except the last line when building programmatically
- **N11** — Actionable non-findings deserve documentation (only when absence of pattern removes a decision lever)

### Narrative Quality
- **NQ1** — "This matters because..." mandatory sentence completing logic from observation to implication
- **NQ2** — "The surprising part is..." mandatory for contrast-based findings before the recommendation
- **NQ3** — All statistical metrics followed by plain-language translation in parentheses
- **NQ4** — Effect size vs. statistical significance must be explicitly distinguished in every test

---

## Generalizable Analytical Patterns

Seven universal statistical methods. **Read `references/industry/statistical-methods.md` for full specifications.**

- **P1** — Subset fingerprinting (overrepresentation ratio + multiple comparison correction)
- **P2** — Cohort-relative scoring (percentile rank within same-age cohort)
- **P3** — Pre/post event split for trend validation
- **P4** — Both-parties-above-average for synergy detection
- **P5** — Three-screen scouting list (quality + undiscoveredness + momentum — all three required)
- **P6** — Commercially significant subset test (retest headline finding on core business subset)
- **P7** — Data-derived segmentation candidates (dual-spine clustering, dimension menus by sector)
- **OR-12** — Feature cross-correlation with Simpson's Paradox detection

---

## Industry Adaptation

**CRITICAL: Do not load all domain files.** The five domain files total ~1,200 lines (~8,000 tokens). Loading all of them when only two are relevant wastes 4,000+ tokens of context that directly degrades the quality of subsequent analysis.

**Procedure:** Read `references/industry/patterns-catalog.md` first — it is the router. Use the Pattern Index Table to identify which named patterns apply based on data available and sector. Use the Engagement Loading Guide (Section B) to determine which domain files to read. **Load only the 2–3 domain files relevant to this engagement.** Do not load scripts during planning stages — load `references/scripts/[domain]/[pattern].py` only when implementing a specific analysis in Stage 4.

Domain files:
- `references/industry/customer-behavior.md` — segmentation, lifecycle, cadence, mission type
- `references/industry/product-catalog.md` — product structure, catalog organization, behavioral signals
- `references/industry/cart-temporal.md` — timing, sequencing, cart dynamics, temporal effects
- `references/industry/operational.md` — operations, inventory, margin, finance
- `references/industry/statistical-methods.md` — universal cross-cutting methods (P1-P6, OR-12)

### The Pattern Catalog Is a Floor, Not a Ceiling

The patterns in this catalog represent the analytical moves that have been validated across prior engagements. They are the minimum — a guarantee that these analyses will be considered for any dataset where the data requirements are met. They are not the maximum.

Every dataset contains structure that no prior engagement has seen. The most valuable findings in any analysis are almost always the ones that were not anticipated before touching the data. The catalog exists so that Claude Code does not miss the obvious — not so that it stops at the familiar.

During Stage 4b, treat the catalog as a source of inspiration and analogy, not as a checklist. The question is never "which catalog pattern applies here?" The question is "what does this specific data reveal that would surprise a client who knows their business?"

When Stage 4b produces a finding that cannot be explained by any existing catalog pattern, that finding is a candidate for a new pattern. Flag it explicitly with the tag [SKILL-CANDIDATE] in the notebook markdown and include it in the Stage 6 learning harvest.

---

## Notebook Technical Standards

- **Pandas-first**: All data operations use vectorized methods. No iterrows(), no itertuples() for analysis.
- **Two-cell pattern**: Every insight = markdown narrative cell + code output cell. No print() for narrative.
- **Plotly for visuals**: Stage 5 outputs use Plotly exclusively. Stage 4 can use matplotlib for quick exploration.
- **Seven-element insights**: what it shows, why this metric, key finding, business implication, concrete example, confidence verdict, key caveat. (→ N3)
- **Exclusion log**: End of Stage 4 notebook lists every dropped analysis with one-line reason.
- **Variable safety**: All DataFrames loaded in setup cell are reserved names. Use abbreviated loop iterators (`vol`, `cnt`, `n`, `rr` — never `orders`, `products`, `users`).
- **Batch cell insertion**: When inserting 3+ cells into an existing notebook, use a single batch script building all cells as a list at tracked positions. Never sequential individual insertions.
- **Post-insertion execution**: Always re-execute full notebook top-to-bottom after adding cells.
- **Cell source encoding**: When building cells programmatically, split source on `\n`, add `\n` to all lines except the last.

### Cell Source Helper Pattern
```python
lines = source.split('\n')
cell["source"] = [l + '\n' for l in lines[:-1]] + [lines[-1]]
```

### Variable Shadowing Check (run before every notebook execution)
```python
import json
with open('notebook.ipynb') as f:
    nb = json.load(f)
setup_src = ''.join(nb['cells'][SETUP_CELL_INDEX]['source'])
reserved = re.findall(r'^(\w+)\s*=\s*pd\.read_csv', setup_src, re.MULTILINE)
# Scan all code cells for loop variables matching reserved names
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        for var in reserved:
            if re.search(rf'for\s+.*\b{var}\b.*\s+in\s+', ''.join(cell['source'])):
                print(f"WARNING: '{var}' used as loop variable — will shadow setup DataFrame")
```

---

## Running Notes Protocol — Incremental Learning Capture

Every engagement produces observations that should feed back into this skill. Rather than relying on end-of-project recall (Stage 6), capture observations incrementally in a running notes file throughout the engagement.

### File Location and Lifecycle

- **Path:** `$PROJECT_ROOT/other/skill_notes.md`
- **Created at:** Stage 1, as the final step before the checkpoint confirmation
- **Updated at:** End of every subsequent stage (2–5), before the checkpoint confirmation
- **Consumed at:** Stage 6a as the primary input to the Learning Harvest

### What Qualifies for the Notes File

An observation belongs in the notes file if it passes this threshold test:

> **"Would a fresh Claude Code instance running this skill on a different dataset tomorrow benefit from knowing this? If yes, include it. If not, leave it out."**

Specific qualifying categories:
- A skill rule that didn't work as documented
- A pattern the skill doesn't cover that would have been useful
- A rule that fired incorrectly and needs scoping
- An ambiguity that required a judgment call not covered by the skill
- A generalizable pattern that emerged from the data

### What Does NOT Qualify

- Tooling warnings and environment noise (nbformat warnings, pip version notices)
- Dataset-specific domain knowledge that won't transfer to other engagements
- Things the skill already handles correctly — no need to confirm what works
- Execution details with no generalizable lesson

### File Format

```markdown
# EDA Skill — Running Notes ([Project Name])

## Stage 1 — Data Source Inventory
**Date:** YYYY-MM-DD
- [Observation with enough context to be actionable in Stage 6]

## Stage 2 — Data Quality & Preparation
**Date:** YYYY-MM-DD
- [Observations]

## Stage 3 — Research Brief & Hypothesis Floor
**Date:** YYYY-MM-DD
- [Observations]

## Stage 4a — Foundational Frequency Analysis
**Date:** YYYY-MM-DD
- [Observations]

## Stage 4a-V — Validation Gate
**Date:** YYYY-MM-DD
- [Observations]

## Stage 4b — Autonomous Exploration
**Date:** YYYY-MM-DD
- [Observations]

## Stage 4c — Formal Hypothesis Testing
**Date:** YYYY-MM-DD
- [Observations]

## Stage 4d — Confidence Audit
**Date:** YYYY-MM-DD
- [Observations]

## Stage 5 — Dashboard-Ready Notebook
**Date:** YYYY-MM-DD
- [Observations]

## Stage 6 — Skill Update
*(this file is a primary input to Stage 6)*
```

### Observation Quality Standard

Each observation should include:
1. **What happened** — the specific situation that triggered the note
2. **Why it matters** — the generalizable principle, not the dataset-specific detail
3. **What the skill should say** — a concrete proposal (new rule, scoped rule, new checklist item)

A note that says "onpromotion was null before April 2014" is dataset-specific and does not qualify. A note that says "mid-dataset schema introductions are a distinct exceptional structure the skill should list, because they create analysis windows that differ from random missingness" is generalizable and qualifies.

---

## What This Skill Does NOT Cover

- Dashboard application construction (Dash layouts, callbacks, CSS, app.py) — for deployed Dash applications, see the `eda-dashboarding` skill which picks up where Stage 5 leaves off
- Visualization styling beyond basic Plotly chart assets
- Hardcoded industry assumptions — adapt via Stage 3 research
- Machine learning model training (though feature engineering and EDA for ML inputs are in scope)
