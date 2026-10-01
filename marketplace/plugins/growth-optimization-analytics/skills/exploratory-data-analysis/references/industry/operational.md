# Domain Reference: Operations, Inventory, Margin, Finance, and Supplier Patterns

This file is a domain reference for operational analytics patterns. It documents reusable analytical patterns. NO Python code lives here -- all code goes in `scripts/`. Each pattern documents: business problem, data requirements, implementation approach (prose only), business output, common mistakes, and confidence labeling.

---

## Patterns

### RW-6. Shrinkage and Ticket Anomaly Detection

**Business problem:** Is the business losing inventory to theft, scanning errors, or administrative failures? Where should investigation efforts focus?

**Data requirements:** `transaction_id`, `cashier_id`, `datetime`, `sku_id`, `quantity`, `unit_price`. Preferred: `void_flag`, `refund_flag`, `discount_amount`, inventory count data.

**Implementation approach:** Compute the value-per-item ratio for each transaction (total value divided by total items). Z-score this ratio per cashier, not globally -- each cashier has their own baseline reflecting the mix of products they typically scan. Derive the anomaly threshold from the distribution shape to produce a manageable investigation list (target 50-200 flags per period) rather than applying a fixed z-score cutoff. At the cashier level, flag those whose low-value transaction rate exceeds the 90th percentile across all cashiers. Use control charts (X-bar or CUSUM) for weekly shrinkage rates by department to detect drift over time. Distinguish physical shrinkage (book inventory exceeds physical count) from scanning errors (SKU rings at wrong price) and administrative losses (receiving discrepancies, damaged goods not written off).

**Business output:** A prioritized investigation list with estimated loss amounts, grouped by likely cause (theft pattern, scanning error, administrative gap). Department-level shrinkage trends with control limits.

**Common mistakes:** Global z-scores instead of per-cashier baselines (a cashier in electronics will always look anomalous vs. one in groceries). Not excluding known promotional periods (deep discounts look like sweethearting). Assuming all anomalies are theft -- most are process failures.

**Confidence labeling:** CONFIRMED if the pattern persists across 3+ months, is specific to certain cashiers or shifts, and shows greater than 5 sigma separation from peers. QUALIFIED if partially explained by operational factors (new cashier, system change). FRAGILE if based on fewer than 1 month of data.

Implementation: see `scripts/operational/rw-06-shrinkage-detection.py`

---

### RW-8. Gross Margin Analysis

**Business problem:** Where is the business actually making money? Which products, categories, suppliers, and branches generate profit vs. just revenue?

**Data requirements:** `sku_id`, `quantity`, `unit_price`, `unit_cost`, `date`. Preferred: `category`, `supplier`, `branch`, `customer_segment`.

**Implementation approach:** Compute margin metrics by every available dimension (category, supplier, branch): total revenue, total margin, margin percentage, transaction count, and margin contribution (share of total margin). Identify margin traps -- SKUs or categories with high revenue but low or negative margin that consume resources without generating profit. Compare supplier margins within the same category to identify negotiation opportunities. Check branch divergence for the same SKU (same product selling at different margins across locations indicates pricing inconsistency or cost allocation issues). For low-margin SKUs flagged as potential problems, perform a loss leader validation: compute the average basket margin when the SKU is present vs. absent. A justified loss leader drives significantly higher complementary purchases that offset its own margin shortfall.

**Business output:** Margin contribution waterfall by category. Supplier margin comparison within category. Branch margin divergence report. Loss leader justification or elimination list.

**Common mistakes:** Stale cost data -- when supplier costs move frequently, margin computed with 90-day-old costs is fiction. Comparing margin percentages without volume context (a 50% margin on a product selling 2 units per month is irrelevant). Not distinguishing front margin (invoice price minus cost) from back margin (supplier rebates, volume bonuses) -- the P&L sees both but the transaction data usually shows only front margin.

**Confidence labeling:** CONFIRMED if cost data is current (fewer than 30 days old) and computed margin reconciles within 5% of the P&L gross margin line. QUALIFIED if cost data is 30-60 days old. FRAGILE if no cost data exists and margin is estimated from industry benchmarks.

Implementation: see `scripts/operational/rw-08-gross-margin-analysis.py`

---

### RW-9. Intermittent Demand Forecasting (Croston's Method)

**Business problem:** What reorder quantity and timing should be used for slow-moving SKUs that have many zero-demand periods?

**Data requirements:** `sku_id`, `date`, `quantity_sold` (daily or weekly granularity).

**Implementation approach:** Standard moving averages and exponential smoothing fail for intermittent demand because the frequent zeros drag down the forecast, leading to chronic understocking. Croston's method addresses this by separately forecasting two components: the demand size (conditional on demand occurring) and the inter-demand interval (time between non-zero demand events). Each component is smoothed independently, and the final forecast is their ratio. Use the statsforecast library with CrostonOptimized, which selects smoothing parameters automatically. Apply this method to SKUs identified as intermittent: coefficient of variation greater than 0.7 or more than 50% zero-demand periods.

**Business output:** SKU-level reorder quantities and suggested reorder intervals. Comparison of Croston forecast accuracy vs. naive method to demonstrate improvement.

**Common mistakes:** Applying Croston to fast-moving SKUs where standard methods work better. Using daily granularity when weekly is more appropriate (too many zeros at daily level for products that sell a few times per week). Not validating with a proper holdout test.

**Confidence labeling:** CONFIRMED if MASE is below 1.0 on a held-out test set and Croston outperforms the naive method on more than 60% of SKUs. QUALIFIED if MASE is between 1.0 and 1.5. FRAGILE if MASE exceeds 1.5 or the SKU has fewer than 20 non-zero demand observations.

Implementation: see `scripts/operational/rw-09-intermittent-demand.py`

---

### RW-11. Working Capital and Cash Conversion Cycle

**Business problem:** How efficiently does the business convert inventory investment into cash? This is a core liquidity question for any inventory-intensive business, and becomes especially acute when prices are moving and holding inventory means holding a depreciating asset.

**Data requirements:** `date`, `inventory_value` (or quantities multiplied by cost), `sales`, `accounts_receivable`, `accounts_payable`.

**Implementation approach:** The cash conversion cycle equals DIO + DSO - DPO (days inventory outstanding plus days sales outstanding minus days payable outstanding). When prices are moving substantially over the analysis window, nominal DIO is misleading because inventory value rises from cost increases, not from more days of stock. Use unit-based DIO as a robustness check: average units on hand divided by average daily units sold. This strips out the price-movement distortion. Track CCC monthly and overlay any known structural-break boundaries. Early warning signal: rising DIO combined with stable DSO and falling DPO means the business is consuming cash to fund growing inventory -- a liquidity squeeze is developing even if nominal sales look healthy.

**Business output:** Monthly CCC decomposition (DIO, DSO, DPO) in both nominal and unit-based terms. Trend analysis with regime annotations. Cash flow impact quantification of a 1-day improvement in each component.

**Common mistakes:** Using only nominal DIO when prices are moving (overstates inventory duration). Ignoring seasonality in receivables (cyclical income events shift payment patterns). Not distinguishing trade payables from other payables.

**Confidence labeling:** CONFIRMED if complete financial data (inventory, receivables, payables) is available at monthly granularity. QUALIFIED if only sales and inventory data exist (DSO and DPO must be estimated or omitted). FRAGILE if inventory values are estimated or only periodic physical counts exist.

Implementation: see `scripts/operational/rw-11-working-capital-ccc.py`

---

### RW-12. Supplier Scorecard and Negotiation Analytics

**Business problem:** Which suppliers deliver the best combination of reliability, margin, and terms? What data supports the next negotiation round?

**Data requirements:** `purchase_date`, `supplier`, `sku_id`, `ordered_qty`, `received_qty`, `unit_cost`, `delivery_date`. Preferred: `promised_delivery_date`, `payment_terms`, `return_rate`.

**Implementation approach:** Score each supplier across multiple dimensions: fill rate (received divided by ordered), lead time reliability (coefficient of variation of delivery times, not just the mean), margin contribution, total spend, and order frequency. Normalize each dimension to a 0-1 scale and apply weights. Run sensitivity tests on the weights -- if the ranking changes dramatically with small weight shifts, the scorecard is fragile and should not be presented as definitive. For negotiation preparation, compute the client's share of each supplier's estimated output (leverage), identify alternative suppliers for the same categories (substitution threat), and compare each supplier's price trend against category-level inflation (are they increasing faster or slower than the market).

**Business output:** Supplier ranking table with composite score and dimension breakdowns. Negotiation brief per supplier highlighting leverage points and risk factors. Alternative supplier mapping.

**Common mistakes:** Treating fill rate as binary (a supplier at 95% and one at 94% are not meaningfully different -- use confidence intervals). Ignoring back-margin contributions (rebates, co-op advertising). Not accounting for supplier switching costs.

**Confidence labeling:** CONFIRMED if 12+ months of purchase data with 10+ orders per supplier scored. QUALIFIED if fewer months or fewer orders per supplier. FRAGILE if purchase records are incomplete or suppliers are scored on fewer than 5 transactions.

Implementation: see `scripts/operational/rw-12-supplier-scorecard.py`

---

### RW-14. Cross-Branch Benchmarking

**Business problem:** Which branch genuinely underperforms vs. simply serving a different market? How do we set fair targets?

**Data requirements:** `branch`, `category`, transaction-level data (at minimum: `date`, `sku_id`, `quantity`, `unit_price`).

**Implementation approach:** Raw revenue comparison across branches is misleading because each branch serves a different catchment with different category preferences. Use category-adjusted performance instead. Compute expected revenue per category per branch as: branch total revenue multiplied by the chain-wide category share. The ratio of actual to expected revenue for each category at each branch reveals true over- or underperformance relative to what the branch's size and the category's importance would predict. A ratio above 1.0 means the branch outperforms in that category given its overall size; below 1.0 means underperformance. Extend to 6-8 KPIs (margin, basket size, conversion if available, shrinkage rate, labor productivity) and present as a spider chart per branch for executive communication.

**Business output:** Branch performance matrix with actual/expected ratios by category. Spider charts on 6-8 KPIs per branch. Ranked opportunity list (branches with the largest gap between actual and expected in high-margin categories).

**Common mistakes:** Comparing branches that opened at different times without adjusting for maturity curves. Ignoring data quality differences across branches (one branch may have better POS discipline). Using absolute metrics instead of ratios (a branch in a smaller city will always have lower absolute revenue).

**Confidence labeling:** CONFIRMED if all branches have comparable data quality, similar operating periods, and 12+ months of history. QUALIFIED if branches have different opening dates or data gaps in some periods. FRAGILE if branch-level data cannot be reliably separated or fewer than 6 months of overlap exist.

Implementation: see `scripts/operational/rw-14-cross-branch-benchmarking.py`

---

### OR-22 — Operational-Factor Revenue Regression
For physical retail with store-level attributes, test operational factors (selling area, employee count, product breadth, etc.) against revenue using Spearman r with partial correlation controlling for geography. The conventional assumption 'bigger store = more revenue' is common across retail verticals and rarely validated with data. The typical finding: product breadth (assortment width) dominates physical size as a revenue predictor, especially in specialty retail where assortment matters more than shelf space. Report raw and partial correlations (controlling for geography/market), and compare R² for geography-only, operations-only, and combined models. → Cross-reference: S10 (confound control), H12-type hypothesis.

---

### RW-22 — Promotional Saturation Diagnostic
When more than 50% of transactions carry a promotional flag, switch from standard lift analysis (RW-13) to a saturation diagnostic. At high promotion penetration, the 'non-promoted' baseline may be a systematically different minority population, not a true control. The diagnostic has three steps: (1) same-product price comparison — are promoted and non-promoted unit prices identical? If yes, the promotion is a visibility label, not a price change. (2) Effective discount rate calculation — compute the actual discount as a fraction of the total transaction value; rates below 2% are cosmetic. (3) Within-product visibility lift by product tier — test whether the promotional label drives volume through visibility/placement rather than price incentive. Distinguish promotional dependency (the business can't operate without promotions) from promotional effectiveness (promotions drive incremental behavior). → Cross-reference: T7 (seasonal promotion period validation), S11 (causal direction for visibility vs price response).
