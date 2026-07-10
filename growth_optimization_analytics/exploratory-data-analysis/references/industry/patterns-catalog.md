# Patterns Catalog — Navigation Index

## A — Pattern Index

**Tier legend:** `floor` = mandatory consideration for any engagement where data requirements are met; `ext` = extension pattern, apply when the floor patterns are complete and time allows.

| ID | Name | Domain File | Data Req. | Sector | Tier |
|----|------|-------------|-----------|--------|------|
| OR-3 | Shopping Mission Type | customer-behavior | txn | universal | floor |
| OR-4 | Lifecycle Reorder Trajectory | customer-behavior | txn+cid | repeat-purch | floor |
| OR-5 | Basket Composition Mode Dist. | customer-behavior | txn+cid | repeat-purch | ext |
| OR-6 | Personal Ordering Cadence | customer-behavior | txn+cid+dt | repeat-purch | floor |
| OR-15 | Temporal Basket Size Variation | customer-behavior | txn+dt | universal | ext |
| OR-20 | Segment-Conditional Strategy | customer-behavior | txn+cid | repeat-purch | floor |
| RW-3 | B2B/B2C Customer Detection | customer-behavior | txn | wholesale, phys-retail | floor |
| RW-4 | RFM Segmentation | customer-behavior | txn+cid+dt | repeat-purch, b2b | floor |
| RW-10 | B2B Account Health Scoring | customer-behavior | txn+cid+dt | b2b | ext |
| RW-16 | Customer Basket Migration | customer-behavior | txn+cid+dt | repeat-purch | ext |
| RW-19 | Payment Behavior Scoring | customer-behavior | txn+cid+dt | b2b | ext |
| OR-1 | Traffic vs Retention Engine | product-catalog | txn+cid | repeat-purch | floor |
| OR-2 | Anchor Product Basket Premium | product-catalog | txn+cid | repeat-purch | floor |
| OR-10 | Category Behavioral Tier | product-catalog | txn | universal | floor |
| OR-11 | Universal Staple ID | product-catalog | txn+cid | repeat-purch | floor |
| OR-13 | High-Vol Low-Loyalty Quadrant | product-catalog | txn | universal | ext |
| OR-14 | Premium Product Loyalty Test | product-catalog | txn+cid | repeat-purch | ext |
| OR-16 | Core Catalog Overlap | product-catalog | txn+cid | repeat-purch | ext |
| OR-17 | New-Product Trial Tracking | product-catalog | txn+cid | repeat-purch | ext |
| OR-18 | Aisle Co-occurrence Affinity | product-catalog | txn | universal | ext |
| OR-21 | Product Lifecycle Stage | product-catalog | txn+cid | repeat-purch | ext |
| RW-1 | ABC/XYZ Inventory Class. | product-catalog | txn+cost | universal | floor |
| RW-2 | Market Basket Analysis | product-catalog | txn | universal | floor |
| RW-15 | SKU Velocity Decay | product-catalog | txn+dt | universal | ext |
| RW-18 | Cannibalization Detection | product-catalog | txn+dt | universal | ext |
| RW-20 | Category Role Classification | product-catalog | txn+cost | phys-retail, wholesale | ext |
| OR-7 | Cart Sequence Zone Profiling | cart-temporal | txn+cart-seq | online-retail | floor |
| OR-8 | Intervention Window Optim. | cart-temporal | txn+dt | repeat-purch | ext |
| OR-9 | Time-of-Day Vol vs Comp. | cart-temporal | txn+dt | universal | ext |
| OR-19 | Reorder Interval Spike | cart-temporal | txn+cid+dt | repeat-purch | ext |
| RW-7 | Demand Pattern Analysis | cart-temporal | txn+dt | universal | floor |
| RW-13 | Promotional Effectiveness | cart-temporal | txn+dt | phys-retail, wholesale | ext |
| RW-21 | Traffic×Basket DOW Decomp. | cart-temporal | txn+dt | universal | floor |
| RW-6 | Shrinkage & Anomaly Detect. | operational | txn+dt | phys-retail | ext |
| RW-8 | Gross Margin Analysis | operational | txn+cost | universal | floor |
| RW-9 | Intermittent Demand Forecast | operational | txn+dt | universal | ext |
| RW-11 | Working Capital / Cash Conv. | operational | txn+cost+dt | wholesale, b2b | ext |
| RW-12 | Supplier Scorecard | operational | txn+cost | b2b | ext |
| RW-14 | Cross-Branch Benchmarking | operational | txn+cost | phys-retail | ext |
| OR-22 | Operational-Factor Revenue Regression | operational | txn+cost | phys-retail | ext |
| RW-22 | Promotional Saturation Diagnostic | operational | txn+dt | universal | ext |
| OR-12 | Feature Cross-Corr / Simpson | statistical-methods | any | universal | floor |
| P1 | Subset Fingerprinting | statistical-methods | any | universal | ext |
| P2 | Cohort-Relative Scoring | statistical-methods | any | universal | ext |
| P3 | Pre/Post Event Split | statistical-methods | any | universal | ext |
| P4 | Both-Parties-Above-Average | statistical-methods | any | universal | ext |
| P5 | Three-Screen Scouting List | statistical-methods | any | universal | ext |
| P6 | Commercially Significant Test | statistical-methods | any | universal | floor |
| P7 | Data-Derived Segmentation | statistical-methods | any | universal | floor |

## B — Engagement Loading Guide

| Engagement Type | Files to Load | ~Tokens |
|-----------------|---------------|---------|
| Online grocery / e-commerce | customer-behavior, product-catalog, cart-temporal, statistical-methods | 8,000 |
| Wholesale distributor (B2B/B2C mixed) | customer-behavior, product-catalog, operational, statistical-methods | 9,000 |
| Physical supermarket | customer-behavior, product-catalog, cart-temporal, operational | 9,500 |
| B2B manufacturer | customer-behavior, operational, statistical-methods | 6,500 |
| Construction materials dist. | product-catalog, operational, statistical-methods | 7,000 |
| Logistics operator | operational, statistical-methods | 4,500 |
| General repeat-purchase client | customer-behavior, product-catalog, statistical-methods | 7,500 |

Load statistical-methods.md for any engagement involving hypothesis testing or correlation analysis.

## C — Sector Context

**Wholesale Distributors & Cash-and-Carry.** B2B/B2C mixed, 3500+ SKUs, thin margins. Priority: ABC/XYZ, Market Basket, RFM. Key files: customer-behavior, product-catalog, operational.

**Supermarkets & Food Retail.** High-volume, low-margin, perishables, loyalty data. Priority: Category Management, Shrinkage, Demand Forecasting. Key files: product-catalog, cart-temporal, operational.

**Construction Materials.** Project-driven B2B, credit sales, seasonal. Priority: Project demand clustering, Credit risk, Margin analysis. Key files: customer-behavior, operational.

**Plastics/Packaging Manufacturers.** B2B, raw material cost sensitivity, MOQ-driven. Priority: Cost pass-through, Customer concentration, Quality cost. Key files: operational, product-catalog.

**Food Manufacturing.** Perishable inputs, batch production, regulatory. Priority: Batch yield, Shelf life, Demand planning. Key files: operational, product-catalog.

**Logistics & Freight.** Asset-heavy, route-based, fuel cost. Priority: Route optimization, Fleet utilization, Customer profitability. Key files: operational.

**Online Retail & E-Commerce.** Full user identity, cart sequence, recommendation confounding. Priority: Lifecycle trajectory, Mission type, Anchor products. Key files: customer-behavior, product-catalog, cart-temporal.
