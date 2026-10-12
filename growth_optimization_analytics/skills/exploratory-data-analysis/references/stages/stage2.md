## Stage 2 — Data Quality and Preparation

**Goal:** Identify and treat every data quality issue. Document every decision. Nothing is silently dropped or modified.

### 2.1 Temporal Integrity (if date/time columns exist)

- Detect and validate all date/datetime columns
- Check format consistency, future dates, historical anomalies
- Identify time series gaps and duplicate timestamps
- Detect business calendar patterns (weekday/weekend, holiday effects)
- If the dataset spans a known structural break (policy change, system migration, pricing regime shift, major operational event), flag for decomposition before trend analysis (→ T2)
- Rules: never compute trend without seasonality check (→ T1); never compare periods without verifying completeness (→ T3)
- After detecting date gaps, classify each as a **business-closure gap** (aligns with known non-operating days such as national holidays or seasonal closures — document and move on) or a **data-collection gap** (unexpected absence requiring investigation in Stage 2)

#### Seasonality Scoping Rule (→ T5)

**Never** make a blanket statement that "seasonality analysis is not possible." Instead, specify exactly which types of seasonality the available fields support:

| Seasonality Type | Required Fields | Analysis |
|-----------------|----------------|----------|
| **Weekly** | `day_of_week` or any DOW field | Day-of-week distribution, weekday vs. weekend comparisons |
| **Daily (intra-day)** | `hour_of_day` or timestamp | Hourly volume patterns, morning vs. evening behavior |
| **Weekly × Daily interaction** | Both DOW and HOD | Full 7×24 heatmap — richer than either alone. **Must be explicitly named as a third type.** |
| **Ordering cadence** | `days_since_prior` or inter-event intervals | Individual cycle detection, cadence segmentation |
| **Monthly / Annual** | Calendar dates (month, year) | Traditional seasonal decomposition |

Replace any blanket "seasonality not applicable" with this four-type breakdown specifying what IS and IS NOT possible.

### 2.2 Missing Values
For every column with missing values:
- Count and percentage missing
- Classify: MCAR, systematic, or structural (→ Q5)
- Test whether missingness correlates with outcome variable
- Document treatment: drop, impute, flag, or leave as-is
- Flag any column with >20% missing as HIGH RISK

### 2.3 Sentinel Values (→ Q3)
- Scan all numeric columns for suspicious extreme frequencies at distribution extremes
- Common sentinels: 99999, 0, -1, 9999.99, extreme integers
- Validate whether real or system flags
- Replace confirmed sentinels with NaN and document

### 2.4 Outlier Treatment
- Before applying the IQR method, examine the distribution shape — histogram and basic descriptive statistics. If the distribution is visibly heavy-tailed (a long right tail with the mean substantially above the median), the IQR fence will flag a large fraction of legitimate values as outliers. In this case, report the IQR results descriptively as context but default to keeping all values and using median-based metrics downstream. The IQR method assumes approximate symmetry and breaks down on distributions where the tail is the business.
- **Investigate before removing** — genuine extreme values (B2B bulk orders, seasonal spikes) must not be removed as errors
- Document treatment with business rationale for each decision

### 2.5 Legacy and Regional Data Specifics (→ Q6)
- **Encoding:** detect and fix Latin-1/Windows-1252/UTF-8 issues
- **Dates:** standardize all format variants within the same column
- **Numerics:** remove currency symbols, fix separator conventions
- **Codes:** check for tax-ID or barcode truncation and leading-zero loss when numeric identifiers are stored as floats
- **Branches:** check for schema inconsistency across locations or time periods
- **Text:** strip spaces, normalize case, deduplicate string variants

### 2.6 Join Construction (if multiple tables)
- Build all joins from Stage 1 relationship map
- Report final join yield after cleaning
- If below 90% after cleaning: investigate reason and report
- Document excluded records and the analytical impact of their exclusion
- For reference tables with geographic or entity-level scoping (e.g., regional holidays, zone-specific pricing), verify the join resolves to the correct entity subset. Before any geographic join, enumerate all distinct values on both sides, compare explicitly, and resolve mismatches with a manual mapping table. A date-level join that ignores scope will over-assign events to entities that are not affected.

### 2.7 Field Validation (→ Q1, Q4)
When multiple measures of the same underlying activity exist in the dataset (e.g., unit sales and transaction counts both measuring store-day activity), cross-validate them before any downstream analysis. A strong positive correlation confirms both signals are consistent. A weak or negative correlation indicates a data quality issue or a misunderstanding of field semantics that must be resolved before proceeding.

For any field used as a key metric or segmentation variable:
- Cross-validate against at least one independent signal
- If a claimed scale contains out-of-range values: investigate before using
- If a binary flag is used as a filter: estimate the dominant error rate and direction

### 2.8 Descriptive Statistics
For every numeric field in the cleaned dataset:
- Mean, median, std, min, max, P25, P75, P90
- Distribution shape assessment (normal, skewed, bimodal, heavy-tailed)
- Flag significant mean/median divergence as skew indicator

### 2.9 Data-Derived Segmentation Candidates

**Separate prompt (→ Context Preservation).** This sub-stage is conceptually distinct from the quality audit (2.1–2.8) and can produce substantial analytical output (clustering for every spine dimension). It should run as its own prompt after 2.1–2.8 are confirmed, not as a continuation of the same execution block.

**Goal:** For every categorical dimension in the segmentation spine (identified at Stage 1), derive an alternative data-driven grouping and compare it against the official classification. Both the official and the data-derived groupings enter the spine as a dual pair.

**Why this runs in Stage 2:** Clustering requires clean data (post-2.1 through 2.8) and produces groupings that feed into the segmentation spine before Stage 3 hypothesis design. If data-derived groupings are discovered later (e.g., Stage 4), any superior grouping would force a backwards pass through all prior analysis under new segments — a process failure. The cost of running clustering in Stage 2 is low; the cost of discovering a better segmentation late is high.

#### Step 1 — Identify Clustering Candidates

For each categorical dimension in the Stage 1 segmentation spine (store type, product category, customer tier, etc.), determine whether a data-derived alternative is feasible:

- The dimension must have at least 10 entities (stores, products, customers) to support meaningful clustering.
- There must be at least 2 behavioral variables available to cluster on — clustering on a single variable reduces to sorting, which is not a grouping.
- If the dimension is purely geographic (city, state) with no behavioral data attached, clustering is not applicable — geographic splits are used as-is.

Document which dimensions proceed to clustering and which are excluded with a one-line reason.

#### Step 2 — Select Dimensions and Method

**Dimension selection:** Choose 2–4 input variables that the client already understands or can immediately grasp. The dimensions must be business-meaningful — a cluster defined by interpretable features ("high-weekend-traffic, low-weekday stores") is a deliverable; a cluster defined by abstract principal components is not.

Typical dimension menus by entity type (these are starting points — floors, not ceilings):

**Store clustering:**
- Volume level (total units or transactions per period)
- Temporal shape (weekend-to-weekday ratio, start-of-month index, seasonal amplitude)
- Assortment profile (share of top product family, perishable share, promotional intensity)
- Geography proxy (if not already a spine dimension)

**Product clustering:**
- Velocity (units per selling-day)
- Demand regularity (coefficient of variation across periods, selling-day coverage)
- Promotional responsiveness (on-promo vs. off-promo lift)
- Category role (share of store-level volume when present)

**Customer clustering (when customer IDs exist):**
- Frequency (visits per period)
- Recency (days since last visit)
- Basket profile (average basket size, category breadth per visit)
- Value trajectory (trending up, stable, trending down)

**Time-period clustering:**
- Volume level (total daily/weekly sales)
- Composition (product mix shift from baseline)
- External signals (holiday, event, macro indicator value)

**Method selection framework:** The clustering method must be appropriate to the entity and dimensions being clustered. No single method is prescribed.

| Data Characteristics | Recommended Approaches |
|---------------------|----------------------|
| Small entity count (<50), few dimensions (2–3) | Visual inspection of scatter/heatmap first. If structure is visible, k-means or hierarchical clustering. |
| Medium entity count (50–500), mixed types | k-means on standardized continuous variables. If categorical variables are important, k-prototypes or hierarchical with Gower distance. |
| Large entity count (>500), continuous variables | k-means or Gaussian Mixture Models. Consider mini-batch k-means for speed. |
| Time-series profiles (DOW shapes, seasonal curves) | Distance-based clustering with DTW or shape-based features (amplitude, phase, trend), then hierarchical or k-medoids. |
| Binary/sparse features | Hierarchical clustering with Jaccard distance. |

#### Step 3 — Determine Cluster Count

The number of clusters must be data-derived, not fixed. Require explicit justification for k:

- **Silhouette analysis:** Compute mean silhouette score for k = 2 through min(k_max, entity_count / 5). Select the k that maximizes silhouette, subject to the interpretability gate.
- **Elbow method:** Plot within-cluster sum of squares vs. k. Identify the elbow point.
- **Domain constraint:** In most business contexts, k should be between 3 and 8. Fewer than 3 is unlikely to capture meaningful heterogeneity. More than 8 is unlikely to be operationally actionable — a manager cannot differentiate 12 store types.
- If silhouette and elbow disagree, prefer the lower k that is still interpretable.

#### Step 4 — Interpretability Gate (Hard Gate)

**Every cluster must be nameable in business language.** After clustering, examine the centroid profile of each cluster and assign a descriptive name based on its distinguishing characteristics. If a cluster cannot be named — if its centroid does not have a clear, distinguishing feature that differentiates it from adjacent clusters — merge it with its nearest neighbor and re-run.

The naming convention is: `[distinguishing feature] [entity type]`. Examples: "Weekend-heavy stores," "High-velocity staples," "Monthly stock-up customers," "Holiday-spike periods." The name must be understandable by a business owner with no data background.

Document the cluster names, their centroid profiles, and the business rationale for each name in the notebook. A cluster labeled "Cluster 3" is not a valid deliverable.

#### Step 5 — Compare Against Official Segmentation

For every dimension where an official categorical variable exists (store type, product category, customer tier, etc.), compare variance explained between the official grouping and the data-derived grouping:

- **Metric:** Use eta-squared (from Kruskal-Wallis) or R-squared (from ANOVA) on the primary business metric for that entity type (e.g., daily transactions for stores, daily velocity for products).
- **Test against multiple dependent variables:** A segmentation variable that explains traffic may not explain assortment mix (→ Segmentation Variable Evaluation in SKILL.md). Test both groupings against at least 2 dependent variables.
- **Report both.** The data-derived grouping does not replace the official one. Both enter the spine. The comparison itself — the gap in explanatory power — is part of the deliverable.
- **If the data-derived grouping explains substantially more variance:** Document this as a finding. It means the official segmentation is missing behavioral structure that the data captures. This is a high-value consulting deliverable regardless of whether the official segmentation is weak.
- **If the official grouping explains equal or more variance:** The official segmentation is empirically validated. Document this positive result — confirming that the client's existing framework works is also valuable.

#### Step 6 — Construct the Dual Spine

The output of 2.9 is a **dual segmentation spine** for every dimension where a data-derived grouping was produced:

| Dimension | Official Variable | Data-Derived Variable | Official eta² | Data-Derived eta² |
|-----------|------------------|----------------------|--------------|-------------------|
| Store | store_type (A–E) | store_cluster_derived (k=4) | — | — |
| Product | family (33 categories) | product_cluster_derived (k=5) | — | — |

Both columns travel through Stages 3–5. When the skill specifies "split by segmentation spine dimension," both the official and data-derived groupings are tested. If they tell the same story, report once. If they diverge, both are reported — the divergence itself is a finding.

**Efficiency rule for downstream stages:** Both groupings are tested at every segmentation checkpoint, but the narrative expands only when they diverge. If both groupings tell the same story for a finding, report the finding once with a one-sentence note: 'Segment status is Uniform under both official and data-derived groupings.' If they diverge, both results are reported in full — the divergence is itself a finding.

**Pre-existing cluster variables:** If the dataset already contains a cluster variable (as in the Favorita dataset's `cluster` field with 17 values), it is treated as a third grouping alongside the official categorization and the data-derived clustering. It does not substitute for either — its provenance is unknown, and its relationship to the other groupings must be tested empirically, not assumed.

### 2.10 Constraint Register (Mandatory)

The constraint register is a structured artifact — a CSV file at `$PROJECT_ROOT/data/constraint_register.csv` — that captures every data limitation discovered during Stages 1–2 in a format that downstream stages can mechanically iterate over. It travels forward as a mandatory input to Stages 3, 4a, 4a-V, 4b, and 4c.

**Why a structured artifact, not prose:** Prose quality findings are read once and deprioritized under context pressure. A CSV table can be loaded in a notebook setup cell and iterated over programmatically — each finding must acknowledge each applicable register row, making omissions visible.

#### Schema

```csv
constraint_id,constraint_type,table_name,column_or_key,affected_rows,share_of_total,bias_direction,affected_analyses,notes
```

**Fields:**
- `constraint_id`: Short unique identifier (e.g., `POP-1`, `DOM-1`, `REF-1`, `TEMP-1`, `FIELD-1`, `OVERLAP-1`, `SCOPE-1`)
- `constraint_type`: One of the eight types below
- `table_name`: Which fact or dimension table is affected
- `column_or_key`: The specific column, key, or dimension involved
- `affected_rows`: Count of affected rows (integer)
- `share_of_total`: Fraction of the table's rows affected (decimal, e.g., 0.776)
- `bias_direction`: Plain-language description of how this constraint distorts results if ignored
- `affected_analyses`: Comma-separated list of analysis types affected (e.g., "basket analysis, customer segmentation, order-level aggregations")
- `notes`: Additional context — asymmetries, known workarounds, cross-references to other constraints

#### Constraint Types

**1. FLAGGED_POPULATION** — Rows that belong to a systematically non-representative population identified in §2.3 (sentinels, placeholders, return-only records, test accounts). These rows are in the data but should not be treated as equivalent to the general population.

**2. DOMINANT_ENTITY** — An entity whose volume share is visibly disproportionate relative to other entities in the same segmentation dimension — meaning its inclusion could plausibly change aggregate statistics in a materially different direction than the rest of the population. Identified in §1 (segmentation spine) and confirmed in §2. The assessment is qualitative and distribution-relative; no fixed threshold applies. Includes which dependent variables (revenue, margin, quantity) the dominance applies to.

**3. DUAL_SPINE_OVERLAP** — The relationship between an official and data-derived grouping from §2.9. Classified as Independent (adjusted Rand <0.3 or no cluster >60% concentrated), Partially Overlapping (any cluster 60–80% concentrated), or Redundant (any cluster >80% concentrated). Computed during §2.9 Step 5 — the crosstab and adjusted Rand index are produced here, not deferred to 4a-V.

**4. REFERENTIAL_INTEGRITY** — Any join that loses rows: orphaned foreign keys, unmatched master records, ID mismatches, discontinued codes. Includes the loss rate, whether it is symmetric across dimensions (e.g., channel-dependent orphan rates), and the known bias direction (e.g., "orphaned products skew lower-priced").

**5. TEMPORAL_INTEGRITY** — Gaps in date coverage, periods with unreliable data, fiscal calendar misalignment, known business closures, mid-period schema introductions (→ Q7). Any period where cross-temporal aggregation is unreliable.

**6. FIELD_RELIABILITY** — Columns that exist but are inconsistently populated, manually entered, encoding-changed mid-period, or have high null rates that compromise aggregation. Distinct from missing values (§2.2) — field reliability covers columns that are *present* but *untrustworthy* for specific uses.

**7. ANALYSIS_SCOPE** — Dimensions or variables that exist only for a subset of the data. This is not a quality issue — it's a structural coverage gap that determines which analyses are testable on which population. Example: customer_key available only for online channel (22.4% of online rows for real customers). Unlike FLAGGED_POPULATION (which marks rows to exclude), ANALYSIS_SCOPE marks analyses that are *impossible* on certain populations.

**8. SCALE_CONSTRAINT** — Tables above the notebook-safe threshold (→ L1, L6) that require standalone script processing. Affects how findings are computed, not what they mean. Recorded so downstream stages know which tables need chunked processing.

**9. CONSTRAINT_INTERACTION** — Added during Stage 4a-V Phase 1a when two or more constraints on the same table interact in ways neither individual entry describes. Records the parent constraint_ids, the combined effect, and which analyses are affected by the interaction. Not populated at Stage 2 — it is produced during 4a-V's register completeness review.

#### Construction Rule

The register is built incrementally:
- **Stage 1** contributes: DOMINANT_ENTITY (from segmentation spine outlier detection), SCALE_CONSTRAINT (from scale flags), REFERENTIAL_INTEGRITY (from join yield checks), and TEMPORAL_INTEGRITY (from date range inspection).
- **Stage 2** contributes: FLAGGED_POPULATION (from §2.3 sentinel detection), FIELD_RELIABILITY (from §2.7 field validation), ANALYSIS_SCOPE (from population definition), and DUAL_SPINE_OVERLAP (from §2.9 Step 5).

In practice, the full register is assembled at the end of Stage 2 by consolidating findings from both stages. Entries from Stage 1 may be refined during Stage 2 (e.g., a REFERENTIAL_INTEGRITY entry gains its bias_direction after §2.10 orphaned-key profiling).

#### Downstream Consumption Contract

Every stage from Stage 3 onward must:
1. **Load** the register in its setup/pre-flight step.
2. **Acknowledge** each row — either by referencing it in the relevant finding/hypothesis or by marking it N/A with a one-sentence reason.
3. **Never silently ignore** a register row. If a constraint does not apply to a specific finding, the non-applicability must be stated.

The register is **append-only after Stage 2** — downstream stages may add rows (e.g., a new constraint discovered during 4b exploration) but may not modify or delete existing rows.

### Required Output
- Cells organized per quality dimension (2.1 through 2.10)
- Clean master DataFrame(s) with explicit variable names
- Data quality summary table: column, issue, treatment, records affected
- Dropped fields log with reasons
- Analytical population statement: N records, date range, what is included and excluded
- Dual segmentation spine table (from 2.9)
- **Constraint register CSV** (`$PROJECT_ROOT/data/constraint_register.csv`) with all rows populated per §2.10

### Canonical Output

After completing all Stage 2 work, write `$PROJECT_ROOT/other/stage2_quality_log.md`. This is the Stage 2 canonical output per SKILL.md Rule 7 — the session-portable record Claude Code reads for continuity in later stages. The notebook remains the analyst's full working interface and the primary review surface; `stage2_quality_log.md` is what Claude Code reads to re-establish Stage 2 context without opening the notebook.

`other/stage2_quality_log.md` must contain:
- **Declared engagement mode** — Standard or Deep (from `stage1_catalog.md`); no Stage 2 operations change based on mode, but the mode is carried forward for downstream traceability
- **Quality issues log** — one entry per quality issue treated across §2.1–2.8, with the column affected, the issue type (missingness, sentinel, outlier, encoding, join loss, etc.), the treatment applied, and the records affected
- **Constraint register summary** — the full contents of `$PROJECT_ROOT/data/constraint_register.csv` reproduced in markdown table form, so it is readable without loading the CSV
- **Dual-spine groupings** — the output of §2.9: for each segmentation dimension, the cluster names, centroid profiles, and the eta² comparison between official and data-derived groupings

Write the file as structured markdown: one section per content area above, suitable for direct reading without executing any code.

### Running Notes Update

Before the checkpoint confirmation, append the completed Stage 2 section to `$PROJECT_ROOT/other/skill_notes.md` with the current date and any qualifying observations. Apply the threshold test and qualifying criteria from SKILL.md § Running Notes Protocol. If no observations qualify, write "No qualifying observations."

### Checkpoint
> "Stage 2 complete. Cleaned dataset has [N] records across [date range]. [M] quality issues identified and treated. [K] fields dropped. Constraint register written to `$PROJECT_ROOT/data/constraint_register.csv` with [J] constraint rows. Canonical output written to `other/stage2_quality_log.md` — please review alongside the notebook before confirming. Ready to proceed to Stage 3?"

**Mid-Flow Mode Adjustment:** Before confirming, assess whether anything discovered during Stage 2 — an unusually high density of constraint register entries suggesting complex data quality terrain ahead, or a DUAL_SPINE_OVERLAP result of Independent with large eta² gaps indicating the official segmentation significantly misaligns with the data — materially changes the complexity or depth of later stages relative to the declared mode. If so, surface the specific observation and suggest a targeted depth adjustment for the affected stage(s) (e.g., upgrade 4a-V Phase 2 to full cross-dimensional, or upgrade Stage 4b to all four moves). See SKILL.md § Engagement Modes — Standard and Deep for the asymmetric override rule.
