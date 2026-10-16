# SQL vs Cypher — Side-by-Side

The teaching moment named in [`CLAUDE.md`](../CLAUDE.md#teaching-moments--preserve-these) — *SQL JOIN explosion vs. a simple Cypher multi-hop traversal* — made executable. Six paired examples: real SQL on in-memory SQLite, real Cypher on the live AuraDB instance, same dataset, same answers, side by side.

Reference notebook: [`notebooks/10_sql_vs_cypher.ipynb`](../notebooks/10_sql_vs_cypher.ipynb).

---

## What This Notebook Demonstrates

Six paired examples, escalating from a trivial baseline to the canonical "easy in graph, brutal in SQL" payoff. Each example is a `(markdown question → SQL cell → Cypher cell)` triplet. The reader compares line count, JOIN count vs. hop count, and what each side handles cleanly.

| # | Example | SQL | Cypher | What it shows |
|---|---|---|---|---|
| 1 | Movies in genre "Comedy" | 1 JOIN | 1 hop | Baseline — for shallow questions, both sides are roughly equally clean. |
| 2 | Other movies featuring Toy Story's actors | 3 JOINs | 2 hops | First gap — SQL needs a bridge table per hop. |
| 3 | Users who rated the same movies as user 196 | self-join + `<>` filter | 2 hops + relationship uniqueness | Where Cypher's relationship-uniqueness rule (notebook 09 §5 Shape 1) saves a `WHERE` clause. |
| 4 | Movies in genres user 196 already rated | 4 JOINs + `NOT IN` | 3 hops + `NOT` pattern predicate | Gap widens; the "exclude already-rated" clause looks different on each side. |
| 5 | Explainable rec: "you rated Toy Story 5★ → Tom Hanks → Apollo 13" | `\|\|` string concat across 4 JOINed rows | path-object projection with `[r]` binding | The [`CLAUDE.md`](../CLAUDE.md#recommendation-strategies) explainability path — graph side is a direct projection, SQL side is glued-together strings. |
| 6 | Triangle: 3 actors who all collaborated | CTE + 3 self-joins on collaboration relation | one triangle pattern with `:COLLABORATED_WITH` | The payoff — mirrors the triangle in [`notebooks/07_collaborated_with.ipynb`](../notebooks/07_collaborated_with.ipynb) cell-17. |

Examples 1 and 2 establish the baseline. Examples 3–5 show the gap opening. Example 6 is the punchline.

---

## Scope Decisions

A few choices worth recording.

- **Why SQLite.** Python-stdlib (`import sqlite3` — no install), in-memory (`":memory:"` — no file on disk, no cleanup), and a single-process embedded engine so the SQL side and the Cypher side don't fight for resources. The lesson is *query-shape*, not *engine choice*; SQLite removes everything that isn't query-shape from the picture.
- **Why `enriched_movies.csv` instead of re-querying Neo4j for cast/director data.** That CSV is already the TMDB-materialized form used by [`src/etl.py`](../src/etl.py) to populate Neo4j. Reusing it means both sides start from the exact same source rows, with zero round-trip cost. A "pre-materialize TMDB data" step would have added complexity without changing the lesson.
- **Why the setup cell *doesn't* `import` from `src/etl.py`.** The bridge-table normalization — `ast.literal_eval` on stringified lists, `.explode()`, `.to_sql()` — *is* part of the lesson. It's the tabular tax the graph side skips. Importing it would obscure the very work the reader is meant to see.
- **Why exactly 6 examples.** One trivial baseline (Ex 1) + four escalating cases (Ex 2–5) + one brutal payoff (Ex 6). Fewer would not show the gap opening; more would dilute it. The escalation is by hop count: 1 → 2 → 2 → 3 → 3 → triangle.
- **No perf benchmarks.** In-memory SQLite vs. networked AuraDB Free tier is apples-to-oranges — comparing latencies would teach a wrong lesson (one side wins by being local). The notebook compares *what you have to write*, not *how fast it runs*. Performance lessons live elsewhere (notebook 08 §5 for the index-in-action proof; deeper perf work is out of project scope).
- **Soft prints, no asserts.** Same policy as notebooks 08 and 09. Each cell prints what it found rather than raising on mismatch — readability over CI-friendliness.
- **Example 3's asymmetry is a feature.** SQL needs `WHERE u1.userId <> u2.userId`; Cypher omits it because relationship uniqueness handles it for free. The markdown explicitly ties this back to [`docs/09_cypher_queries.md`](09_cypher_queries.md) §5 Shape 1 so the reader recognizes the lesson, not a bug.

---

## What's In vs. What's Out

| In scope | Out of scope | Where it lands |
|---|---|---|
| 6 paired SQL ↔ Cypher examples, escalating by hop count | Cypher-only or SQL-only examples | Notebook 09 (Cypher 101), recommender notebooks (T-19+) |
| In-memory SQLite as the SQL backend | Postgres, DuckDB, or any disk-resident engine | Out of project scope — engine choice is not the lesson |
| Bridge-table normalization as part of the setup cell | Importing from `src/etl.py` to hide the normalization | Deliberately rejected — see scope decisions |
| Explainability path comparison (Ex 5) | Recommender-level explainability (multi-signal weighting) | T-19+ recommender notebooks |
| Triangle query (Ex 6) | Variable-length paths (`*1..3`), shortest path, community detection | Not needed for the four recommender strategies |
| Soft prints with OK/MISMATCH labels | Hard `assert` cells | Same policy as notebooks 08 / 09 |
| Read-only against Neo4j and SQLite | Write-side comparison (`INSERT` vs. `MERGE`, schema DDL) | Out of scope — writes are covered implicitly in notebooks 04–07 |
| Latency observations only if they show up incidentally | Timing benchmarks, `EXPLAIN PROFILE` comparisons | Out of project scope — apples-to-oranges |

---

## Quick Sanity Check Before Running

If a cell errors on first run, it's almost always one of these:

1. **Notebooks 03 → 07 haven't been run against the current AuraDB instance.** Every Cypher cell will return empty results while the SQL side works fine — a visible mismatch in the soft-print output. Re-run the load notebooks.
2. **AuraDB instance paused.** Free-tier instances auto-pause; resume from [console.neo4j.io](https://console.neo4j.io).
3. **`.env` missing or stale.** `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` must point to the live instance.
4. **`data/enriched/enriched_movies.csv` missing.** The setup cell builds the SQLite movies/actors/directors/genres tables from this file. If TMDB enrichment (notebook 05) didn't run, the SQL side will be empty for Examples 2 and 5 and the row-count soft-verify will flag it.
5. **`data/raw/ml-100k/` missing.** The setup cell reads `u.user` (pipe-sep, `latin-1`) and `u.data` (tab-sep) directly. If the MovieLens 100K archive wasn't unpacked, the `users` and `ratings` tables will be empty and every example's user-related result will be wrong on the SQL side.

The soft-verify table printed by the setup cell — `ratings = 100,000`, `users = 943`, `movies ≈ 1,640+` — is the fastest way to spot any of the above before working through the examples.
