# Cart Dynamics, Timing, Sequencing, and Temporal Patterns

Domain reference for timing-based analytics: cart position behavior, intervention windows, time-of-day effects, reorder intervals, demand patterns, and promotional measurement.

All implementation code lives in `scripts/cart-temporal/`. This file contains only business context, data requirements, analytical approaches (prose), outputs, pitfalls, and confidence labeling.

---

## OR-7. Cart Sequence Behavioral Zone Profiling

**Business problem:** Does the sequence of items added to an online cart carry behavioral signal for recommendation strategy?

**Data requirements:** order_id, product_id, add_to_cart_order, reordered flag. Department and category metadata for each product.

**Implementation approach:** Compute the reorder rate at each cart position (the fraction of items at position N that are reorders). To determine how many observations per position are needed for stable estimates, derive a minimum observation threshold from confidence interval width stability -- increase the sample size incrementally and find the point where the CI width stops shrinking meaningfully. Test whether there is a monotonic relationship between cart position and reorder rate using Spearman rank correlation. To find natural zone boundaries (rather than imposing arbitrary ones), compute the second derivative of the reorder-rate-by-position curve and identify inflection points where the rate of change shifts. Once zones are defined, compute the department distribution within each zone and test zone-by-department independence using a chi-squared test to determine whether different zones carry genuinely different product profiles.

**Business output:** Behaviorally-grounded cart zones that can drive position-aware recommendation strategy. Each zone has a characteristic reorder rate and department mix.

**Implementation:** see `scripts/cart-temporal/or-07-cart-sequence-zones.py`

**Common mistakes:**
- Fixing zone boundaries at arbitrary positions (e.g., 1-3, 4-6, 10+) without testing whether natural breaks exist in the data.
- Treating zone profiles as static across customer segments and basket sizes. A 5-item basket and a 30-item basket may have entirely different position dynamics.

**Confidence labeling:**
- CONFIRMED if Spearman correlation is statistically significant and zone boundaries are stable across at least two independent smoothing methods.
- QUALIFIED if the relationship is monotonic but boundary placement is ambiguous (inflection points are soft).
- FRAGILE if fewer than 1M order-product rows, as position-level estimates become noisy.

---

## OR-8. Intervention Window Optimization

**Business problem:** At what time of day or day of week should marketing interventions (push notifications, emails, promotions) be sent to maximize engagement?

**Data requirements:** order_id, order_hour_of_day or full timestamp, order_dow. User segment labels where available.

**Implementation approach:** Compute a volume index by hour, defined as hour volume divided by mean hourly volume. The peak window consists of hours where this index exceeds one plus one standard deviation of the index distribution. The key insight is that the optimal intervention window is BEFORE the peak, not during it -- the goal is to catch users as they are forming intent, not after they have already placed an order. Estimate the pre-peak intervention window from ramp sharpness: identify the hour with the sharpest volume increase (largest first derivative of the volume curve) and target intervention at or just before that hour. Decompose the analysis by customer segment to produce segment-specific intervention windows, since different segments may have different temporal profiles.

**Business output:** Segment-specific optimal send times for marketing interventions, with the distinction between peak activity windows and optimal pre-peak intervention windows.

**Implementation:** see `scripts/cart-temporal/or-08-intervention-window.py`

**Common mistakes:**
- Sending marketing communications during peak hours rather than before them. By the time someone is already ordering, the intervention is wasted.
- Conflating volume timing with composition timing. The hour when most orders happen is not necessarily the hour when order composition changes. These are independent questions requiring separate analyses (see OR-9).

**Confidence labeling:**
- CONFIRMED if peak timing is consistent across 4 or more weeks with coefficient of variation below the stability threshold.
- QUALIFIED if peak timing shifts week-to-week but a dominant pattern is visible.
- FRAGILE if fewer than 8 weeks of data or fewer than 10,000 total orders.

---

## OR-9. Time-of-Day Volume vs. Composition Separation

**Business problem:** Does the hour of ordering affect what is purchased (composition), or only how many orders are placed (volume)? This distinction matters because volume-only variation calls for staffing adjustments, while composition variation calls for assortment and recommendation changes.

**Data requirements:** order_id, order_hour_of_day, reorder rate per order (or any per-order composition metric).

**Implementation approach:** Use a Kruskal-Wallis test across hours for reorder percentage to test the composition hypothesis (that the distribution of reorder rates differs across hours of day). Compute the effect size from the test statistic. To determine whether this effect size is practically meaningful, derive a practical significance floor from the distribution of all effect sizes computed across the engagement -- this floor represents the threshold below which an effect, even if statistically significant, is too small to act on. Compare the observed effect size to this floor.

**Business output:** A clear determination of whether time-of-day variation is volume-only (adjust staffing) or also compositional (adjust recommendations, assortment, and merchandising by hour).

**Implementation:** see `scripts/cart-temporal/or-09-volume-vs-composition.py`

**Common mistakes:**
- Concluding "people shop differently at different times" based solely on volume variation. More orders at 10am than 3am does not mean the orders contain different products.
- Using p-value as the decision criterion on large datasets. With millions of orders, nearly any difference will be statistically significant. The practical significance floor is the correct decision tool.

**Confidence labeling:**
- CONFIRMED if effect size exceeds the practical significance floor.
- FRAGILE if effect size falls below the floor, regardless of p-value. Statistical significance without practical significance does not support action.

---

## OR-19. Reorder Interval Spike Analysis

**Business problem:** What are the true ordering rhythms of customers, and are any apparent peaks in the interval distribution actually data artifacts rather than genuine behavioral patterns?

**Data requirements:** user_id, order_id, days_since_prior_order.

**Implementation approach:** Plot the raw distribution of reorder intervals. Check for right-censoring at the maximum observed value: if the count at the maximum value exceeds 1.5 times the count at the next highest peak, the maximum value is likely a censoring artifact (the field was capped, so all intervals beyond that threshold are recorded as the cap value). Exclude censored values from cadence analysis entirely. Apply peak detection on the cleaned histogram to identify genuine behavioral peaks (e.g., weekly cadence at 7 days, biweekly at 14 days).

**Business context:** During the Instacart analysis, the prominent spike at 30 days was a right-censoring artifact -- the days_since_prior_order field was capped at 30, so all intervals of 30 or more days were recorded as 30. This was not monthly shopping behavior. This pattern applies broadly to any dataset with capped or truncated interval fields. Always check the maximum value for censoring before interpreting peaks.

**Business output:** Cleaned interval distribution with genuine behavioral peaks identified, enabling accurate cadence-based targeting (e.g., nudge a weekly shopper on day 6, not day 29).

**Implementation:** see `scripts/cart-temporal/or-19-reorder-interval-spike.py`

**Common mistakes:**
- Interpreting the censored spike as a genuine behavioral peak and building marketing cadences around it.
- Failing to check for censoring before running cadence analysis.

**Confidence labeling:**
- CONFIRMED if peaks remain visible after excluding censored values and are stable across user subsets (e.g., high-frequency vs. low-frequency shoppers).

---

## RW-7. Demand Pattern Analysis

**Business problem:** When do customers come, and what do they buy at different times? This drives staffing decisions, replenishment scheduling, and temporal targeting of promotions.

**Data requirements:** transaction_id, datetime (date and time), quantity, amount. Preferred additional fields: product category, customer_segment (B2B vs. B2C where applicable).

**Implementation approach:** Compute day-of-week patterns by expressing each metric (transaction count, units sold, average ticket size) as an index relative to the weekly mean. A Monday index of 1.15 means Monday runs 15% above average. Compute hour-of-day patterns separately for weekdays and weekends, since the intra-day profile often differs substantially. Where customer segment data is available, separate B2B from B2C temporal patterns. B2B customers typically peak in early morning hours (restocking before opening), while B2C customers peak in evening hours and on weekends.

**Staffing optimization:** Derive the throughput benchmark from the observed distribution of transactions per cashier per hour, using the median rather than a fixed industry benchmark. The median from actual data reflects the specific store's layout, product mix, and customer behavior. Compute minimum cashier coverage by hour as the hourly transaction volume divided by this throughput benchmark, rounded up.

**Business output:** Hourly and daily demand indices, segment-separated temporal profiles, staffing coverage recommendations by hour.

**Implementation:** see `scripts/cart-temporal/rw-07-demand-pattern-analysis.py`

**Common mistakes:**
- Not separating B2B and B2C temporal patterns. Blended patterns obscure the distinct rhythms of each segment and lead to suboptimal staffing and promotion timing.
- Comparing January to March without seasonal adjustment. Demand levels change across months; the temporal pattern (which hours, which days) may or may not.
- Using transaction count alone when the value pattern differs. A day with fewer but larger transactions requires different handling than a day with many small ones.

**Confidence labeling:**
- CONFIRMED if based on 12 or more months of data, the pattern is visible across all months, and the day-of-week pattern has a coefficient of variation below 15%.
- QUALIFIED if 6 to 12 months of data are available.
- FRAGILE if fewer than 6 months of data or if there are gaps in the data that could distort temporal patterns.

---

## RW-13. Promotional Effectiveness Measurement

**Business problem:** Did the promotion actually increase total profit, or did it merely shift demand forward in time (customers buying during the promotion what they would have bought anyway the following week)?

**Data requirements:** Transaction data with dates, quantities, and amounts. Promotion period start and end dates. Promotion cost or discount amount.

**Implementation approach:** Use an interrupted time series design. Establish a baseline from the same day-of-week in non-promoted weeks (matching DOW controls for weekly seasonality). Compare actual volume and revenue during the promotion to this baseline to compute raw uplift. Critically, measure at the category level, not just the promoted SKU, to capture both halo effects (increased sales of related products) and cannibalization (decreased sales of substitutes). After the promotion ends, check for a post-promotion dip, which indicates demand pull-forward rather than true incremental demand. Compute net uplift as the sum of promotional uplift and the post-promotion dip (which will be negative if pull-forward occurred). The key decision metric is Return on Promotion, defined as incremental gross margin minus promotion cost, divided by promotion cost.

**Business output:** Net promotional uplift (after accounting for pull-forward), category-level halo and cannibalization effects, and Return on Promotion as the summary decision metric.

**Implementation:** see `scripts/cart-temporal/rw-13-promotional-effectiveness.py`

**Common mistakes:**
- Measuring only the promoted SKU and missing cannibalization of adjacent products.
- Declaring success based on gross uplift during the promotion without checking for the post-promotion dip.
- Using a simple before/after comparison without matching on day-of-week, which confounds promotional effect with weekly seasonality.

**Confidence labeling:**
- CONFIRMED if the pre-promotion baseline period, promotion period, and post-promotion observation period each contain at least 14 days, and the measured uplift exceeds 2 standard deviations of baseline variation.
- QUALIFIED if any of the three periods is shorter than 14 days but the effect is still clearly visible.
- FRAGILE if no proper baseline exists (e.g., the promotion started on day one of available data).

**Selection bias caveat:** Without random assignment of promotions to items/stores, promotional lift estimates are upper bounds — they include both the causal effect of the promotion and the selection effect of promoting items that were already expected to sell well. Always label non-experimental lift estimates as QUALIFIED and include the selection-bias caveat in the finding narrative. Report the absolute unit delta alongside percentage lift. Flag entities where the off-promotion baseline falls below the data-derived low-volume threshold and present their lifts separately with an explicit caveat.

---

## RW-21. Traffic × Basket DOW Decomposition

**Business problem:** Do different high-sales days achieve their volume through different mechanisms — more customers walking in (traffic) or customers buying more per trip (basket expansion)? The answer determines whether the merchandising response should focus on conversion (traffic days) or cross-selling (basket days).

**Data requirements:** Daily unit sales AND daily transaction counts, both at the store or network level. These must be independent signals — unit sales from the item-level fact table, transaction counts from a separate transactions table or POS summary.

**Implementation approach:** Compute Units per Transaction (UPT) = total_unit_sales / total_transactions for each day. Index both daily transactions and daily UPT to their weekly mean (100 = mean). For each day of the week, the Sales Index approximately equals the Traffic Index times the Basket Index. Compare the two components: a day where traffic is high but basket is average is a traffic day; a day where basket is high but traffic is average is a basket-expansion day. Decompose by store type or geography to check whether the pattern is universal or segment-specific.

**Business output:** A DOW classification into traffic-driven days, basket-driven days, and balanced days. Traffic days warrant staffing investment, store-front visibility, and conversion optimization. Basket days warrant in-store merchandising, cross-category displays, and complementary-product placement.

**Implementation:** see `scripts/cart-temporal/rw-21-traffic-basket-decomposition.py`

**Common mistakes:**
- Treating all high-sales days as equivalent when they achieve volume through different mechanisms.
- Not checking whether the decomposition holds across store segments — a network-level basket day may be a traffic day at a specific store type.
- Confusing this with a trend decomposition (which uses the same Sales = Traffic × Basket formula but over months/years rather than DOW).

**Confidence labeling:**
- CONFIRMED if the traffic/basket split is consistent across all major store segments and the difference between the two indices exceeds the practical significance floor.
- QUALIFIED if the split is visible at the network level but reverses in one or more segments.
- FRAGILE if transaction counts are not independent of unit sales (e.g., derived from the same table rather than measured separately).
