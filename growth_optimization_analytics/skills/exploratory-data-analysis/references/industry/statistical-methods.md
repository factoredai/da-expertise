# Statistical Methods — Universal Cross-Cutting Patterns

These methods apply across industries and analytical domains. They are techniques, not business analyses — they answer "how to test" rather than "what to test."

---

## OR-12. Feature Cross-Correlation with Simpson's Paradox Detection

**Business problem:** Are there counterintuitive relationships between behavioral features that would produce wrong recommendations at population level?

**Data requirements:** Entity-level behavioral features (reorder rate, order frequency, basket size, product variety, inter-order interval, etc.). User/entity segments.

**Implementation approach:** Build Spearman cross-correlation matrix on all entity-level features. Define domain-expected sign directions for each pair. Flag correlations where observed sign differs from expected. For every flagged correlation, decompose by segment: compute within-segment correlation. If sign reverses in any segment, this is a Simpson's Paradox — the population-level finding is misleading.

**Mandatory rule:** No population-level behavioral correlation may be translated into a recommendation without segment decomposition. POPULATION-ONLY label for any reversed finding.

**Implementation:** see scripts/statistical-methods/or-12-cross-correlation-simpsons.py

**Common mistakes:** Treating unexpected population correlation as inherently valuable without segment decomposition. Assuming counterintuitive findings are insights rather than composition artifacts.

**Confidence labeling:**
- **CONFIRMED Simpson's Paradox:** Within-segment correlation sign reverses in 2+ segments and between-segment composition explains population result.
- **QUALIFIED:** Only one segment reverses.

---

## P1 — Subset Fingerprinting

**Business problem:** What distinguishes a high-performing subset from the full population? Applicable to: top customers, top SKUs, top branches, churned customers.

**Implementation approach:** Define success subset using data-derived threshold (→ M2). For each categorical attribute, compute overrepresentation ratio = (% in success subset) / (% in full population). Ratio >1.0 = overrepresented; <1.0 = underrepresented. Apply Bonferroni correction for number of attributes tested (→ S2). Present only attributes surviving correction. Report both ratio and absolute counts to avoid small-sample artifacts.

**Implementation:** see scripts/statistical-methods/p1-subset-fingerprinting.py

**Common mistakes:** Not applying multiple comparison correction. Small sample sizes in the success subset inflating ratios.

---

## P2 — Cohort-Relative Scoring

**Business problem:** Rank entities by performance within their same-age cohort, removing systematic advantage of older entities.

**Implementation approach:** Define cohorts by time period. Within each cohort, compute percentile rank: (rank_position - 1) / (cohort_size - 1). Result is 0.0 (worst) to 1.0 (best). Cross-cohort comparisons now valid because age bias is removed. Always report cohort size alongside score.

**Implementation:** see scripts/statistical-methods/p2-cohort-relative-scoring.py

**Common mistakes:** Not reporting cohort size. A percentile in a cohort of 5 means less than in a cohort of 500.

---

## P3 — Pre/Post Event Split for Trend Validation

**Business problem:** Is a trend structural or caused by a known event?

**Implementation approach:** Identify structural break date. Fit trend model on pre-event data only, then separately on post-event data. If both show same direction: structural (report both R²). If only post-event: event likely caused it. If pre-event stronger: event may have disrupted existing trend. Essential whenever the dataset spans a known structural break (→ T2).

**Implementation:** see scripts/statistical-methods/p3-pre-post-event-split.py

**Common mistakes:** Not testing pre-event separately. Attributing post-event acceleration to an independent structural shift without checking.

**Baseline growth adjustment:** When using year-over-year comparisons for event impact, first establish the baseline YoY change in the surrounding non-event period. The incremental event lift is the event-period YoY change minus the baseline YoY change — not the raw event-period YoY figure. A raw +118% YoY with a +57% baseline means +61pp incremental lift, not +118%.

**Lagged macro-indicator extension:** When testing a macro indicator (oil price, CPI, exchange rate) against a business metric and the contemporaneous detrended correlation is null, extend to lagged correlations at multiple period lags in both directions. Apply BH-FDR correction across all tests. If no lag survives correction, the null is robust and the indicator can be dismissed. If a specific lag emerges, the relationship is delayed rather than absent — this changes the story materially.

---

## P4 — Both-Parties-Above-Average for Synergy Detection

**Business problem:** Does a combination (supplier-product, salesperson-territory, branch-category) outperform both parties' individual averages?

**Implementation approach:** Compute Party A's average across all partners, Party B's average across all partners, and A+B combination performance. Synergy exists only if A+B > max(A_avg, B_avg) × 1.10 (the 10% premium prevents noise classification). Require minimum 3+ observations. Report conservative premium: min(A+B/A_avg, A+B/B_avg).

**Implementation:** see scripts/statistical-methods/p4-synergy-detection.py

**Common mistakes:** Attributing one party's strength to the partnership. Not requiring minimum sample size.

---

## P5 — Three-Screen Scouting List

**Business problem:** Identify high-potential entities requiring three simultaneous conditions: quality, undiscoveredness, and positive momentum.

**Implementation approach:** Define each screen with data-derived threshold (→ M2): Quality = above median on quality metric; Undiscoveredness = below median on reach metric; Momentum = positive slope on time series with R² ≥ 0.25 (→ S5). Apply all three simultaneously. Bootstrap-test list stability (→ S6). Two-out-of-three entities go in separate "watch list."

**Implementation:** see scripts/statistical-methods/p5-three-screen-scouting.py

**Common mistakes:** Relaxing to two-out-of-three without flagging the fundamentally different risk profile. Not bootstrap-testing stability.

---

## P6 — Commercially Significant Subset Test

**Business problem:** Does a headline finding survive restriction to entities that actually matter commercially?

**Implementation approach:** Define "commercially significant" with business-appropriate threshold (top 80% cumulative revenue, above-median transactions, minimum viable account size). Run full analysis on all data ("Full Population"). Rerun on commercially significant subset ("Core Business"). If both agree: robust. If full shows effect but subset doesn't: tail-driven — demote to FRAGILE. If subset shows stronger: even more actionable. Always report both side by side.

**Implementation:** see scripts/statistical-methods/p6-commercially-significant-subset.py

**Common mistakes:** Not retesting on the core business subset. Accepting findings driven by thousands of micro-entities representing 2% of revenue.

---

## P7 — Data-Derived Segmentation Candidates (Dual-Spine Clustering)

**Business problem:** Official categorical variables (store type, product category, customer tier) may not capture the behavioral structure in the data. Data-derived groupings based on actual behavioral patterns can substantially outperform official classifications — and discovering this is a high-value consulting deliverable.

**Data requirements:** Entity-level behavioral features (at least 2 variables per entity). An official categorical variable to compare against.

**Implementation approach:** For each categorical dimension in the segmentation spine, derive a data-driven clustering and compare variance explained against the official classification. See `references/stages/stage2.md` § 2.9 for the full six-step procedure: identify candidates, select dimensions and method, determine cluster count (data-derived), apply interpretability gate (hard — every cluster must be nameable), compare against official, construct dual spine. Both groupings travel through the rest of the analysis.

**Dimension menus by sector (starting points, not ceilings):**

### Retail / Supermarket / Grocery

**Store clusters — typical dimensions:**
| Dimension | What It Captures | Source |
|-----------|-----------------|--------|
| Volume level (units or transactions per period) | Scale and traffic | Transaction summary |
| Weekend-to-weekday ratio | Shopping mission type (destination vs. convenience) | DOW aggregation |
| Start-of-month sales index | Sensitivity to pay-cycle patterns | DOM aggregation |
| Dominant family share | Assortment character (grocery-centric vs. diversified) | Family × store cross-tab |
| Promotional intensity | Reliance on promotions for traffic | Promo flag aggregation |

**Product clusters — typical dimensions:**
| Dimension | What It Captures | Source |
|-----------|-----------------|--------|
| Velocity (units per selling-day) | Demand level | Item-level aggregation |
| Selling-day coverage (% of operating days with a sale) | Demand regularity vs. intermittency | Item × date cross-tab |
| Promotional lift (on-promo / off-promo ratio) | Promotional responsiveness | Promo comparison |
| Store penetration (% of stores carrying the item) | Distribution breadth | Item × store cross-tab |

**Customer clusters (when IDs exist) — typical dimensions:**
| Dimension | What It Captures | Source |
|-----------|-----------------|--------|
| Visit frequency (per period) | Engagement level | Customer × date |
| Basket size (items or units per visit) | Trip type | Customer × order |
| Category breadth (distinct families per visit) | Mission scope | Customer × family |
| Reorder rate | Habit formation | Customer × item history |

### Wholesale / B2B Distribution

**Customer/Account clusters:**
| Dimension | What It Captures | Source |
|-----------|-----------------|--------|
| Order frequency | Engagement cadence | Account × date |
| Average order value (if $ available) or average line count | Scale of each transaction | Order summary |
| Category concentration (% of spend in top category) | Specialist vs. generalist | Account × category |
| Payment behavior (days to pay, if available) | Financial reliability | Accounts receivable |

**Product clusters:**
| Dimension | What It Captures | Source |
|-----------|-----------------|--------|
| Demand coefficient of variation | Forecastability | Item-level time series |
| Customer penetration (% of accounts ordering) | Breadth of demand | Item × account |
| Average order quantity | Bulk vs. unit purchasing | Order detail |

### Construction Materials / Specialty

**Project-driven demand — typical dimensions:**
| Dimension | What It Captures | Source |
|-----------|-----------------|--------|
| Order lumpiness (max single-order share of total) | Project vs. maintenance demand | Order detail |
| Customer recurrence (repeat purchase rate) | One-time vs. ongoing relationship | Customer × date |
| Seasonal concentration (share in peak quarter) | Seasonal sensitivity | Item × quarter |

**Implementation:** see `scripts/statistical-methods/p7-data-derived-segmentation.py`

**Common mistakes:**
- Using too many dimensions (>4), which makes clusters uninterpretable. Fewer dimensions produce more explainable groupings.
- Accepting clusters that cannot be named in business language. The interpretability gate is not optional — a cluster the client cannot describe to their team is not actionable.
- Fixing k before examining the data. The number of clusters must be justified empirically.
- Treating the data-derived grouping as a replacement for the official classification. Both enter the spine — the comparison itself is the deliverable.
- Clustering on raw features without standardizing. Variables on different scales will dominate by magnitude rather than by explanatory value.
- Not testing stability: re-run the clustering on a temporal split (first half / second half) and check whether entities retain their cluster assignments. Unstable clusters are not reliable segments.

**Confidence labeling:**
- **CONFIRMED** if the data-derived grouping explains meaningfully more variance than the official classification across multiple dependent variables, and clusters are stable across a temporal split (entity retention in same cluster exceeds the majority in both halves).
- **QUALIFIED** if the data-derived grouping explains more variance on one dependent variable but not others, or if stability is marginal.

When the data-derived grouping matches or exceeds the official classification in variance explained, report this as a supporting finding that strengthens the confidence label already assigned to the relevant finding — it does not create a new label. A matching result between official and data-derived groupings increases confidence in an existing HIGH or QUALIFIED label; it does not produce a standalone VALIDATED finding.
