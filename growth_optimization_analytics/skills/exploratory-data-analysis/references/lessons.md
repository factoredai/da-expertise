# EDA Analytics — Complete Lesson Reference

These lessons encode methodological principles extracted from real analytical work. Each represents a general principle applicable to any industry.

---

## Metric Design

### M1 — No arbitrary composite weights
When building a composite metric (e.g., CommercialScore = 0.75 x A + 0.25 x B), the weights must be justified through theory (demand funnel logic, business priority) AND collinearity testing. If two candidate components correlate above rho=0.85, including both double-counts the same signal. Test explicitly and document the decision. Never assign weights because they "feel right."

### M2 — No arbitrary thresholds
Never define "top performers," "high value," or "significant" using round numbers (top 10, top 15%) unless they are industry standards. Derive thresholds from the data: percentile breaks (P75, P90), natural distribution inflection points (elbow method on sorted values), or documented industry conventions (ABC: 80/15/5 rule). Always state which method was used and why.

### M3 — Cumulative metrics carry age/time bias
Any metric that accumulates over time (total sales, total owners, total transactions) systematically favors older records regardless of current performance. For any such metric used in comparisons, either: (a) normalize by time in market, (b) use cohort-relative ranking (percentile within same-age cohort), or (c) use rate metrics (sales per month) instead of stock metrics (total sales). Document which approach was used and why.

### M4 — Platform and system metrics carry structural bias
Ratings from loyalty apps, reviews on e-commerce platforms, NPS scores, and ERP-generated flags all carry bias introduced by the system itself. Before using any system-generated metric as a proxy for a business reality, validate it against at least one independent signal. If validation fails, demote the metric from primary to contextual.

### M5 — Composite indices must be sensitivity-tested
After building any composite index, recompute it with at least two alternative weighting schemes. If the top-N entities remain stable across all schemes, the index is robust. If the ranking reshuffles significantly, the index is threshold-sensitive and must be presented as a pool (not a ranked list) with that limitation stated explicitly.

---

## Data Quality

### Q1 — Variables that appear to measure X may measure Y
Before using any field, validate its meaning against known ground truth. A field named "language_ease" on a scale of 1-5 that actually contains values up to 1,757 is not a 1-5 scale. A field named "kickstarted" that misses 53% of actual Kickstarter games is not a reliable binary flag. Cross-validate every important field against at least one external reference before building insights on it. If validation fails, the field is either unusable or requires a correction factor.

### Q2 — External datasets require source validation
Any dataset not generated internally (market data, demographic data, regional statistics) must be treated as suspect until its methodology, source, and vintage are confirmed. Signs of synthetic or modeled data: population ratios that appear mathematically generated, no source attribution, round number distributions, implausible uniformity across heterogeneous geographies. If source cannot be confirmed, label findings as DIRECTIONAL ONLY and do not use them for irreversible decisions.

### Q3 — Sentinel values masquerade as real data
Values like 99999, 0, -1, or extreme integers are often used by legacy systems to indicate "not applicable," "unknown," or "not ranked" rather than actual measurements. Before any analysis, scan for values that appear at suspicious frequencies at the extremes of any numeric distribution. Replace confirmed sentinel values with NaN and document the treatment.

### Q4 — Binary flags have error rates that change conclusions
A flag with a high false negative rate means the true effect is larger than measured. A flag with a high false positive rate means the effect is overstated. Always estimate the dominant error direction of any binary flag before interpreting findings that depend on it.

### Q5 — Missing data patterns determine what analysis is valid
Missing completely at random (MCAR) allows most analyses. Systematic missingness (fields missing only for low-volume entities, or for a specific time period) biases results in predictable directions. For every column with >5% missing values, test whether missingness correlates with the outcome variable. If it does, the missing data is informative and must be handled explicitly, not ignored.

### Q6 — String and encoding issues in legacy regional data are the norm
Expect, especially when sourcing from legacy POS and ERP systems: accented characters corrupted by encoding mismatch (Latin-1 / Windows-1252 vs UTF-8), dates as DD/MM/YYYY strings with inconsistent separators, numeric fields with currency symbols, dots as thousands separators and commas as decimal separators (or vice versa), product names with trailing spaces creating false duplicates, and tax ID or code numbers stored as floats losing leading zeros. Treat all of these in Stage 2 before any analysis begins.

### Q7 — Mid-dataset schema introductions
Columns introduced partway through a dataset create structural analysis windows. This is distinct from random or systematic missingness — the field simply did not exist in the source system before a certain date. Identify the exact boundary date by examining the transition from 100% null to populated values. Document which analyses are restricted to the post-introduction period. Do not impute the pre-introduction period — the field was not measured, and imputation would fabricate data. If pandas emits a DtypeWarning during profiling, investigate immediately — it often signals a schema change, sentinel value regime, or encoding inconsistency.

### Q8 — Dominant placeholder entities in dimension tables
Dimension tables may contain catch-all or anonymous entity records (e.g., "Not Provided," "Unknown," "Guest," "Walk-in") that function as high-frequency sentinels in the fact table. These are not outliers in the numeric sense (→ Q3) — they are structurally different entities whose aggregated behavior contaminates order-level, basket-level, and customer-level analyses. Detection: compute the row count per entity in the fact table; any entity contributing >10× the median entity row-count is a placeholder candidate. Treatment: flag with a dedicated boolean column and validate every downstream finding with and without the flagged population. → Cross-reference Q3 (sentinel detection is the numeric complement; Q8 addresses entity-level placeholders).

### Q9 — Return-only rows as a distinct record type
In fact tables that contain both sales and return fields, zero-quantity sales rows may be return records, not data errors. Before flagging zero values as sentinels (→ Q3), cross-reference with return fields. If sales_quantity = 0 AND return_quantity > 0 AND return_amount > 0, classify as a return-only row: exclude from sales volume metrics, include in return-rate calculations. These rows represent a distinct transaction type with a different data-generating process — treating them as errors or sentinels distorts both.

### Q10 — Referential integrity losses must be profiled by segmentation spine
When orphaned foreign keys are detected (join yield < 100%), profile the loss rate by every spine dimension (channel, geography, time, product tier). A flat aggregate orphan rate can mask severe asymmetric bias — e.g., 6% loss in one channel and 23% in another, or stable loss rates across time but concentrated in lower-priced products. Report per-dimension rates and flag any dimension where the orphan rate exceeds 2× the overall average. This profiling should occur in Stage 2 (not deferred to Stage 4) so that hypothesis-level scope decisions in Stage 3 can reference the per-dimension rates. → Cross-reference the constraint register (§2.10) — Q10 feeds the REFERENTIAL_INTEGRITY rows in the register.

---

## Statistical Validity

### S1 — Correlation requires causal interrogation before strategic translation
A rho=0.93 correlation between two variables does not establish which causes which, or whether both are caused by a third variable (confound). Before translating any correlation into a business recommendation, explicitly test: (a) does the relationship survive when controlling for the most plausible confound? (b) is the relationship bidirectional? Use partial correlation, subgroup analysis, or regression residuals. State the causal claim precisely and its confidence level.

### S2 — Multiple comparisons require correction
If you test 30 mechanics, 20 themes, and 15 time periods for significance, you will find "significant" results by chance. Apply Bonferroni correction (divide alpha by number of tests) or Benjamini-Hochberg FDR correction for any analysis that tests multiple hypotheses simultaneously. State explicitly which correction was applied. Findings that do not survive correction are demoted to DIRECTIONAL.

### S3 — Effect size matters as much as significance
A p<0.001 finding with rho=0.03 is statistically real but commercially meaningless. Always report effect size alongside p-values: Cohen's d for means, Spearman rho or Pearson r for correlations, ratio of medians for group comparisons. State in plain language what the effect size means in revenue or operational terms.

### S4 — Findings must survive restriction to the commercially significant subset
A finding that holds across all records but disappears when restricted to records above a minimum commercial threshold (minimum transaction count, minimum revenue contribution) is driven by micro-niche tail behavior, not the core business. Always retest key findings on the commercially significant subset and report both results.

### S5 — Trend lines require R-squared reporting and a minimum R-squared for action
A trend line fitted to a noisy scatter is not a trend. For any trend claim, report R-squared alongside the slope. Establish a minimum R-squared threshold before beginning analysis:
- R² >= 0.25: minimum for directional evidence
- R² >= 0.60: actionable trend
Below the threshold, classify as STABLE or INSUFFICIENT EVIDENCE, not Rising or Declining.

### S6 — Bootstrap stability for rankings and thresholds
Any ranked list that will drive business decisions should be bootstrap-tested: resample the dataset 100-500 times and check what percentage of the top-N entities remain in the top-N across resamples. If stability is below 70%, the ranking is data-noise-sensitive and should be presented as a pool, not an ordered list.

**Operational procedure for Stage 4c:**

For any ranking that appears in a high-impact recommendation (top products to prioritize, top segments to target, catalog configuration to maintain):

1. Define N = size of the top-N that goes into the recommendation.
2. Execute 200 bootstrap resamples (with replacement) of the relevant dataset.
3. In each resample, compute the same ranking and record which entities appear in the top-N.
4. Calculate stability = proportion of resamples in which each entity from the original top-N appears in the resample's top-N.
5. Classification:
   - **Stability ≥ 80%:** robust ranking. Present as an ordered list.
   - **Stability 60–80%:** moderate ranking. Present as a candidate pool with a sensitivity note.
   - **Stability < 60%:** unstable ranking. Do not present as a list. Investigate what is generating the instability before recommending.

**Application gate:** Mandatory for rankings that inform inventory, investment, or prioritization decisions. Not mandatory for purely descriptive rankings (top 20 by volume as context).

### S7 — Confounds must be explicitly named and tested
The most common confounds in business data: entity size (large customers/products look better on everything), time in market (older products accumulate more), geography (branch-level differences confound product-level analysis), channel mix (B2B vs B2C behavior confounds aggregate metrics). Name the most plausible confound for every major finding and test it.

### S8 — Simpson's Paradox detection is mandatory
After every population-level correlation or proportion finding, explicitly check whether the finding holds direction across all primary segments. If it reverses in any segment, the finding is immediately reclassified as POPULATION-ONLY and the population-level recommendation is withdrawn. This is not optional — it is mandatory in every hypothesis test template. The population average can be dangerously misleading when segment composition differs.

### S9 — p-value is insufficient on large datasets
On datasets above 1 million rows, any real effect — no matter how tiny — will achieve statistical significance. p < 0.001 with Cramér's V = 0.02 is statistically real but commercially meaningless. The confidence label must be driven by effect size, not p-value. Report both, but the effect size determines the tier.

### S10 — The confound test requires a control procedure, not just a name

**Problem:** Naming the most plausible confound without formally testing it produces the illusion of rigor without the rigor itself. A finding can survive the mention of a confound and still be entirely explained by it.

**Mandatory procedure for findings that are candidates for HIGH label:**

1. Identify the three most plausible covariates for this finding in this dataset. Use the list of typical confounds from S7 as a starting point. Always include: entity size (volume, frequency), age in the dataset, and the primary segmentation variable if one exists.

2. Run a linear regression (OLS) with the finding's dependent variable as the outcome and the variable of interest plus the three covariates as predictors. Report the coefficient of interest with and without the covariates.

3. Compute attenuation: `(coef_without_controls - coef_with_controls) / coef_without_controls`. Express as a percentage.

4. Automatic degradation rule:
   - **Attenuation < 20%:** confound does not explain the finding. Keep label.
   - **Attenuation 20–50%:** confound explains part of the effect. Degrade from HIGH to QUALIFIED. Document what fraction of the effect survives the control.
   - **Attenuation > 50%:** confound explains the majority of the effect. Degrade to FRAGILE or WITHDRAW depending on the magnitude of the residual effect.

5. If OLS is not appropriate (binary dependent variable, count data), use the equivalent: logistic regression for binary outcomes, Poisson regression for counts, stratified analysis for cases where regression does not converge. Document the substitution with a one-sentence rationale.

**When to apply:** Mandatory for every finding that is a candidate for HIGH before assigning the final label in Stage 4c step 4. Not applicable to pure descriptive findings (Tier 1) where no causal relationship is implied.

**What to report:** A two-row table — coefficient without controls and coefficient with controls — with the attenuation percentage and the resulting label.

### S11 — Causal direction requires a two-step protocol before translation into strategic recommendation

**Problem:** A correlation A→B and a correlation B→A are statistically indistinguishable. Recommending an action based on "A causes B" when the relationship is "B causes A" produces strategies that do not work or actively harm the business.

**Mandatory protocol for findings that translate into action recommendations (not purely descriptive findings):**

**Step 1 — Mechanical plausibility test (always mandatory):**
  Answer these two questions explicitly:
  (a) Does a known mechanism exist by which A could cause B? Describe the mechanism in one sentence.
  (b) Does the same mechanism exist in the reverse direction (B causes A)? Describe that mechanism in one sentence.

  If mechanism exists in only one direction: document as "plausible causality" with the identified direction. Maintain label but add an explicit caveat in the finding narrative.

  If plausible mechanisms exist in both directions: the finding is correlational, not causal. The action recommendation must be framed as an experiment (test whether intervening on A moves B) not as a certainty.

**Step 2 — Granger test (conditional — only if the dataset supports it):**
  Applicable only if: the dataset has time series with at least 20 consecutive periods per entity, and the temporal granularity is sufficient to detect the lag of the proposed mechanism.

  If these conditions are not met: document "Granger test not applicable — insufficient temporal history" and retain the Step 1 result.

  If applied: use the lag suggested by the Step 1 mechanism (if the mechanism operates over weeks, use weekly lag). A Granger result that is significant in one direction and not the other increases confidence in the identified causal direction.

**What to report:** For each finding that generates an action recommendation, include a line: "Causal direction: [A→B / B→A / Bidirectional / Not determinable]" with a one-sentence justification.

### S12 — Detrend before cross-series correlation
For time-series correlations on datasets spanning more than two years, detrend both series before computing the correlation coefficient. Two series with opposite trends will show a strong spurious correlation driven entirely by the time component, not by any genuine relationship between them. If the detrended correlation is not significant, the raw correlation is confounded by time and must not be reported as a finding. When a contemporaneous macro-indicator correlation is null after detrending, extend to lagged correlations at multiple period lags in both directions, applying BH-FDR correction across all tests. If no lag survives correction, the null is robust.

### S13 — Silhouette-maximizing k requires η² validation
After selecting k by silhouette score, verify η² on the primary business metric. If η² < 0.10, the clustering is separating outliers rather than meaningful segments — increase k until η² exceeds 0.10 or conclude that the dimension lacks clusterable structure. The silhouette-optimal solution maximizes within-cluster cohesion, which can be achieved by isolating a few outliers from a homogeneous majority — a mathematically clean but commercially useless segmentation. → Cross-reference S6 (bootstrap stability) for verifying that the cluster assignment is robust after η² is confirmed.

### S14 — Pre-screen clustering features by between/within variance ratio
Before clustering, compute the between-cluster / within-cluster variance ratio for each candidate feature using a preliminary k (e.g., the k from silhouette analysis). Features with ratio < 1.0 contribute more noise than signal — they increase within-cluster variance without improving between-cluster separation. Exclude them and re-run. Silhouette typically improves substantially (sometimes +0.10–0.20) with no loss in η² or business interpretability. The exclusion is safe because a feature with ratio < 1.0 is, by definition, less discriminating than random noise would be. → Cross-reference M1 (no arbitrary composite weights) — variance-ratio pre-screening is the empirical test for whether a feature earns its place in the clustering input.

### S15 — Behavioral vs demographic prediction has a temporal horizon
Full-tenure behavioral features (computed over the entire customer relationship) typically outperform demographics for predicting customer value metrics. However, first-period behavioral features (e.g., first 90 days) may underperform demographics because insufficient behavior has accumulated to differentiate customer types. When designing behavioral-vs-demographic comparisons, specify the behavioral observation window explicitly. "Early behavioral" and "full behavioral" are different predictors with different relationships to demographics. The optimal targeting strategy often uses demographics for initial segmentation (available immediately at acquisition) and behavioral features for ongoing management (available after sufficient history accumulates). → Cross-reference P2 (cohort-relative scoring) — cohort membership defines the behavioral observation window.

### S16 — POPULATION-ONLY dual-component labeling
When a finding has both a magnitude component (the effect size of a metric) and a directional component (whether the effect is positive or negative), and Simpson's Paradox affects the direction but not the magnitude, assign POPULATION-ONLY to the aggregate and label each segment sub-finding independently. The aggregate finding's effect size may be real (e.g., promotions cost 1.3pp margin — true at every level), but the direction of the associated recommendation reverses across segments (e.g., promotions help revenue in one segment, hurt in another). Stage 5 must visualize the segment sub-findings, not the aggregate. Include the aggregate only as a reference line with a "do not act on this" annotation. → Cross-reference S8 (Simpson's Paradox detection).

---

## Temporal Analysis

### T1 — Seasonality must be detected before any trend claim
Never fit a trend line to a time series without first testing for seasonality. A series with strong annual seasonality will show a spurious trend if the start and end points fall at different seasonal phases. Decompose first (trend + seasonality + residual), then interpret the trend component.

### T2 — Macro event decomposition is mandatory when the dataset spans a known structural break
Any time series covering a policy change, system migration, pricing regime shift, major operational event, or any other dated event known to have altered the data-generating process must be split at the event boundary. Test whether findings hold on both sides independently. If a finding only holds on one side, say so. Do not present a pre+post aggregate as if it were a single stable trend.

### T3 — Period-to-period comparisons require complete data on both sides
Never compare Q1 this year to Q1 last year if either period has data gaps. Verify completeness before any YoY or MoM comparison. State explicitly whether the comparison periods are complete.

### T4 — Cumulative vs. rate metrics in temporal analysis
Total sales over a period rewards longer periods. Always complement cumulative metrics with rate metrics (daily average, weekly rate) for any temporal comparison. This is the temporal equivalent of Lesson M3.

### T5 — Seasonality scoping before declaring "not applicable"
Never make a blanket statement that seasonality analysis is not possible. Specify which of four types are supported:

1. **Weekly seasonality** — requires day-of-week field. Always available if DOW exists.
2. **Daily (intra-day) seasonality** — requires hour-of-day or timestamp.
3. **DoW × HoD interaction** — produces a full 7×24 heatmap. Must be explicitly named as a third analysis type, not assumed to follow from the two individual analyses.
4. **Ordering cadence** — requires inter-event interval field (e.g., days_since_prior_order). Supports individual cycle detection and cadence segmentation.

Only monthly and annual seasonality requires absolute calendar dates.

### T6 — Day-of-month normalization
When computing day-of-month aggregates, normalize by the number of occurrences of each day in the dataset. Days 29–31 have fewer occurrences than days 1–28 (not all months have a 31st, February lacks a 29th in non-leap years) and will appear artificially low if raw totals are compared. This is a mechanical artifact, not a behavioral pattern. Always divide by occurrence count before interpreting day-of-month patterns.

### T7 — Seasonal promotion structures require period-size validation
Before computing promotional lift time-series, verify that both promoted and non-promoted transactions coexist within each time period. If promotions are applied to entire periods (e.g., all transactions in a month or quarter are either promoted or not promoted), the lift within that period is undefined — there is no baseline. Use coarser periods (quarterly, semi-annual) that are long enough to contain both promotional states. This validation should happen before any chart design decisions. Seasonal promotion structures are common in retail (regional campaigns run for fixed calendar windows) and will silently produce empty comparison groups at fine granularity. → Cross-reference RW-13 (promotional effectiveness) and RW-22 (promotional saturation diagnostic).

---

## Notebook Quality

### N1 — Pandas-first, Python-last
All data operations must use pandas vectorized methods: `.groupby()`, `.agg()`, `.transform()`, `.query()`, `.merge()`, method chaining. Replace Python loops over rows with `.apply()`, vectorized operations, or `.pipe()`. Exception: matplotlib annotation loops are acceptable as layout operations, not analytical computation. NumPy is acceptable for mathematical operations pandas does not cover natively (Gini, bootstrap, custom distance). Never use `iterrows()` or `itertuples()` for data analysis.

### N2 — Narrative belongs in markdown cells, not print()
Every finding, interpretation, caveat, and business implication must be in a markdown cell. Code cells produce tables, visualizations, or silence (computation only). The two-cell pattern for every insight: Cell 1 = markdown narrative, Cell 2 = code output (table or chart). No `print()` for narrative. No narrative embedded in code comments as the primary communication channel.

### N3 — Every insight cell must contain seven elements
1. **What it shows** — one sentence description (the cell title or opening sentence; specific, not generic)
2. **Why this metric was chosen** (metric basis — analytical justification for the choice)
3. **Key finding** — the specific numbers that support the finding, in plain language
4. **Business implication** (what should the decision-maker do)
5. **Concrete example** — a named product, store, city, or numeric value from the data
6. **Confidence level** with verdict badge and plain-language justification
7. **Key caveat** (what limits or qualifies the finding — the reader must know this before acting)

If any element is missing, the insight is not complete.

### N4 — Quality filter before every cell
Before writing any analytical cell, ask: does this pass the quality filter? "Can a decision-maker act on this finding in the next 12 months?" If no, do not write the cell. A null result or flat distribution is worth one sentence in a summary, not a full visualization.

### N5 — Autonomously discovered insights must be flagged
Any finding not explicitly requested but discovered during analysis must be clearly labelled as **AUTONOMOUS FINDING** and include the specific reason why it was pursued: what pattern in the data triggered the investigation.

### N6 — Dropped analyses must be documented
Every analysis that was attempted and excluded (because it failed the quality filter, was circular, had insufficient data, or was superseded by a stronger finding) must be logged in an exclusion list at the end of the notebook with a one-line reason.

### N7 — Reserved DataFrame names must never be shadowed
All DataFrames loaded in the setup cell are reserved names. Loop variables, comprehension variables, and temporary names must not collide with them. Common dangerous pattern: `for i, (orders, rr) in enumerate(...)` where `orders` overwrites the global DataFrame. Use abbreviated forms for loop iterators: `vol`, `cnt`, `n`, `rr` — never `orders`, `products`, `users`, `segments`, or any other setup-cell name. Run the variable shadowing check (see SKILL.md) before every notebook execution.

### N8 — Batch cell insertion for notebooks
When inserting three or more cells into an existing notebook, use a single batch insertion script that builds all cells as a list at tracked positions, then writes the notebook once. Never use sequential individual cell insertions — they create race conditions, position drift, and cell ID conflicts. Track the insertion position with an incrementing counter.

### N9 — Full re-execution after cell insertion
Always re-execute the full notebook top-to-bottom after adding cells. Never assume individual cell correctness implies notebook correctness. State leaks between cells: a variable defined in cell 5 and overwritten in cell 20 will cause cell 25 to fail silently with wrong data, not with an error.

### N10 — Cell source encoding for programmatic insertion
When building notebook cells programmatically via JSON manipulation, cell source lines must end with newline characters except the last line. Use this helper:
```python
lines = source.split('\n')
cell["source"] = [l + '\n' for l in lines[:-1]] + [lines[-1]]
```

### N11 — Actionable non-findings deserve explicit documentation
When a temporal, geographic, categorical, or operational dimension shows no variation, document it as a non-finding **only when the absence of pattern has a specific business implication that would change a decision**. The filter: "Would a reasonable stakeholder have considered acting on this dimension? If yes, documenting its absence removes a lever from consideration and saves investigation time."

Qualifying examples: uniform channel margins (tells the client not to pursue channel-specific pricing), flat day-of-week patterns (removes DOW-based staffing optimization from the agenda), uniform return rates across categories (category-specific quality programs are not warranted).

Non-qualifying examples: "no correlation between X and Y" where nobody would have acted on that correlation, absence of variation in a dimension not in the hypothesis floor or segmentation spine, or null results from exploratory checks where no specific action was contemplated.

Document qualifying non-findings with the same narrative structure as positive findings: what was tested, what was found (nothing), and what decision this informs. Do not create a narrative cell for non-qualifying non-findings — they belong in the exclusion log with a one-line note.

---

## Narrative Quality

### NQ1 — "This matters because..." is mandatory
Every finding cell must include a sentence starting with "This matters because..." that completes the reasoning chain from observation to business implication in plain language. Not just a conclusion — the full logic chain.

### NQ2 — "The surprising part is..." for contrast-based findings
For findings where significance comes from a contrast rather than an absolute number, a mandatory "The surprising part is..." sentence that names the contrast explicitly before drawing the recommendation.

### NQ3 — Plain-language translations for all statistical metrics
Every statistical metric must be followed by a plain-language translation in parentheses. Example: "Cramér's V = 0.23 (moderate practical effect, comparable to the difference between weekday and weekend shopping patterns)." The translation must reference something the reader already understands.

### NQ4 — Effect size vs. statistical significance must be distinguished
On datasets above one million rows, statistical significance is guaranteed for any real effect. p-value alone is never a valid confidence criterion. Every hypothesis test must explicitly separate effect size (practical significance) from statistical significance and state which is driving the confidence label.

---

## Large Dataset Architecture

### L1 — Tables >5M rows: standalone scripts, not notebook cells
If any table exceeds approximately 5 million rows, heavy transformations — concat, groupby, merge — must be done in a standalone Python script (`build_stage4a_data.py`), not inside the notebook. The notebook is the presentation layer only — it loads pre-built CSVs and runs lightweight validation. This split must be planned from Stage 1 when scale flags are set.

### L2 — Check available libraries before choosing serialization
Default to CSV if uncertain about the environment. Never assume parquet, feather, or HDF5 are installed. If performance requires columnar formats, check `import pyarrow` or `import fastparquet` first and fall back to CSV.

### L3 — No lambda aggregations on large groupbys
Never use lambda aggregations on groupbys with more than one million groups. Use built-in aggregations only: `mean`, `median`, `sum`, `count`, `std`, `min`, `max`. If `mode` or custom logic is needed, compute it separately on a smaller intermediate table.

### L4 — Diagnosing nbconvert execution failures
If `nbconvert --execute` fails, check cell-by-cell output status immediately:
- **ALL cells have no output** = kernel crash (not a single cell error). Look for memory issues, import failures, or segfaults.
- **Some cells have output, one has error** = traceable cell-level bug. Fix that cell.
- **All cells have output but some are wrong** = state leak between cells. Re-read the full notebook flow.

### L5 — Test heavy processing as plain Python scripts first
Before embedding heavy data processing in a notebook, run the same logic as a standalone `.py` script. This isolates memory issues, import problems, and performance bottlenecks from notebook-specific complications (kernel state, cell order, output rendering).

### L6 — State data scale at Stage 1 checkpoint
The Stage 1 checkpoint must explicitly name every table above the notebook-safe threshold (~5M rows) so that Stage 2 can plan the script-vs-notebook split architecture from the start, rather than discovering it through kernel crashes.

### L7 — Large-table profiling recipe for Stage 1 inventory
For tables above the notebook-safe threshold, use a five-step profiling procedure: (1) read the header plus a small row sample for schema detection, (2) count total rows via a single-column chunked read, (3) read the last few rows for end-of-range values, (4) sample a manageable subset for distribution statistics, (5) stream the full file column-by-column for null counts. This produces all statistics required for the field-level catalog without loading the full table into memory. The alternative — attempting `pd.read_csv()` on the full file — will either fail with a memory error or take prohibitively long.

### L8 — Cross-chunk nunique requires set accumulation
Chunked `groupby().nunique()` overcounts because the same entity (e.g., customer, order, product) may appear in multiple chunks. Each chunk's nunique is correct within that chunk, but summing across chunks double-counts entities that span chunk boundaries. For exact nunique, maintain per-group sets (e.g., `defaultdict(set)`) and append entity values from each chunk, then count after all chunks are processed. The overcount is silent — no error is raised — and produces plausible-looking but inflated numbers. This affects any unique-count aggregation (order counts, product breadth, customer counts) on tables processed in chunks per L1.

