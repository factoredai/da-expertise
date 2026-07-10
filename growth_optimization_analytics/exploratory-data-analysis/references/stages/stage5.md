## Stage 5 — Dashboard-Ready Notebook

**Goal:** Second notebook with confirmed/qualified findings reformatted as Plotly visual assets for future dashboard construction.

### Pre-Flight Checks (Before any code is written)

0. **Create dashboard/ subfolder** inside the project folder before writing any Dash files. This folder did not exist during Stages 1–4.
1. **Confirm client narrative language** — The user specifies the target language for chart narratives. Every chart must include both an English technical summary and a client-language narrative card if dual language is required.
2. **Confirm FRAGILE exclusions** — List all FRAGILE findings being excluded from this notebook.
3. **Confirm POPULATION-ONLY treatment** — List all Simpson's Paradox findings that need segmented visualization.
4. **Finding-to-Chart Mapping Table** — Before writing any visualization code, construct a mapping table covering every non-FRAGILE finding from the Stage 4d audit. Present this table to the user for confirmation before proceeding.

   | Column | Description |
   |--------|-------------|
   | Finding ID | ID from Stage 4d audit (e.g., H1, H2, B1-H1, 4a-3) |
   | Finding Tier | A / B / C (from Stage 4d audit) |
   | Finding Name | One-line description |
   | Confidence Label | HIGH / QUALIFIED / POPULATION-ONLY |
   | Planned Chart ID | V1, V2, ... (sequential) |
   | Chart Type | Bar, scatter, heatmap, dual-subplot, etc. |
   | Business Question | The question this chart answers for the decision-maker |
   | Concrete Example | A specific instance illustrating the finding |
   | Segmentation Lens | Official / Data-Derived / Both / N/A |
   | Raw Data Flag | Yes/No — whether chart requires pre-computing from raw data above notebook-safe threshold (→ L1) |

   FRAGILE findings appear in a separate **Excluded** section at the bottom of the table with the exclusion reason from Stage 4d.

   Every non-FRAGILE finding from Stage 4d must appear either as a chart in the mapping or in the Excluded section with a one-line reason. No finding may be silently omitted.

   The segmentation comparison itself — official vs. data-derived variance explained — is a chartable finding (typically as a grouped bar chart showing eta² for each grouping across multiple dependent variables).

   **Plotly technical note:** Avoid `add_vrect`/`add_hrect` with `annotation_text` on non-numeric axes — Plotly's internal `_mean()` will fail on string values. Use `add_annotation` with explicit coordinates instead.

   The mapping must be confirmed by the user before any visualization code is written. This prevents both omissions (findings that were audited but never charted) and wasted work on charts that don't survive review.

### Batch Protocol (→ Context Preservation)

**Batch size:** 6–8 charts per pass. POPULATION-ONLY charts always in their own **final** batch, isolated from all other charts. Order charts from simplest (Tier C descriptive) to most complex (Tier A strategic). Group by thematic section from the Stage 4d audit where possible.

**Self-interruption:** After each batch of charts, stop and present the batch summary before continuing. This is the stage with the highest observed template simplification risk — in the Favorita engagement, 13 of 14 charts lost 3 of 7 required narrative elements.

**Structural self-check (per chart, before moving to the next — this is the most critical self-check in the pipeline):**
- [ ] **What it shows** — one sentence, no jargon
- [ ] **Why this metric was chosen** — analytical justification
- [ ] **Key finding** — the specific number, in plain language
- [ ] **Business implication** — what should the reader do
- [ ] **Concrete example** — a named product, store, city, or numeric value from the data
- [ ] **Confidence level** — with plain-language justification
- [ ] **Caveat** — the reader must know this before acting

If any of the 7 elements is missing from the current chart's narrative card, fix it before writing the next chart. This per-chart check is the single most important compliance mechanism in the entire skill.

### For each confirmed or qualified insight from Stage 4:

**Visualization:**
- Recreate using Plotly (not matplotlib)
- Style consistently: clean background, legible fonts, hover templates, company palette if provided
- Each visualization: one chart per cell, fully self-contained
- Title every axis with `title_standoff=25` for readability

**Card Narrative** (markdown cell paired with each chart):
1. What the chart shows (one sentence, no jargon)
2. Why this metric was chosen (analytical justification)
3. Key finding in plain language with the specific number
4. Business implication: what should the reader do
5. Concrete example — a named product, store, city, or numeric value from the data
6. Confidence level with plain-language justification
7. Caveat the reader must know before acting

**Standard-mode caveat propagation:** Before writing any chart narrative, read the mode-dependent gate log in `stage4c_verdicts.md`. For any finding where S11 was skipped, the Caveat element of the card narrative must include: "Causal direction was not formally tested — the assumed direction has not been verified." For any Tier A ranking where S6 was skipped, the Caveat element must include: "Ranking position stability was not assessed — entity ordering reflects current data only."

### Narrative Depth Graduation by Confidence Tier

**Mode-conditional:** In Standard mode, all HIGH findings receive a single narrative depth — use the "HIGH (single confirmation)" row for all HIGH findings regardless of convergent evidence count. In Deep mode, graduated depth applies in full.

| Tier | Bullet Points | Special Requirements |
|------|--------------|---------------------|
| **HIGH** (3+ convergent confirmations) | 4-5 bullets | Full confidence justification + caveat *(Deep mode only)* |
| **HIGH** (single confirmation) | 3-4 bullets | Standard treatment |
| **QUALIFIED** | 3 bullets | Limitation stated prominently |
| **POPULATION-ONLY** | Full structure + framing paragraph | See rules below |

### POPULATION-ONLY Visualization Rules

These findings must follow strict rendering rules:

1. **Render as segmented charts** showing the reversal — never as a single population chart with a badge
2. The population aggregate may appear **only as a reference line**, never as the primary element
3. Chart title must **name the paradox explicitly** (e.g., "Repertoire Paradox — Population Trend Reverses Within Segments")
4. Caption must contain a plain-language warning: "Acting on the population average would harm [N] of [M] segments"
5. **Always in their own final batch** (per Batch Protocol above), isolated from all other charts
6. **Include a temporal dimension within each segment panel** when the finding has a time-series component. Trajectory within segments often reveals dynamics invisible in a static cross-section (e.g., fading lift, deepening destruction, accelerating divergence). If the finding is cross-sectional only, this rule does not apply.

### Large Dataset Charts (→ L1)

If any chart requires reading raw data above the notebook-safe threshold:
- Pre-compute the aggregates in a standalone script
- The notebook cell loads only the pre-computed CSV
- Exception: if the computation is simple (one groupby, one filter), inline is acceptable

### Required Output
- Dashboard-ready notebook (separate file from Stage 4)
- One Plotly chart + one narrative markdown per insight
- Chart inventory table: chart ID, title, insight source, confidence level, suggested dashboard section

### Canonical Output

After completing all Stage 5 chart and narrative work, write `$PROJECT_ROOT/other/stage5_chart_manifest.md`. This is the Stage 5 canonical output per SKILL.md Rule 7 — the session-portable record of the final deliverable map. The notebook remains the analyst's full working interface and the primary review surface.

`other/stage5_chart_manifest.md` must contain:
- **Declared engagement mode** — Standard or Deep (from `stage1_catalog.md`); note any findings in the manifest where Standard-mode caveats (unverified causal direction, untested ranking stability) appear in the chart narrative
- **Chart manifest** — one entry per produced chart with: chart ID (V1, V2, ...), finding ID (from Stage 4d audit), finding name, confidence label (HIGH / QUALIFIED / POPULATION-ONLY), chart type, chart file path, and one-line narrative summary
- **FRAGILE exclusion log** — all findings excluded from Stage 5 with the exclusion reason from Stage 4d
- **POPULATION-ONLY summary** — the list of POPULATION-ONLY findings and the segmented treatment applied to each

Write the file as structured markdown: one section per content area above, suitable for direct reading without executing any code.

### Running Notes Update

Before the checkpoint confirmation, append the completed Stage 5 section to `$PROJECT_ROOT/other/skill_notes.md` with the current date and any qualifying observations. Apply the threshold test and qualifying criteria from SKILL.md § Running Notes Protocol. If no observations qualify, write "No qualifying observations."

### CHECKPOINT — DO NOT PROCEED TO STAGE 6 WITHOUT USER CONFIRMATION
> "Stage 5 complete. [N] dashboard-ready charts produced from [M] confirmed/qualified findings. [K] FRAGILE findings excluded. [J] POPULATION-ONLY findings rendered with segmented treatment. Canonical output written to `other/stage5_chart_manifest.md` — please review the chart manifest alongside the notebook before confirming. Ready to proceed to Stage 6?"

**Mid-Flow Mode Adjustment:** At this stage the analytical record is fixed — no new gate runs are possible. Before confirming, assess whether the final chart set reveals any pattern — findings carrying Standard-mode caveats that appear more consequential in visualization than in the audit, or a concentration of QUALIFIED labels across related charts — that suggests Stage 6 should pay special attention or flag a specific depth upgrade for the next engagement. Surface the observation here so it enters the Stage 6 learning harvest. See SKILL.md § Engagement Modes — Standard and Deep.
