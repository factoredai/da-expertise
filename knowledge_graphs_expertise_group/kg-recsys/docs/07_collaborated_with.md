# Loading `COLLABORATED_WITH` Edges

The first **derived** relationship in the graph. Every edge before this point — `:RATED`, `:IN_GENRE`, `:DIRECTED_BY`, `:FEATURES_ACTOR`, `:HAS_OCCUPATION`, `:HAS_GENDER` — was loaded from a source file. `:COLLABORATED_WITH` is different: it's *computed from the graph itself* via a single Cypher query.

Reference notebook: [`notebooks/07_collaborated_with.ipynb`](../notebooks/07_collaborated_with.ipynb).

---

## What This Step Produces

| Element | Source | Expected count |
|---|---|---|
| `(:Actor)-[:COLLABORATED_WITH {movie_count}]->(:Actor)` | derived from `:FEATURES_ACTOR` | ~30,000–60,000 |

The count is approximate — it depends on how cast lists overlap across the 1,664 movies in the graph. After this notebook runs cleanly, the AuraDB instance should report **7 relationship types** in the summary (the 6 from prior steps + this one).

---

## What's Different About Derived Edges

Three things that didn't apply to 04, 05, or 06:

1. **`etl.py` doesn't grow.** No source file to parse. No reader function. The "reader" is a Cypher pattern.
2. **No node loading.** Both endpoints (`:Actor`) already exist from T-10; this step only adds edges.
3. **The graph is the input.** The compute query reads `:FEATURES_ACTOR` from the live database and writes `:COLLABORATED_WITH` back. The dependency direction is graph → graph, not file → graph.

This is the conceptual shift the KG story is built around: **the graph can compute its own derivations.** SQL can do this too (with self-joins), but at scale it gets ugly fast. In Cypher, a derivation is a pattern — usually three or four lines.

---

## Scope Decisions

Four decisions worth recording, settled during scoping.

- **Canonical single direction, not both.** Each pair gets one edge, with the alphabetically-smaller actor's name on the left (`WHERE a1.name < a2.name`). Halves storage; halves node degree; enforces a convention by the data itself. The arrow direction is *semantically meaningless* — collaboration is symmetric, so queries always use undirected match `-[:COLLABORATED_WITH]-`.
- **Store `movie_count` as a property.** Two actors with 5 shared films should not look identical to two with 1. The property is set as an integer via `SET r.movie_count = count(m)`. Without it, the materialized edge barely earns its keep over a per-query traversal.
- **No threshold at load time.** All co-appearances kept, even `movie_count = 1`. Filtering belongs at query/visualization time, not at load — easier to throw data away later than to recover it.
- **Pure Cypher, server-side.** One query, no Python compute. This is the pedagogical heart of the step — the graph computes from itself.

Scope inherited from `:FEATURES_ACTOR`: each movie carries at most 10 cast members in our graph (TMDB top-billed). So `:COLLABORATED_WITH` reflects **top-10-billing co-appearances only**. Two actors who were both in *Forrest Gump* but neither was top-10 billed will not get an edge. This is a data-scope decision baked in at T-10/T-11, not a flaw of this step.

---

## The Compute + Load Pattern

```cypher
MATCH (a1:Actor)<-[:FEATURES_ACTOR]-(m:Movie)-[:FEATURES_ACTOR]->(a2:Actor)
WHERE a1.name < a2.name
WITH a1, a2, count(m) AS movie_count
MERGE (a1)-[r:COLLABORATED_WITH]->(a2)
SET r.movie_count = movie_count
```

Five lines, four mechanics:

### 1. `MATCH` — the two-hop pattern

```cypher
MATCH (a1:Actor)<-[:FEATURES_ACTOR]-(m:Movie)-[:FEATURES_ACTOR]->(a2:Actor)
```

Read this left-to-right: *find an Actor `a1`, traverse backwards to a Movie `m` that features them, then forwards to a second Actor `a2` that the same movie features.* The pattern produces one row per (a1, m, a2) triple. If two actors share three movies, that's three rows — that's why we aggregate next.

Cypher's pattern matching has a built-in rule worth knowing: within a single pattern, no two relationship instances can bind to the same edge. That means `a1 = a2` is impossible — you'd need the same `:FEATURES_ACTOR` edge twice. So no self-loops, no extra `WHERE a1 <> a2` needed.

### 2. `WHERE a1.name < a2.name` — canonical ordering

```cypher
WHERE a1.name < a2.name
```

Without this, every pair would appear twice (once as (Hanks, Allen), once as (Allen, Hanks)) — and both would write an edge, giving us two redundant edges per real pair. The string comparison `<` is strict, so equal names are excluded (they couldn't match anyway, since `actor_name` is unique).

### 3. `WITH ... count(m)` — aggregation

```cypher
WITH a1, a2, count(m) AS movie_count
```

Cypher's `WITH` is *part pipeline operator, part SQL `GROUP BY`*. Here it groups by the (a1, a2) tuple and counts how many distinct movies they share. After this clause, one row per pair — not per (pair, movie) triple.

### 4. `MERGE` + `SET` — write the edge with its count

```cypher
MERGE (a1)-[r:COLLABORATED_WITH]->(a2)
SET r.movie_count = movie_count
```

`MERGE` matches an existing edge or creates one (same idempotency guarantee as 04/05/06). `SET` then writes the count. Re-running this notebook *overwrites* `movie_count` — so if cast data ever changes, counts refresh correctly with no stale values.

---

## The MERGE Gotcha (Important)

The natural temptation:

```cypher
MERGE (a1)-[r:COLLABORATED_WITH {movie_count: movie_count}]->(a2)   -- WRONG
```

This is a **bug.** `MERGE` matches on the *entire pattern, including properties*. So:

- First run: no edge exists → MERGE creates `(a1)-[:COLLABORATED_WITH {movie_count: 3}]->(a2)`. Fine.
- Second run with updated data: count is now 4 → MERGE looks for an edge with `{movie_count: 4}`, doesn't find one, and **creates a second edge**. Now there are two `COLLABORATED_WITH` edges between the same pair, with counts 3 and 4. Subsequent queries return both.

The correct idiom — used in our query — is **`MERGE` on labels + direction only, then `SET` the property separately**. `MERGE` matches the existing edge regardless of its property value, and `SET` overwrites the count.

This is the most common Neo4j gotcha for newcomers. Internalize it now and you'll save hours of "why are my edge counts doubling on each re-run."

For finer control there are also `ON CREATE SET` (writes only on creation) and `ON MATCH SET` (writes only when matched). For our case we want the count refreshed every time, so plain `SET` is right.

---

## Heads-up: Prolific Actors Become Super-Hubs

Same fan-out pattern we saw with `:Gender` in T-12, but milder. An actor who appeared in many ml-100k movies (Samuel L. Jackson, Gene Hackman, Robert De Niro) will have hundreds of `:COLLABORATED_WITH` edges. Tom Hanks, with fewer films in the dataset, will have a more modest 20–40.

For our query patterns this is fine — we always start from a specific actor and traverse outward. But it's worth knowing for two reasons:

1. **Visualization will struggle.** If you try to render the full `:COLLABORATED_WITH` subgraph in pyvis without filtering, your browser will hang. The Streamlit demo should filter at query time, e.g. `WHERE r.movie_count >= 3` or `LIMIT 200`. That's the right place for the filter — it can be tuned per panel, while a load-time threshold would be baked in forever.
2. **Cardinality intuitions don't transfer from `:RATED`.** A user has ~106 `:RATED` edges. A prolific actor might have 150 `:COLLABORATED_WITH` edges. Both look like "person-node-with-many-out-edges" in the graph, but the semantics are very different.

---

## Verification

After running the compute cell, the summary should report:

| Relationship | Count |
|---|---|
| `RATED` | 100,000 |
| `FEATURES_ACTOR` | ~16,000 |
| `IN_GENRE` | ~3,000 |
| `DIRECTED_BY` | ~1,700–2,000 |
| `HAS_OCCUPATION` | 943 |
| `HAS_GENDER` | 943 |
| `COLLABORATED_WITH` | ~30,000–60,000 |

The exact `COLLABORATED_WITH` count is data-dependent — it'll be whatever falls out of the cast-list overlap. As long as it's in the right order of magnitude (tens of thousands, not millions or hundreds), you're fine.

### Proving idempotency

Same drill as 04/05/06: **run the summary once, re-run the compute cell, run the summary again.** All counts identical. That's `MERGE` + `SET` doing their job.

If you ever see the `COLLABORATED_WITH` count doubling on re-run — congratulations, you've reproduced the MERGE gotcha. Check whether the property is inlined in MERGE vs. set separately.

---

## The Spot-Check Queries

### Spot-check 1 — Top 10 collaborator pairs by `movie_count`

```cypher
MATCH (a1:Actor)-[r:COLLABORATED_WITH]-(a2:Actor)
WHERE a1.name < a2.name
RETURN a1.name AS actor1, a2.name AS actor2, r.movie_count AS shared_movies
ORDER BY shared_movies DESC LIMIT 10
```

The undirected match `-[r:COLLABORATED_WITH]-` matches both binding orientations of the edge; the `WHERE` filter dedups to one row per pair (without it, every pair appears twice).

**Sanity check the results.** Expect repeat-pairing actors from the 1988–1998 era — Hanks/Ryan, Pacino/De Niro, Marin/Cheech, the Scorsese regulars. If the top result is two unknown actors with `movie_count = 1`, something's gone wrong: probably a duplicate-edge bug (MERGE gotcha) or unexpected data.

### Spot-check 2 — Tom Hanks's top collaborators

```cypher
MATCH (target:Actor {name: "Tom Hanks"})-[r:COLLABORATED_WITH]-(other:Actor)
RETURN other.name AS collaborator, r.movie_count AS shared_movies
ORDER BY shared_movies DESC LIMIT 10
```

A "from a known actor" lookup — the canonical recommendation-query shape. Tom Hanks is a recognizable middle: prolific enough in ml-100k's era to have substantial collaborator counts (Big, Forrest Gump, Apollo 13, Toy Story, Sleepless in Seattle, Philadelphia, A League of Their Own, You've Got Mail), but not a fan-out monster like a Hollywood character actor.

If the query returns empty, Tom Hanks isn't in the graph — pick another well-known actor and re-run.

### Spot-check 3 — Triangle test (3 mutual collaborators)

```cypher
MATCH (a:Actor)-[:COLLABORATED_WITH]-(b:Actor)-[:COLLABORATED_WITH]-(c:Actor)-[:COLLABORATED_WITH]-(a:Actor)
WHERE a.name < b.name AND b.name < c.name
RETURN a.name AS actor_a, b.name AS actor_b, c.name AS actor_c LIMIT 10
```

**This is the pedagogically strongest query in the notebook** — three actors who have *all* worked with each other. A↔B, B↔C, A↔C.

In SQL, this is three self-joins on a movie_cast table with `WHERE a.id < b.id AND b.id < c.id` to trim the 6 permutations per triangle. Verbose, slow, hard to read. The query planner has to materialize three intermediate joins.

In Cypher, it's one pattern: traverse the triangle. The same `<` chain trims to unique triples. **This is what "graphs make hard queries easy" actually looks like** — not magic, just a pattern language that matches the shape of the data.

---

## What's Not in This Step

| Out of scope | Why |
|---|---|
| Director-director collaborations | Directors rarely co-direct; the edge would be very sparse |
| Director-actor collaborations (the "Scorsese → De Niro" pattern) | Interesting, but not in the schema. Worth its own discussion if you want it later |
| `:SIMILAR_TO` between movies | Dropped from project scope — the multi-hop queries it would precompute can be expressed at query time via `:IN_GENRE` / `:FEATURES_ACTOR` traversals. Keeping it would contradict the "graph traversal replaces precomputed similarity" teaching point |

---

## Quick Sanity Check Before Running

If something errors on first run, it's almost always one of these:

1. **T-11 not loaded.** The compute query depends on `:FEATURES_ACTOR` edges — run [`05_load_relationships.ipynb`](../notebooks/05_load_relationships.ipynb) first.
2. **`:Actor` nodes missing.** Same — depends on T-10's `04_load_nodes.ipynb`.
3. **Edge count doubles on re-run.** You hit the MERGE gotcha. Check whether `movie_count` is inlined in MERGE (wrong) vs. written via separate `SET` (correct).
4. **AuraDB instance paused.** Free-tier instances auto-pause; resume from [console.neo4j.io](https://console.neo4j.io).
