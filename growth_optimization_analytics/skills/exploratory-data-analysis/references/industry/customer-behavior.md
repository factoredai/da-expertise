# Customer Behavior and Segmentation Patterns

Domain reference for customer behavior analysis and segmentation. This file contains pattern descriptions only — all executable code lives in the corresponding script files.

---

## Pattern Index

| ID | Pattern | Script |
|----|---------|--------|
| OR-3 | Shopping Mission Type Analysis | `scripts/customer-behavior/or-03-shopping-mission-type.py` |
| OR-4 | Customer Lifecycle Reorder Trajectory | `scripts/customer-behavior/or-04-lifecycle-reorder-trajectory.py` |
| OR-5 | Basket Composition Mode Distribution | `scripts/customer-behavior/or-05-basket-composition-mode.py` |
| OR-6 | Personal Ordering Cadence Distribution | `scripts/customer-behavior/or-06-personal-ordering-cadence.py` |
| OR-15 | Temporal Basket Size Variation | `scripts/customer-behavior/or-15-temporal-basket-variation.py` |
| OR-20 | Segment-Conditional Strategy Matrix | `scripts/customer-behavior/or-20-segment-conditional-strategy.py` |
| RW-3 | B2B/B2C Customer Detection from Ticket Signals | `scripts/customer-behavior/rw-03-b2b-b2c-detection.py` |
| RW-4 | RFM Segmentation | `scripts/customer-behavior/rw-04-rfm-segmentation.py` |
| RW-10 | B2B Account Health Scoring | `scripts/customer-behavior/rw-10-b2b-account-health.py` |
| RW-16 | Customer Basket Migration Tracking | `scripts/customer-behavior/rw-16-basket-migration-tracking.py` |
| RW-19 | Payment Behavior Scoring for B2B Credit | `scripts/customer-behavior/rw-19-payment-behavior-scoring.py` |

---

### OR-3. Shopping Mission Type Analysis

**Business problem:** Is this a planned stock-up business or a top-up convenience business? The answer determines UX design, recommendation engine strategy, and promotion structure.

**Data requirements:** order_id, basket_size. User segments if available.

**Implementation approach:** Examine the basket size distribution for bimodality using KDE peak detection and Hartigan's dip test. If bimodal, derive the mission boundary from the valley between modes rather than using an arbitrary cutoff. Compute the single-item order rate by segment. Test whether segment differences are meaningful using chi-squared testing with Cramér's V for effect size. The output is a classification of the business as stock-up-dominant, top-up-dominant, or mixed, along with segment-level single-item rates and mission type proportions.

**Implementation:** see `scripts/customer-behavior/or-03-shopping-mission-type.py`

**Business output:** Classification of dominant shopping mission, segment-level breakdowns of mission type proportions, and actionable thresholds for basket size that separate missions.

**Common mistakes:**
- Using a fixed basket size threshold for "small" vs "large" without testing the actual distribution shape.
- Treating the single-item order rate as a quality metric (something to minimize) when it is a structural feature of the business model.

**Confidence labeling:**
- **CONFIRMED** if clear bimodality exists (dip test p < 0.05) or segment-level single-item rates differ meaningfully.
- **QUALIFIED** if bimodality is weak or borderline.
- **FRAGILE** if fewer than 1,000 orders in the dataset.

---

### OR-4. Customer Lifecycle Reorder Trajectory

**Business problem:** At what point does habitual behavior lock in? Are there customer types that never reach the habit threshold? Understanding the habit formation curve determines when to invest in retention versus acquisition.

**Data requirements:** order_id, user_id, order_number, reordered flag.

**Implementation approach:** Compute the reorder rate by order number across the customer base. Drop order numbers with insufficient observations by applying a CI-width stability criterion — if the confidence interval at a given order number is too wide relative to signal, it adds noise rather than information. Find the inflection point in the reorder curve via second derivative analysis, which identifies where the rate of change in reorder behavior shifts from accelerating to decelerating. Decompose by user segment. Test for plateau in the post-inflection region using linear regression: a slope statistically indistinguishable from zero indicates a permanent behavioral ceiling rather than continued growth.

**Implementation:** see `scripts/customer-behavior/or-04-lifecycle-reorder-trajectory.py`

**Business output:** The order number at which habit behavior locks in, per-segment plateau levels, and identification of segments that never reach the habit threshold.

**Common mistakes:**
- Treating the plateau as a retention failure when it is a natural behavioral ceiling.
- Treating the population-level inflection point as universal without testing whether it holds per segment.
- Using a fixed order number (e.g., "order 5") as the habit formation point without empirical verification.

**Confidence labeling:**
- **CONFIRMED** if the inflection point is stable across two different smoothing methods and per-segment plateau tests reach significance.
- **QUALIFIED** if the inflection point is sensitive to smoothing bandwidth choice.
- **FRAGILE** if fewer than 500 customers per segment.

---

### OR-5. Basket Composition Mode Distribution

**Business problem:** Do customers shop in reorder mode, discovery mode, or both? The answer determines whether the recommendation strategy should separate repeat and discovery experiences or blend them.

**Data requirements:** order_id, reordered flag, basket_size. User segments.

**Implementation approach:** Compute the reorder percentage for each non-first order (first orders have no reorder history by definition). Classify each order into modes: pure_habit (100% reordered items), pure_discovery (0% reordered items), and mixed. Perform segment decomposition using chi-squared testing with Cramér's V for effect size. Derive the practical significance floor from the dataset itself rather than using a textbook threshold, since effect size interpretation depends on sample characteristics.

**Implementation:** see `scripts/customer-behavior/or-05-basket-composition-mode.py`

**Business output:** Distribution of shopping modes across the customer base, segment-level mode proportions, and whether mode differences across segments are large enough to warrant segment-specific recommendation strategies.

**Common mistakes:**
- Using fixed reorder percentage cutoffs (e.g., >80% = habit) rather than data-derived thresholds.
- Treating the mixed-mode rate as a binary classification problem when the degree of mixing carries information.

**Confidence labeling:**
- **CONFIRMED** if Cramér's V exceeds the dataset-derived practical significance floor and the pattern holds across two temporal splits of the data.
- **QUALIFIED** if some segments have insufficient sample sizes.
- **FRAGILE** if fewer than 500 orders per segment.

---

### OR-6. Personal Ordering Cadence Distribution

**Business problem:** What is the actual distribution of ordering rhythms across the customer base? Is there a dominant cadence (e.g., weekly) or is behavior too heterogeneous for anything but personalized timing?

**Data requirements:** user_id, order_id, inter-order interval (days between consecutive orders).

**Implementation approach:** Compute the per-user dominant cadence as the mode of their inter-order intervals. Examine the population-level distribution of dominant cadences using peak detection and the dip test for multimodality. If distinct peaks exist, derive bucket boundaries from the valleys between peaks rather than imposing arbitrary day ranges. Cross-tabulate cadence buckets with behavioral segments to determine if cadence is segment-dependent.

**Implementation:** see `scripts/customer-behavior/or-06-personal-ordering-cadence.py`

**Business output:** Population cadence distribution, identified cadence clusters with data-derived boundaries, and segment-cadence cross-tabulation showing whether cadence is independent of or correlated with customer type.

**Common mistakes:**
- Assuming weekly dominance without testing the actual distribution shape.
- Using fixed day-range buckets (e.g., 1-7, 8-14, 15-30) that do not align with actual behavioral clusters.
- Treating data caps (e.g., a 30-day maximum inter-order interval in the dataset) as literal values rather than right-censored observations.

**Confidence labeling:**
- **CONFIRMED** if multimodality is statistically significant or segment-level cadences show meaningful Cramér's V with at least 100 customers per segment.
- **FRAGILE** if the average customer has fewer than 10 orders, making per-user cadence estimation unreliable.

---

### OR-15. Temporal Basket Size Variation

**Business problem:** Does when an order is placed affect basket size enough to justify timing-based promotions? If so, is the effect uniform or driven by specific customer segments?

**Data requirements:** order_id, basket_size, order_dow (day of week), order_hour_of_day. User segments.

**Implementation approach:** Start with population-level Kruskal-Wallis testing by day of week. Compute eta-squared as the effect size measure. Then perform MANDATORY segment decomposition: compute the weekend versus weekday basket premium for each segment separately. Test for concentration — if the largest segment-level effect is more than three times the smallest, the population-level finding is segment-driven rather than universal. Report segment-specific effects alongside population effects to prevent false generalization.

**Implementation:** see `scripts/customer-behavior/or-15-temporal-basket-variation.py`

**Business output:** Population-level and segment-level temporal effects on basket size, identification of which segments drive the pattern, and whether timing-based promotions should be universal or segment-targeted.

**Common mistakes:**
- Acting on a population-level temporal effect without performing segment decomposition.
- Using the population basket premium as if it applies uniformly to all customer segments.

**Confidence labeling:**
- **CONFIRMED (segment-specific)** if the within-segment effect exceeds the practical significance floor.
- **POPULATION-ONLY** if the effect reverses or disappears within individual segments (Simpson's paradox).
- **FRAGILE** if segment-level sample sizes are too small for reliable within-segment testing.

---

### OR-20. Segment-Conditional Strategy Matrix

**Business problem:** For which behavioral metrics can the business use a single population-level strategy, and for which metrics must the approach be segment-specific? This pattern prevents both over-segmentation (unnecessary complexity) and under-segmentation (ignoring real differences).

**Data requirements:** User-level behavioral metrics (basket size, reorder rate, single-item rate, ordering interval, etc.). User segments.

**Implementation approach:** Define the key metrics to evaluate: median basket size, reorder rate, single-item rate, and median inter-order interval. Compute each metric at the population level and per segment. Calculate the divergence ratio for each metric as max segment value divided by min segment value. Derive the divergence threshold from the median of all divergence ratios rather than using a fixed number. Metrics with a divergence ratio above the threshold require SEGMENT-SPECIFIC strategy; those below can use population-level approaches.

**Implementation:** see `scripts/customer-behavior/or-20-segment-conditional-strategy.py`

**Business output:** A matrix mapping each metric to either "population-level strategy sufficient" or "segment-specific strategy required," with the divergence ratios as supporting evidence.

**Confidence labeling:**
- **CONFIRMED** if segment assignments are stable and divergence ratios are consistent across temporal halves of the data.

---

### RW-3. B2B/B2C Customer Detection from Ticket Signals

**Business problem:** The POS system has no customer type flag, but the business serves both resellers (B2B) and families (B2C). Every subsequent analysis — pricing, promotion, assortment — requires this segmentation as a prerequisite.

**Data requirements:** transaction_id, date, time, total_amount, item_count. Customer IDs if available.

**Implementation approach:** Build transaction-level features: total amount, item count, unique SKU count, category count, hour of day, day of week, and maximum quantity of any single SKU in the basket. Test for bimodality in the log-transformed ticket value distribution using peak detection. Fit a Gaussian Mixture Model on the log-transformed feature set to derive a data-based separation threshold rather than using a fixed currency amount. Assign labels based on which cluster each transaction belongs to, interpreting clusters by their mean characteristics.

**Business output:** A segmented customer base. Segment names and share must be data-derived from cluster centroids (e.g., "small high-frequency baskets indicative of small-format resellers," "bulk-quantity low-frequency baskets indicative of institutional buyers," "broad-category mid-ticket baskets indicative of end consumers") rather than imposed from an external industry taxonomy.

**Implementation:** see `scripts/customer-behavior/rw-03-b2b-b2c-detection.py`

**Common mistakes:**
- Using any fixed currency threshold to separate B2B from B2C — this becomes obsolete in inflationary environments and fails to generalize across markets.
- Assuming all tax-ID holders are B2B when individuals can hold the same identifier type.
- Not validating the statistical segmentation against known B2B accounts where ground truth exists.

**Confidence labeling:**
- **CONFIRMED** if the bimodal distribution is visible and the GMM achieves a silhouette score above 0.4.
- **QUALIFIED** if there is overlap between modes making clean separation difficult.
- **FRAGILE** if the distribution is unimodal, indicating the business may not have a clear B2B/B2C split.

---

### RW-4. RFM Segmentation

**Business problem:** Which customers are most valuable, at risk of leaving, or should be targeted for reactivation? RFM provides the foundation for lifecycle marketing and retention prioritization.

**Data requirements:** customer_id, transaction_date, transaction_amount.

**Implementation approach:** Run RFM within previously detected segments (from RW-3), not across the full mixed population. Calculate Recency (days since last purchase), Frequency (number of purchases in the analysis window), and Monetary (total spend). Monetary robustness note: raw currency values are unreliable across periods of substantial price movement; options include deflating by CPI, using percentile rank within each period, or substituting unit volume for monetary value. Score each dimension using quintiles that are data-derived from the actual distribution rather than fixed boundaries. Map the resulting score combinations to actionable segment labels.

**Business output:** Customer classification with associated actions. Example segment labels (to be confirmed against cluster characteristics rather than imposed): Champions (highest value, most frequent), Loyalists (consistent mid-value), High-Spend Low-Frequency, At-Risk (declining recency or frequency), Lapsed (beyond recovery threshold), New (recent first purchase). Churn early warning rule: flag any customer whose time since last purchase exceeds twice their historical inter-purchase interval.

**Implementation:** see `scripts/customer-behavior/rw-04-rfm-segmentation.py`

**Common mistakes:**
- Running RFM on a mixed B2B/B2C population where the dimensions have fundamentally different scales.
- Using nominal monetary values when prices have moved materially across the window, making more recent purchasers appear more valuable purely from price drift.
- Using fixed time windows for recency scoring when purchase cadences vary by segment.
- Not accounting for seasonal customers who appear lapsed but are simply between seasons.

**Confidence labeling:**
- **CONFIRMED** if segments show statistically significant differences on retention rate with bootstrap stability above 70%.
- **QUALIFIED** if the monetary dimension is unreliable because no period-normalization was applied.
- **FRAGILE** if the dataset covers fewer than 6 months or contains fewer than 100 customers.

---

### RW-10. B2B Account Health Scoring

**Business problem:** Which B2B accounts are healthy, which are deteriorating, and which need immediate attention? Provides the basis for account management prioritization and early intervention.

**Data requirements:** customer_id, date, amount, quantity, sku_id.

**Implementation approach:** Construct four health components. Frequency trend: compute the slope of monthly order count over the observation window — negative slope indicates declining engagement. Value trend: compute the slope of period-normalized monthly spend — must use period-normalized values, not raw nominal values. Breadth: count of unique product categories purchased — higher breadth indicates a stickier account that is harder to replace. Recency: days since last purchase, inverted so that more recent is healthier. Normalize each component to a 0-1 scale, combine into a composite score, and classify accounts into Green (healthy), Yellow (watch), and Red (action required). Sensitivity-test the composite by running it with at least two alternative weighting schemes to verify that classification is not an artifact of weight choice (this connects to pattern M5 for formal sensitivity analysis).

**Implementation:** see `scripts/customer-behavior/rw-10-b2b-account-health.py`

**Business output:** Account-level health classification with component scores, prioritized list for account management action, and early warning flags for accounts transitioning from Green to Yellow.

**Confidence labeling:**
- **CONFIRMED** if the health score classification is stable across two different weighting schemes (i.e., the same accounts land in the same tier regardless of weights).
- **QUALIFIED** if classification is sensitive to weight choices, meaning the composite is not robust.

---

### RW-16. Customer Basket Migration Tracking

**Business problem:** Are customers changing what they buy over time? This pattern reveals trading down (switching to cheaper brands), trading out (dropping categories entirely), or consolidation behavior — all critical signals under inflationary pressure.

**Data requirements:** customer_id, date, category (or brand), quantity.

**Implementation approach:** For each customer, compute the monthly category share of their basket (what percentage of items come from each category). Track shifts in these shares period-over-period. Key migration signals: increasing share of private label combined with decreasing share of premium national brands indicates trading down. Decreasing category count indicates consolidation. Complete disappearance of discretionary categories indicates trading out. Aggregate individual migrations to identify population-level trends.

**Implementation:** see `scripts/customer-behavior/rw-16-basket-migration-tracking.py`

**Business output:** Customer-level migration trajectories, population-level trend identification (trading down, trading out, consolidation), and early warning when migration accelerates.

**Confidence labeling:**
- **CONFIRMED** if the migration pattern is consistent across 50 or more customers and spans at least 6 months of data.
- **QUALIFIED** if the pattern is visible in a subset of customers only and may not represent a population trend.

---

### RW-19. Payment Behavior Scoring for B2B Credit

**Business problem:** Which B2B customers should receive credit, how much, and which customers show signs of payment stress that warrant tighter terms?

**Data requirements:** customer_id, invoice data including issue dates, due dates, and actual payment dates.

**Implementation approach:** Compute per-customer payment metrics: average days to pay (from invoice date to payment date), payment trend (slope of days-to-pay over time — positive slope means slowing payments), percent of invoices paid late, maximum overdue days observed, and total outstanding balance. Red flag combination: a slowing payment trend plus a high late rate plus increasing outstanding balance signals deteriorating creditworthiness. Distinguish strategic delay (consistent slight lateness during periods of monetary stress, where the real cost of debt is falling) from genuine distress (accelerating lateness with increasing outstanding balances) — the first is a rational financial behavior, the second is a credit-risk signal.

**Implementation:** see `scripts/customer-behavior/rw-19-payment-behavior-scoring.py`

**Business output:** Per-customer credit risk score, recommended credit limit adjustments, and flagged accounts requiring immediate review of payment terms.

**Confidence labeling:**
- **CONFIRMED** if the dataset covers 6 or more months with at least 10 invoices per customer, providing enough history for trend estimation.
- **FRAGILE** with fewer data points, as payment trends cannot be reliably estimated from sparse observations.
