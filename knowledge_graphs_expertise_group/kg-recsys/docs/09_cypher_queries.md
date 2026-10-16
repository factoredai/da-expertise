# Cypher 101 — Querying the Movie Graph

The bridge between data engineering and the recommender layer. With the graph loaded (notebooks 03 → 07) and verified (notebook 08), this notebook walks a reader from zero Cypher to a query that pulls everything together — without depending on any recommender code.

Reference notebook: [`notebooks/09_cypher_queries.ipynb`](../notebooks/09_cypher_queries.ipynb).

---

## What This Notebook Teaches

Six sections, each introducing one Cypher clause or shape, building strictly on the previous.

| # | Section | New concept introduced |
|---|---|---|
| 1 | **MATCH** | Pattern matching — single-node, then node-edge-node, with inline property filters and arrow direction. |
| 2 | **WHERE** | Filtering beyond inline equality — comparisons, ranges, edge-property filters. |
| 3 | **RETURN** | Projection, `AS` aliases, `ORDER BY`, `LIMIT` — and why aliasing matters for downstream Python. |
| 4 | **WITH** | The pipeline operator — filter on aggregates (SQL `HAVING` analog), `count()` vs. `collect()`. |
| 5 | **Multi-hop traversals** | Three shapes (Collaborative, Content via shared actor, 3-hop genre), plus **relationship uniqueness** as a Cypher-specific behavior. |
| 6 | **Putting it together** | One query that touches `MATCH`, `WHERE`, `WITH` (two aggregates), filter-on-aggregate, `RETURN`, `ORDER BY`, `LIMIT`. |

Section 5 is the load-bearing one — it's where the graph model earns its keep versus tabular and where a real Cypher behavior (relationship uniqueness) surfaces.

---

## Scope Decisions

A few choices worth recording.

- **Recurring anchors, not isolated examples.** Every section reuses the same four anchors — `Toy Story` (`movieId = 1`), `Tom Hanks`, `user 196`, and `Comedy`. A reader who sees Toy Story in §1 and again in §5 can compare what changed in the *query*, not the *data*. The Shape 2 cell in §5 is the clearest payoff: Toy Story → Tom Hanks → his other films wires both recurring anchors into one query.
- **`OPTIONAL MATCH`, `UNION`, `CALL` are deliberately out.** They're useful, but every additional clause raises the bar to "Cypher 102." The notebook's scope is *exactly* what a reader needs to read the recommender queries that arrive in T-19 onward — nothing more.
- **No SQL contrast in this notebook.** The "graph beats SQL on multi-hop" lesson is real, but it deserves its own focused write-up rather than being interleaved here. That contrast lands in T-16 ([`docs/10_sql_vs_cypher.md`](10_sql_vs_cypher.md)). This notebook stays single-language — Cypher all the way down.
- **§5 Shape 1 is a relationship-uniqueness lesson, not a "spot the bug."** The original draft framed the cell as *"this query has a self-match bug — find it."* Running the query showed no self-match — because Cypher's relationship uniqueness already prevents two anonymous edge slots in a single `MATCH` from binding to the same physical edge. Instead of moving the bug to a different shape, the cell now teaches the protection itself, with the caveat that it doesn't generalize to longer paths where the relationship slots are guaranteed distinct.
- **Read-only — no writes.** No `CREATE`, `MERGE`, or `DELETE` anywhere. Writes are taught implicitly in notebooks 04 → 07 (where they're load-bearing) and don't need a parallel walkthrough.
- **Soft output, no asserts.** Same policy as notebook 08. Every cell prints what it found rather than raising on unexpected output — the notebook is a teaching artifact, not a test.

---

## What's In vs. What's Out

| In scope | Out of scope | Where it lands |
|---|---|---|
| `MATCH`, `WHERE`, `RETURN`, `WITH`, `ORDER BY`, `LIMIT`, `DISTINCT` | `OPTIONAL MATCH`, `UNION`, `CALL`, subqueries (`CALL { ... }`) | Future notebook or out of project scope |
| Aggregates: `count()`, `collect()`, `avg()` | `sum()`, `min()`, `max()`, `percentileCont()`, list comprehensions | Recommender notebooks if needed (T-19+) |
| Multi-hop traversal (2-hop and 3-hop) | Variable-length paths (`*1..3`), shortest path | Not needed for the four recommender strategies |
| Relationship uniqueness as Cypher behavior | Node isomorphism (separate concept; rarely a beginner trap) | Out of scope for 101 |
| Recurring-anchor walkthrough | SQL-vs-Cypher side-by-side comparison | **T-16** ([`docs/10_sql_vs_cypher.md`](10_sql_vs_cypher.md)) |
| Read queries | Write queries (`CREATE`, `MERGE`, `DELETE`) | Notebooks 04 → 07 |
| Cypher style conventions (uppercase keywords, PascalCase labels) | `EXPLAIN` / `PROFILE`, query performance | Notebook 08 §5 (index in action); deeper perf is out of project scope |

---

## Quick Sanity Check Before Running

If a cell errors on first run, it's almost always one of these:

1. **Notebooks 03 → 07 haven't been run against the current AuraDB instance.** Section 1's `Toy Story (movieId = 1)` query returns nothing — no data is loaded. Re-run the load notebooks.
2. **AuraDB instance paused.** Free-tier instances auto-pause; resume from [console.neo4j.io](https://console.neo4j.io).
3. **`.env` missing or stale.** `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` must point to the live instance.
4. **TMDB enrichment partial.** Section 5 Shape 2 anchors on Toy Story's actors via `:FEATURES_ACTOR`. If TMDB enrichment didn't run for movieId = 1, that cell returns nothing while the rest of the notebook works.
