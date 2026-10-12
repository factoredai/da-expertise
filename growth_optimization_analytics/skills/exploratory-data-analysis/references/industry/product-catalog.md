# Product Catalog & Assortment — Domain Reference

> **Purpose**: Patterns for analyzing product structure, catalog composition, and assortment strategy.
> All code lives in `scripts/product-catalog/`. This file contains only prose descriptions, business context, and confidence labeling.

---

## OR-1. Traffic Engine vs Retention Engine Classification

**Business problem**: Are products driving most orders the same ones driving repeat purchasing? If not, two distinct management strategies are needed — one for acquisition volume, another for customer retention.

**Data requirements**: product_id, order_id, reordered flag. User identification sufficient to distinguish first vs. repeat orders.

**Implementation approach**: Derive a minimum order threshold where the reorder rate stabilizes by computing a rolling mean across order count and detecting the elbow (the point where marginal change flattens). Rank products on both raw volume and reorder rate independently. Test structural independence between the two rankings with Spearman rank correlation, constructing a bootstrap confidence interval around the coefficient. Measure overlap between the top-ranked products on each dimension at the Pareto elbow (the point where cumulative contribution begins to flatten).

**Key decision**: The degree of overlap matters less than whether the rank correlation confidence interval includes zero. If it does, the two dimensions are structurally independent and require separate management strategies.

**Business output**: Two ranked product lists — Traffic Engines and Retention Engines — with segment-level stability checks. Traffic Engines receive availability and pricing focus. Retention Engines receive subscription and reorder-prompt focus.

**Implementation**: see `scripts/product-catalog/or-01-traffic-vs-retention.py`

**Common mistakes**:
- Using a fixed overlap percentage to declare independence or dependence.
- Binary treatment of what is a spectrum — products can be partially both.
- Not testing within behavioral segments (the overall correlation may mask segment-level divergence).

**Confidence labeling**:
- **CONFIRMED**: Rank correlation CI includes zero and separation holds within all behavioral segments.
- **QUALIFIED**: Correlation is weak but nonzero — dimensions are related but not redundant.
- **FRAGILE**: Fewer than 100 products with sufficient order history to compute a stable reorder rate.

---

## OR-2. Anchor Product Basket Premium Analysis

**Business problem**: Do high-penetration products predict total basket size? If so, a stockout on an anchor product costs far more than that product's own revenue — it suppresses the entire basket.

**Data requirements**: order_id, product_id, user_id. Basket size (item count or value) per order. Product penetration (share of orders containing the product).

**Implementation approach**: Derive a penetration threshold from the product penetration distribution — either an inflection point in the sorted curve or a top-quartile cutoff. For each candidate anchor product, compute the basket size premium: the median basket size for orders containing the product minus the median for orders without it. Then derive an anchor qualification threshold from the distribution of premiums using a Gaussian Mixture Model to find a natural break separating genuine anchors from ordinary high-penetration products.

**Business output**: A short list of anchor products with quantified basket premiums. Stockout cost estimates that include the basket suppression effect, not just the product's own margin.

**Implementation**: see `scripts/product-catalog/or-02-anchor-product-basket.py`

**Common mistakes**:
- Not controlling for order type (e.g., large weekly shops vs. quick top-ups naturally differ in basket size).
- Using a fixed premium percentage threshold instead of deriving it from the data.
- Not verifying the premium holds per customer segment.

**Confidence labeling**:
- **CONFIRMED**: Premium is consistent across segments and penetration is above the derived threshold.
- **QUALIFIED**: Premium concentrates in one segment only.
- **FRAGILE**: Fewer than 500 orders contain the product.

---

## OR-10. Category Behavioral Tier Classification

**Business problem**: Do product categories operate on different purchase logics requiring different management approaches? Some categories are habitual (high reorder), others are exploratory (low reorder). Treating them uniformly wastes resources.

**Data requirements**: product_id, department/category, reordered flag, total_orders per product.

**Implementation approach**: Compute the volume-weighted reorder rate per category (weighting by order count prevents small-volume products from distorting category rates). Bootstrap the observed range of category reorder rates and test whether it exceeds what sampling noise alone would produce. Derive tier boundaries using a Gaussian Mixture Model with BIC selection to determine the optimal number of tiers without imposing a fixed count. Validate tier stability by splitting the data into temporal halves and checking whether products retain their tier assignment.

**Business output**: Category-level tier labels (e.g., habitual, moderate, exploratory) with management implications for each tier.

**Implementation**: see `scripts/product-catalog/or-10-category-behavioral-tier.py`

**Common mistakes**:
- Imposing a fixed tier count (e.g., always three tiers) rather than letting the data determine the number.
- Using unweighted category rates, which lets small categories with volatile rates distort the classification.

**Confidence labeling**:
- **CONFIRMED**: Observed range exceeds the bootstrap null (p < 0.05) and tiers are stable (>75% of products retain tier assignment across temporal halves).
- **QUALIFIED**: Tier boundaries are sensitive to the split point or threshold scheme.
- **FRAGILE**: Fewer than 10 categories with meaningful volume.

---

## OR-11. Universal Staple Identification with Segment Urgency Weighting

**Business problem**: Which products must never be out of stock? And does the urgency of a stockout differ by customer type? A staple for one segment may be irrelevant to another.

**Data requirements**: product_id, user_id (to compute unique user penetration), reordered flag. User segment labels.

**Implementation approach**: Measure user adoption breadth — the number of unique users who have ever ordered each product. Sort products by breadth in descending order and find the inflection point in the curve using the second derivative (the point where breadth drops sharply from "widely adopted" to "niche"). Products above this threshold are staples. For each staple, compute segment-level reorder rates. The urgency multiplier equals the maximum segment reorder rate divided by the minimum segment reorder rate — a high multiplier means stockout impact is uneven across segments.

**Business output**: A staple product list with segment-level urgency scores. Inventory priorities that reflect not just overall importance but differential segment impact.

**Implementation**: see `scripts/product-catalog/or-11-universal-staple-id.py`

**Common mistakes**:
- Using total volume instead of unique user breadth (a product bought 1,000 times by 5 users is not a staple).
- Assuming uniform stockout urgency across segments.

**Confidence labeling**:
- **CONFIRMED**: Clear inflection point in the breadth curve and segment differences in reorder rate are statistically significant.
- **QUALIFIED**: Inflection point is ambiguous (gradual curve rather than sharp elbow).
- **FRAGILE**: Fewer than 6 months of data (seasonal staples may be missed).

---

## OR-13. High-Volume Low-Loyalty Quadrant Analysis

**Business problem**: Products with high volume but low repeat purchasing are commonly mismanaged. Low reorder rate is misread as product failure, but the product may be seasonal, first-order concentrated, or simply a category where repeat purchasing is structurally low.

**Data requirements**: product_id, total_orders, reorder_rate. Product metadata (department, category, aisle).

**Implementation approach**: Create a scatter plot of volume vs. reorder rate. Use the median of each dimension as the boundary (not fixed values, which break across different datasets). This produces four quadrants: core (high volume, high reorder), high_vol_low_loyalty (high volume, low reorder), hidden_gem (low volume, high reorder), and niche (low volume, low reorder). Investigate the HVLL quadrant specifically for alternative explanations — is the product seasonal, concentrated in first orders, or in a category where low reorder is normal? Test whether quadrant membership concentrates in specific departments more than chance would predict.

**Business output**: A quadrant classification for every product. The HVLL quadrant receives special investigation before any discontinuation or deprioritization decisions. Hidden gems receive visibility and promotion consideration.

**Implementation**: see `scripts/product-catalog/or-13-high-vol-low-loyalty.py`

**Common mistakes**:
- Making discontinuation decisions based on reorder rate alone without checking volume.
- Using fixed quadrant boundaries that do not adapt to the dataset.

**Confidence labeling**:
- **CONFIRMED**: Quadrant concentration by department exceeds random expectation (chi-squared test significant).
- **QUALIFIED**: Boundaries are sensitive to the threshold scheme.

---

## OR-14. Premium Product Loyalty Test

**Business problem**: Do premium or specialty product variants (organic, artisan, free-range, etc.) generate higher repeat purchasing than their conventional counterparts? If so, premium assortment serves as a retention lever, not just a margin play.

**Data requirements**: product_id, product_name (for text-based flagging), reorder_rate, total_orders. Department and category for stratified testing.

**Implementation approach**: Flag premium products using text signals in product names (Organic, Artisan, Free-Range, Gluten-Free, Small Batch, etc.). Restrict analysis to products with sufficient order history to produce a stable reorder rate. Test the overall reorder rate difference between premium and conventional products using Mann-Whitney U and compute rank-biserial correlation as the effect size. Then run the test by category separately — the overall result may mask category-level reversals where conventional outperforms premium.

**Business output**: A verdict on whether premium assortment drives retention, overall and by category. Categories where premium loyalty is strongest become targets for assortment expansion.

**Implementation**: see `scripts/product-catalog/or-14-premium-loyalty-test.py`

**Common mistakes**:
- Not controlling for popularity (premium products may simply be rarer, and rarity correlates with reorder behavior).
- Not running the test by category (an overall positive effect may be driven entirely by one category).

**Confidence labeling**:
- **CONFIRMED**: Effect size exceeds a meaningful floor and is consistent across categories.
- **QUALIFIED**: Effect reverses in some categories.
- **FRAGILE**: Fewer than 50 premium products with sufficient history.

---

## OR-16. Core Catalog Overlap Across Segments

**Business problem**: How much of the core catalog is shared across customer segments? The shared portion can be managed universally; the divergent portion needs segment-specific pricing, promotion, and availability strategies.

**Data requirements**: product_id, total_orders per segment. User segment labels.

**Implementation approach**: Identify the core catalog per segment using the Pareto elbow — the smallest set of products accounting for the majority of that segment's volume. Compute the intersection of core catalogs across segments to identify the universal core. Products appearing in one segment's core but not another's are segment-exclusive and require tailored management.

**Business output**: A universal core product list, plus segment-exclusive core lists. The ratio of universal to total core products indicates how differentiated the segments truly are in purchasing behavior.

**Implementation**: see `scripts/product-catalog/or-16-core-catalog-overlap.py`

**Confidence labeling**:
- **CONFIRMED**: Segments are balanced (the smallest segment contains >15% of the total population).
- **QUALIFIED**: Segments are highly imbalanced, making the smaller segment's core catalog unstable.

---

## OR-17. New-Product Trial and Adoption Tracking

**Business problem**: When a customer tries a product for the first time, what is the probability they reorder it? Does this adoption rate differ by category or customer segment? Low trial-to-adoption rates signal product quality or expectation mismatches.

**Data requirements**: user_id, product_id, order_number (to identify sequence), reordered flag.

**Implementation approach**: For each user-product pair, identify the first encounter (the order where the product first appears for that user). Track whether the user reorders the product in any subsequent order. Compute the adoption rate (share of first encounters that lead to at least one reorder) overall, by category, and by customer segment.

**Business output**: Adoption rate benchmarks by category and segment. Products and categories with unusually low adoption rates are candidates for investigation (quality, pricing, expectation mismatch).

**Implementation**: see `scripts/product-catalog/or-17-new-product-trial.py`

**Confidence labeling**:
- **CONFIRMED**: Based on users with 5 or more post-trial orders (sufficient opportunity to reorder).
- **QUALIFIED**: Limited post-trial history reduces certainty about whether non-reorder reflects rejection or insufficient time.

---

## OR-18. Aisle Co-occurrence Affinity Map

**Business problem**: Which product aisles tend to appear together in the same order? This is a lighter, more interpretable alternative to full product-level market basket analysis — useful for store layout, cross-promotion, and category management.

**Data requirements**: order_id, product_id, aisle or category label.

**Implementation approach**: Build an aisle co-occurrence matrix from order-level aisle sets (for each order, record which pairs of aisles are both present). Calculate lift for each pair: observed co-occurrence frequency divided by expected frequency under independence. Derive an actionability threshold from the lift distribution (e.g., the 90th percentile) to filter down to genuinely strong affinities rather than noise.

**Business output**: A filtered affinity map of aisle pairs with strong co-occurrence. Actionable for adjacency planning, cross-category promotions, and bundle design.

**Implementation**: see `scripts/product-catalog/or-18-aisle-co-occurrence.py`

**Confidence labeling**:
- **CONFIRMED**: Top affinities are stable across temporal halves (same pairs appear with similar lift).
- **QUALIFIED**: Some pairs shift between halves, suggesting seasonal or promotional artifacts.

---

## OR-21. Product Lifecycle Stage Classification

**Business problem**: Which products are onboarding gateways (appearing disproportionately in early orders), mature-user staples (appearing in later orders), or exploration items? Each lifecycle stage requires different promotion, placement, and stocking strategies.

**Data requirements**: product_id, order data with order_number (to distinguish early vs. late orders per user).

**Implementation approach**: For each product, compute its first_order_share (proportion of the product's total orders that come from users' first orders) and its mature_order_share (proportion from users with 10+ prior orders, or a data-derived maturity threshold). Classify using median-based boundaries on each dimension: gateway (high first-order share, low mature-order share), staple (low first-order share, high mature-order share), universal (both high), exploration (both low).

**Business output**: A lifecycle label per product. Gateways inform onboarding bundles and first-order promotions. Staples inform retention and subscription offers. Exploration items inform discovery features.

**Implementation**: see `scripts/product-catalog/or-21-product-lifecycle-stage.py`

**Confidence labeling**:
- **CONFIRMED**: Classification is stable across temporal halves.
- **QUALIFIED**: Boundaries shift meaningfully between halves, suggesting the classification is period-dependent.

---

## RW-1. ABC/XYZ Inventory Classification

**Business problem**: Which products deserve tight inventory control vs. loose management? Which have predictable demand vs. erratic demand? The combination determines replenishment strategy.

**Data requirements**: sku_id, date, quantity_sold, unit_cost, unit_price.

**Implementation approach**: Run the ABC classification on BOTH units sold and gross margin independently. Revenue-based ABC can be unreliable when prices move substantially over the analysis window, because price increases shift products between classes without any change in real demand — unit-based classification is immune to price movement. The final ABC class for each product is the higher of the two (if a product is A on units but B on margin, it gets A). For the XYZ classification, compute the coefficient of variation of periodic demand. Derive tercile thresholds from the CV distribution itself rather than using fixed cutoffs (fixed cutoffs like 0.5/1.0 tend to classify nearly everything as Z in high-variance demand environments). The result is a 9-cell matrix (AX, AY, AZ, BX, BY, BZ, CX, CY, CZ) with specific management actions per cell.

**Business output**: A single-page classification table with the recommended replenishment and control action per SKU. A Pareto curve visualization showing cumulative contribution.

**Implementation**: see `scripts/product-catalog/rw-01-abc-xyz-classification.py`

**Common mistakes**:
- Using revenue-only ABC in inflationary environments (products migrate between classes due to price changes, not demand changes).
- Using calendar months for XYZ when holidays and promotional periods add artificial volatility — consider decomposing seasonality first.
- Classifying seasonal products as Z (erratic) when the variation is actually predictable seasonal pattern — decompose seasonality before computing CV.

**Confidence labeling**:
- **CONFIRMED**: Classification is stable across alternative threshold schemes (e.g., 75/92 vs. 80/95 for ABC boundaries) and unit-based and margin-based ABC agree on A-class membership for >75% of products.
- **QUALIFIED**: More than 20% of products change class under alternative thresholds.
- **FRAGILE**: Fewer than 6 months of history.

---

## RW-2. Market Basket Analysis

**Business problem**: Which products are frequently co-purchased? Results inform shelf placement, bundle creation, and suggested order features.

**Data requirements**: transaction_id, sku_id. Preferably customer_segment labels for pre-segmentation.

**Implementation approach**: CRITICAL first step — segment B2B and B2C transactions before running any association rule mining. Mixed data produces useless rules because B2B bulk orders dominate co-occurrence counts. Use the Apriori algorithm (mlxtend implementation). Derive the support threshold from the data: start with a minimum support value that produces between 50 and 200 rules, then adjust. Compute the Kulczynski metric alongside lift — Kulczynski is more robust than lift for items with very different frequencies (lift can be misleadingly high when a rare item co-occurs with another rare item). Derive lift action tiers from the distribution (median lift = moderate affinity, 90th percentile = strong affinity).

**Business output**: A rule table with support, confidence, lift, and Kulczynski for each product pair or set. Tiered by actionability. Segment-specific where applicable.

**Implementation**: see `scripts/product-catalog/rw-02-market-basket-analysis.py`

**Common mistakes**:
- Running on mixed B2B/B2C data (the single most common mistake — produces rules that reflect bulk ordering patterns, not genuine affinities).
- Using lift alone without conviction or Kulczynski (misleading for unequal-frequency pairs).
- Not filtering out promotion-period artificial co-occurrence (two products on sale simultaneously will co-occur without genuine affinity).
- Including the same product at different granularity levels (e.g., brand and SKU both in the item set).

**Confidence labeling**:
- **CONFIRMED**: Rules survive a temporal split with similar lift values and each rule has support representing >50 co-occurrences.
- **QUALIFIED**: Rules are unstable across temporal halves.
- **FRAGILE**: Fewer than 30 co-occurrences for a given rule.

---

## RW-15. SKU Velocity Decay Detection

**Business problem**: Which currently-selling products show early signs of declining demand? Early detection enables proactive decisions — markdown, discontinuation, or investigation — before the product becomes dead stock.

**Data requirements**: sku_id, date, quantity_sold.

**Implementation approach**: Compute monthly unit velocity per SKU over the last 6 months. Fit a linear regression slope to the velocity series. Flag products meeting both criteria: a negative slope (p < 0.10) AND current velocity below 50% of the product's historical peak velocity. The dual condition prevents flagging products that are merely returning to baseline after a promotional spike.

**Business output**: A watchlist of decaying SKUs with slope magnitude, current velocity as a percentage of peak, and statistical significance. Prioritized by inventory exposure (current stock multiplied by decay rate).

**Implementation**: see `scripts/product-catalog/rw-15-sku-velocity-decay.py`

**Confidence labeling**:
- **CONFIRMED**: Slope is significant (p < 0.05) over 6 or more months of data.
- **QUALIFIED**: Slope significance is between p = 0.05 and p = 0.10.
- **FRAGILE**: Fewer than 4 months of history.

---

## RW-18. Cannibalization Detection for New Products

**Business problem**: Did the new product grow the category or just redistribute existing demand among existing products? The answer determines whether the launch was truly incremental or merely shifted share.

**Data requirements**: sku_id, date, quantity, category.

**Implementation approach**: Compare total category daily volume in the period before the new product's introduction to the period after. If category growth is approximately zero and the new product has captured significant share, this indicates pure cannibalization — existing products lost what the new product gained. If category growth is positive and exceeds the new product's contribution, the launch was at least partially incremental. Statistical testing on the before/after difference (e.g., Welch's t-test on daily volumes) provides rigor.

**Business output**: A cannibalization vs. incrementality verdict per new product launch. Quantified category growth attributable to the new product vs. share redistribution from existing products.

**Implementation**: see `scripts/product-catalog/rw-18-cannibalization-detection.py`

**Confidence labeling**:
- **CONFIRMED**: Both the before and after periods have 30 or more days and the growth difference is statistically significant.
- **QUALIFIED**: Shorter observation windows reduce certainty.

---

## RW-20. Category Role Classification

**Business problem**: Which categories drive store traffic vs. generate margin? The answer determines pricing strategy — traffic drivers tolerate thin margins for volume, while margin generators should not be discounted aggressively.

**Data requirements**: transaction_id, category, margin_pct (or enough to compute it).

**Implementation approach**: Compute two metrics per category: penetration (the share of total transactions that contain the category) and median margin percentage. Derive role boundaries from the joint distribution using quartiles rather than fixed thresholds. Assign roles: traffic_driver (high penetration, low margin), margin_generator (low penetration, high margin), core_strategic (high penetration, high margin), and convenience (low penetration, low margin). Separately flag seasonal categories by computing the coefficient of variation of monthly penetration — a high CV indicates seasonal traffic patterns requiring time-specific management.

**Business output**: A category role map with pricing and promotion implications per role. Seasonal flags for categories requiring time-aware strategies.

**Implementation**: see `scripts/product-catalog/rw-20-category-role-classification.py`

**Confidence labeling**:
- **CONFIRMED**: Based on 12 or more months of data covering a full seasonal cycle.
- **QUALIFIED**: Based on 6 to 12 months — seasonal roles may be misclassified.
