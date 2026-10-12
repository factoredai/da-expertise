## Stage 3 — Research Brief and Three-Tier Hypothesis Floor

**Goal:** Define the guaranteed scope of Stage 4 while enabling full autonomous exploration beyond it.

### 3.1 Boundary Check (Mandatory — before any hypothesis)

Before writing a single hypothesis, establish what the data **can and cannot answer**:

- [ ] **Minimum and maximum of every key dimension** (date range, entity counts, value ranges)
- [ ] **What was filtered before the data arrived** (pre-filtered populations, competition splits, excluded segments)
- [ ] **What questions are impossible** with this data (list explicitly — e.g., "no price data → no revenue analysis")
- [ ] **Right-censored or capped fields** and their impact on analysis
- [ ] **Population definition** — who is in this data and who is not
- [ ] **Zero-demand observations** — if the dataset records only non-zero events (no rows for zero-demand periods), document this explicitly. All averages are over positive-event periods only unless zeros are imputed. This affects demand estimation, intermittent demand classification, and any stockout analysis.

A hypothesis proposed without this check may be untestable. This check prevents wasted analytical effort.

### 3.2 Industry Research

**Read `references/industry/patterns-catalog.md`** — use the Pattern Index Table to identify which named patterns apply to this engagement based on data available and sector. Use the Engagement Loading Guide to determine which domain files to read. Load only the relevant domain files. **Do not load scripts during Stage 3 — they are implementation detail needed only during Stage 4 execution.**

Then search the web for current best practices in data analytics for the specific industry. Cover:
- Standard analytical frameworks for this sector
- Typical KPIs and benchmark ranges
- Common analytical pitfalls specific to the industry
- Relevant recent developments or disruptions

#### Applicability Filter (Mandatory)

For **each** framework found during research, state:
1. Whether the current dataset can support it
2. What is missing (if anything)
3. Verdict: APPLICABLE / PARTIALLY APPLICABLE (with adaptation) / NOT APPLICABLE

Build hypotheses **only** from frameworks that survive the filter. Industry research serves the data structure, not the other way around.

**Coverage note:** Datasets without customer IDs will qualify for a substantially reduced share of the catalog, because most customer-behavior and basket-analysis patterns require individual-level tracking. When customer IDs are absent, shift the analytical center of gravity to product × temporal × geography dimensions and set expectations accordingly before running the full applicability filter.

**Partial customer coverage variant:** When customer IDs exist for less than 50% of total revenue, explicitly split the hypothesis floor into population-level hypotheses (all channels, no customer dimension) and customer-level hypotheses (covered channel only). Document the coverage fraction in every customer-level hypothesis. Downstream stages must not over-weight customer findings relative to their population coverage.

### 3.3 Macro / External Context (Deep mode only)

**Mode-conditional:** In Standard mode, skip this section entirely — do not search for macro data and do not produce a macro data menu. In Deep mode, proceed as below.

Search for current macro data relevant to the industry:
- National statistical office series, industry association indices, sector-specific benchmarks
- CPI by category, regional consumption data
- Present a **menu** of available sources — do not integrate yet

### 3.4 Three-Tier Hypothesis Floor

Hypotheses must be organized into three tiers. **Each tier must be completed before the next is proposed.** Tier 1 is non-negotiable.

#### Tier 1 — What Do We Have? (Descriptive Frequency)

The first 3-5 hypotheses must **always** be Tier 1 descriptive frequency questions that produce ranked lists, bar charts, and percentages a client can act on within a week.

Examples:
- "What are the top 20 products by order volume, and do the top 10% account for >70% of all orders?"
- "What does the distribution of basket sizes look like, and what is the median?"
- "Which departments have the highest reorder rates?"
- "What products should we never be out of stock on?"

**Simple descriptive questions ARE hypotheses — the most important ones.** "What products should we never be out of stock on?" is more actionable than a clustering silhouette score.

**Rule: No Tier 2 or Tier 3 hypotheses may be finalized until at least 3 Tier 1 questions have been answered from the actual data** (in Stage 4a).

#### Tier 2 — How Does It Vary? (Simple Comparisons)

Comparisons across natural splits in the data:
- First-time vs. repeat behavior
- Segment-level splits
- Temporal splits (weekday/weekend, morning/evening)
- High-value vs. low-value entities
- Data-derived grouping vs. official grouping comparisons (does the data-derived segmentation reveal patterns the official one misses?)

#### Tier 3 — What Explains It? (Statistical Testing, Segmentation, Correlation)

Formal hypothesis testing, clustering, regression:
- Significance tests with effect size requirements
- Segmentation with validation metrics
- Correlation with causal interrogation
- Segmentation divergence testing: formal comparison of variance explained by official vs. data-derived groupings across multiple dependent variables (→ P7)

#### Hypothesis Tier → Finding Tier Default Mapping

When findings emerge in Stage 4, they inherit a default finding tier based on their hypothesis tier origin:

- **Tier 1 hypotheses** (descriptive frequency) → **Tier C findings** by default. Elevate to Tier B if they reveal a concentration or pattern extreme enough to drive a business decision.
- **Tier 2 hypotheses** (simple comparisons) → **Tier B findings** by default. Elevate to Tier A if the comparison directly informs a resource allocation or strategic choice.
- **Tier 3 hypotheses** (statistical testing, segmentation, correlation) → **Tier A findings** by default.

This mapping gives a starting point for tier assignment before the data is analyzed. The mapping is a default, not a ceiling — any finding can be elevated based on what the data reveals.

### Hypothesis Template

Every hypothesis at every tier must include:

```
H[N] (Tier [1/2/3]): [Falsifiable claim with specific threshold]
Tests using: [metric(s)]
If confirmed: [business action — what the client does on Monday]
If rejected: [what the rejection tells us about the business]
12-month action: [specific operational change within 12 months]
Segmentation lens: [official / data-derived / both — specify which grouping(s) this hypothesis is tested against]
Population/scope: [which table, which rows included/excluded, and why — forces the scope decision at design time]
```

**If the 12-month action requires further modeling before anyone can act, the hypothesis belongs in Analysis Alternatives, not the hypothesis floor.**

### 3.5 Analysis Alternatives

**Rule:** If the recommendation for an analysis alternative is 'Pursue,' it must be promoted to a full hypothesis in §3.4 with an H-number, tier assignment, and the complete template. §3.5 should contain only deferred or skipped items, plus any hypotheses deferred at the §3.6 hypothesis filtering step (tagged "Deferred at hypothesis filtering — scope limit, not analytical exclusion").

#### Segmentation Divergence Hypotheses

When Stage 2.9 produces data-derived groupings, a standard Tier 2 hypothesis should test whether the data-derived grouping reveals patterns the official classification misses. Template:

```
H[N] (Tier 2): Does the data-derived [entity] grouping explain more variance in [metric] than the official [variable]?
Tests using: eta² comparison (Kruskal-Wallis) on [metric] by official variable vs. data-derived clusters
If confirmed: The official segmentation is missing behavioral structure — use data-derived groupings for [operational decision]
If rejected: The official segmentation is empirically validated — continue using it
12-month action: [Adopt data-derived groupings for specific operational decisions / Confirm official framework]
Segmentation lens: both (this hypothesis IS the comparison)
```

At least one segmentation divergence hypothesis should appear for each dimension where Stage 2.9 produced a data-derived alternative. These are not optional — they are a standard output of the dual-spine process.

Present 3-5 additional analysis directions the data supports but that require a design choice. For each:
- What question it answers
- What data it requires
- What the output looks like
- Your recommendation (pursue / defer / skip, with reasoning)

### 3.6 Hypothesis Filtering

After the full hypothesis floor (§3.4) and all Analysis Alternatives promotion decisions (§3.5) are complete, present the combined pool for analyst selection before Stage 4a begins. This step converts a comprehensive analytical ambition into a scoped execution plan.

**Presentation format:** Group hypotheses by analytical category and surface a one-line potential signal for each — what this hypothesis could reveal if confirmed, in plain language (drawn from the "If confirmed" line of the hypothesis template).

Standard categories: **Temporal** (time patterns, trends, seasonality), **Segmentation** (metric variation across segments or groupings), **Product / Catalog** (performance, basket composition, category roles), **Customer Behavior** (lifecycle, engagement, retention — only if customer IDs exist), **Operational** (efficiency, constraints, supply, margin), **Macro / External** (external factor relationships — Deep mode only, §3.3).

| H-Ref | Category | Hypothesis (one line) | Potential if confirmed | Status |
|-------|----------|----------------------|----------------------|--------|
| H1 | Temporal | [brief description] | [one-line business reveal] | — |
| H2 | Segmentation | ... | ... | Pre-selected (promoted §3.5) |
| ... | | | | |

**Pre-selected:** Any hypothesis promoted to the floor from §3.5 with a "Pursue" recommendation starts as pre-selected. The analyst may still deselect it with a one-line note.

**Soft cap:** Suggest a target of **8 selected hypotheses in Standard mode, 12 in Deep mode** — reflecting the gate execution depth per hypothesis at each mode (Standard skips S11 and S6; Deep runs the full 11-step battery). The analyst may select more than the cap; provide a one-line justification for each hypothesis above it. The cap is a planning target, not a hard limit, consistent with the asymmetric override pattern used elsewhere in the pipeline.

**Wait for analyst selection.** Do not begin Stage 4a until the analyst has confirmed the filtered hypothesis list. Stage 4b may add further hypotheses from autonomous exploration — the filtered list here is the Stage 3 floor, not the final Stage 4c scope.

**Deferred hypotheses** — hypotheses in the pool that the analyst does not select — are documented in §3.5 Analysis Alternatives with the tag "Deferred at hypothesis filtering — scope limit, not analytical exclusion." A deferred-by-scope hypothesis is a candidate for a future engagement; this distinction matters for the Stage 6 learning harvest, where a scope-deferred hypothesis is a different signal than an analytically rejected one.

### Required Output
- Boundary check table
- Industry research summary with applicability filter
- Macro data menu (Deep mode only — skip in Standard mode)
- Three-tier hypothesis floor table
- Analysis alternatives with recommendations
- Hypothesis filtering table with selected and deferred hypotheses
- Explicit confirmation request

### Canonical Output

After completing all Stage 3 work, write `$PROJECT_ROOT/other/stage3_research_brief.md`. This is the Stage 3 canonical output per SKILL.md Rule 7 — the session-portable record Claude Code reads for continuity in later stages. The notebook remains the analyst's full working interface and the primary review surface; `stage3_research_brief.md` is what Claude Code reads to re-establish Stage 3 context without opening the notebook.

`other/stage3_research_brief.md` must contain:
- **Declared engagement mode and filtering parameters** — Standard or Deep (from `stage1_catalog.md`); soft cap applied ([8 / 12]); hypotheses selected: [N] of [M] total; hypotheses deferred at filtering: [K]
- **Selected hypothesis floor** — the Stage 3 floor entering Stage 4b after §3.6 filtering: every selected hypothesis with its full template (H-number, tier, falsifiable claim, tests, actions, 12-month action, segmentation lens, population/scope), including any promoted from §3.5; Stage 4b reads this list to know what has already been scoped and may add further hypotheses before Stage 4c begins
- **Boundary check results** — the complete boundary check table from §3.1 (minimum/maximum dimensions, impossible questions, filtered populations, right-censored fields, population definition, zero-demand documentation)
- **Research context** — the industry research summary with applicability verdicts from §3.2; the macro data menu from §3.3 (Deep mode only — omit section in Standard mode); the analysis alternatives from §3.5 with their recommended dispositions, including any hypotheses tagged "Deferred at hypothesis filtering — scope limit, not analytical exclusion"

Write the file as structured markdown: one section per content area above, suitable for direct reading without executing any code.

### Running Notes Update

Before the checkpoint confirmation, append the completed Stage 3 section to `$PROJECT_ROOT/other/skill_notes.md` with the current date and any qualifying observations. Apply the threshold test and qualifying criteria from SKILL.md § Running Notes Protocol. If no observations qualify, write "No qualifying observations."

### CHECKPOINT — DO NOT PROCEED WITHOUT USER CONFIRMATION
> "Stage 3 complete. Boundary check complete across [N] dimensions. Macro data menu: [produced / skipped — Standard mode]. [M] hypotheses generated: [K] Tier 1, [J] Tier 2, [L] Tier 3. [P] analysis alternatives evaluated ([Q] promoted to the floor, [R] deferred, [S] skipped). Hypothesis filtering: [X] selected for Stage 4c, [Y] deferred to §3.5 (scope limit). Canonical output written to `other/stage3_research_brief.md` — please review the selected hypothesis list alongside the notebook before confirming. **Stage 4a must not begin until the hypothesis floor is explicitly approved.** Ready to proceed to Stage 4a?"

**Mid-Flow Mode Adjustment:** Before confirming, assess whether anything produced during Stage 3 — a hypothesis floor dominated by Tier 3 hypotheses with many anticipated Tier A findings, an industry domain where causal direction is systematically contestable across multiple hypotheses, or a boundary check revealing significant scope limitations that compress the analytical surface — materially changes the depth warranted relative to the declared mode. If so, surface the specific observation and suggest targeted adjustments for the affected stage(s). See SKILL.md § Engagement Modes — Standard and Deep for the asymmetric override rule.
