# End-to-End Verification

The final step before moving from data engineering to the recommender layer: run every check that proves the load pipeline (notebooks 03 → 07) produced the graph the schema promised.

Reference notebook: [`notebooks/08_verification.ipynb`](../notebooks/08_verification.ipynb).

---

## What This Notebook Checks

Five sections, each catching a different class of bug a different way.

| # | Section | Catches |
|---|---|---|
| 1 | **Schema artifacts (live)** | A constraint or index that was supposed to land in T-09 didn't actually get created. |
| 2 | **Node counts** | A loader silently dropped rows — e.g. `:Movie` is 1,640 instead of 1,682 because a parse step failed. |
| 3 | **Edge counts** | An edge type is short on rows — same shape of bug as #2 but on the relationships. |
| 4 | **Structural invariants** | Wrong cardinality, NULL property, illegal self-loop, out-of-range value — bugs that pure counts can't see. |
| 5 | **Index in action** (`EXPLAIN`) | The fulltext index exists in the catalog but isn't being used at query time — usually an index-name typo or a stale procedure call. |

Sections 1 + 5 together close out **T-13** (constraints and indexes verified at runtime). Sections 2 + 3 + 4 are the substance of **T-14**.

---

## Scope Decisions

A few choices worth recording.

- **Soft prints, not asserts.** Every cell prints *actual vs. expected* side by side instead of raising on mismatch. Two reasons: (1) the notebook is read as a teaching artifact — seeing all results, including the OK ones, is more informative than stopping at the first mismatch; (2) several counts are *expected ranges*, not exact values (see below) — a hard assert would force us to pick a single number and lie about the rest.
- **Expected counts are typed.** Three of the seven node labels (`User`, `Genre`, `Occupation`, `Gender`) are **exact** because they're fixed by the MovieLens schema. Three (`Movie`, `Actor`, `Director`) are **ranges** because TMDB match coverage and the top-10-billing cap on actors introduce variability. The verification code makes the distinction explicit so the reader knows which mismatches matter most.
- **`RATED = 100,000` is the load-quality anchor.** This count is exact, simple to verify, and tied to a single file (`u.data`). If it's off by even one, every average-rating aggregation downstream is wrong. Section 3 flags this as the most consequential exact check.
- **`COLLABORATED_WITH` is range-checked despite being derived from a deterministic query.** The query result is exact at a given snapshot, but the count drifts if `:FEATURES_ACTOR` changes upstream (e.g. a TMDB refresh adds new cast). Range-checking insulates the verification notebook from future re-loads.
- **No `assert` in any cell** — the closest thing is the "OK" / "MISMATCH" label printed next to each row. A future test-runner can grep for "MISMATCH" if a CI hookup is added later.

---

## The Five Sections — Why Each Matters

### Section 1 — Schema artifacts (live)

`SHOW CONSTRAINTS` and `SHOW INDEXES` walk the AuraDB instance and report what's actually there. The expected outcome — **7 uniqueness constraints + 8 indexes** (7 backing + 1 fulltext) — is fully determined by notebook 03 §6. This section is the *runtime* half of the T-13 audit trail; the *design-time* half lives in [`docs/03_schema_diagram.md`](03_schema_diagram.md#schema-artifacts).

If something is missing here, the most common cause is that notebook 03 didn't run cleanly against the current AuraDB instance — re-run its schema cell.

### Section 2 — Node counts

The simplest integrity check: count nodes per label. Exact counts (`User=943`, `Genre=19`, `Occupation=21`, `Gender=2`) are bound directly to source-file row counts. Range counts (`Movie`, `Actor`, `Director`) accommodate TMDB match coverage and the top-10/movie cap.

A mismatch in an exact count is a silent data-loss bug — a row was dropped without a load error. Worth a `git log` on `src/etl.py` and the relevant load notebook.

### Section 3 — Edge counts

Same shape as Section 2, on relationships. `RATED=100,000` and the two `HAS_*=943` rows are the exact anchors — they should match byte-for-byte. The non-exact rows are sanity-bracketed.

### Section 4 — Structural invariants

Four bug classes that pure counts miss:

1. **Wrong cardinality** — every `:User` should have exactly 1 `:HAS_OCCUPATION` and 1 `:HAS_GENDER`. A user with 0 or 2 of either silently breaks cold-start (CQ-2.4) without changing the *total* edge count.
2. **NULL property** — a movie with a NULL title would never appear in fulltext search and would render blank in the UI.
3. **Illegal self-loop** — the `a1.name < a2.name` filter in T-12 precludes `:COLLABORATED_WITH (a)-(a)` by construction. A non-zero count here would mean the filter was bypassed somewhere.
4. **Out-of-range value** — MovieLens ratings are integers 1–5. Any value outside that range skews every average-rating aggregation.

Each invariant is one Cypher query that should return `0`. The output is a single number.

### Section 5 — Index in action (`EXPLAIN`)

A fulltext-search query against `movie_title_search` for the token `"toy"`. Expected behavior: returns *Toy Story*, *Toy Story 2*, and similar titles via the index. This proves the index is wired up — Section 1 only proves it *exists*, not that it actually serves queries.

If Section 5 returns no hits but Section 1 shows the index present, the index is likely populated but the procedure call is mistyped.

---

## What "Clean" Looks Like

| Section | Clean output |
|---|---|
| 1a | 7 constraints listed, all `UNIQUENESS` |
| 1b | 8 indexes listed — 7 `RANGE` (backing) + 1 `FULLTEXT` named `movie_title_search` |
| 2 | All 7 labels print `OK` |
| 3 | All 7 relationship types print `OK` |
| 4 | All four invariants print `0` violations |
| 5 | Five *Toy Story*-family titles printed with descending scores |

If every section is clean, the data engineering side of the project is done and the recommender layer (T-15 onward) can build on a verified foundation.

---

## What's Not in This Step

| Out of scope | Lands in |
|---|---|
| Query-performance benchmarking (latency budgets, EXPLAIN PROFILE on recommender queries) | T-15+ once the recommender queries exist |
| Data-distribution audits (rating histograms, genre balance, etc.) | Out of project scope — not a graph integrity question |
| Cross-source consistency checks (e.g. every MovieLens user-id in `u.data` exists in `u.user`) | Should be enforced at load time (T-10/T-11), not as a verification step |
| Constraint enforcement smoke test (attempt a duplicate `MERGE`, expect failure) | Considered and skipped — Section 1 already proves the constraint exists; duplicating the test in writeable form adds noise without new signal |
| Manual Browser visual inspection of subgraph shape (T-18) | Covered transitively by notebooks 09 + 10 — every recurring-anchor query uses explicit directional patterns (`(u)-[:RATED]->(m)`, `(m)-[:FEATURES_ACTOR]->(a)`) and would return zero rows if direction or reference-node wiring were wrong. Notebook 09 §5 also programmatically asserts Tom Hanks's known co-films — a stronger shape check than eyeballing. Manual inspection would add an "I looked" audit-trail without unique bug-detection signal. |

---

## Quick Sanity Check Before Running

If something errors on first run, it's almost always one of these:

1. **Notebook 03 hasn't been applied to the current AuraDB instance.** Re-run its schema cell.
2. **AuraDB instance paused.** Free-tier instances auto-pause; resume from [console.neo4j.io](https://console.neo4j.io).
3. **`.env` missing or stale.** `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` must point to the live instance.
4. **You're running against a different instance than 04–07 loaded into.** Section 1 will look clean; Sections 2–3 will be all zeros.
