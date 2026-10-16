# Loading Relationships into Neo4j (T-11)

How we load every relationship type in the KG schema, idempotently, on top of the nodes loaded in T-10. This is the step that turns five disconnected piles of nodes into an actual knowledge graph.

Reference notebook: [`notebooks/05_load_relationships.ipynb`](../notebooks/05_load_relationships.ipynb).

---

## What This Step Produces

After running the notebook against an AuraDB instance that already has the T-10 nodes loaded, the database contains all four relationship types in T-11's scope.

| Relationship | Properties | Source | Expected count |
|---|---|---|---|
| `:User-[:RATED]->:Movie` | `rating` (float), `timestamp` (int) | `data/raw/ml-100k/u.data` | 100,000 |
| `:Movie-[:IN_GENRE]->:Genre` | — | `data/raw/ml-100k/u.item` (boolean cols) | ~3,000 |
| `:Movie-[:DIRECTED_BY]->:Director` | — | `data/enriched/enriched_movies.csv` (`directors`) | ~1,700–2,000 |
| `:Movie-[:FEATURES_ACTOR]->:Actor` | `billing_order` (1–10) | `data/enriched/enriched_movies.csv` (`cast`) | ~16,000 |

---

## Scope Decisions

A few calls were made up front:

- **Four edges only.** `:HAS_OCCUPATION` and `:HAS_GENDER` are in the project schema but stay deferred — they ship together with their `:Occupation` and `:Gender` node loads, in their own task, so we never leave orphans behind.
- **IN_GENRE comes from `u.item`, not from TMDB.** The 19 boolean columns in `u.item` map 1:1 to the 19 `:Genre` nodes loaded in T-10. The `genre_names` column in `enriched_movies.csv` uses TMDB's taxonomy ("Family", "Science Fiction", "Music") which doesn't line up with the ml-100k taxonomy ("Children's", "Sci-Fi", no "Music"). Mixing the two would either drop edges (taxonomy mismatch on `MATCH`) or create rogue `:Genre` nodes (under `MERGE`). Single canonical taxonomy wins.
- **`MERGE` everywhere.** Slightly slower than `CREATE`, but every load is safe to re-run and consistent with T-10. The teaching narrative ("the whole pipeline is re-runnable") matters more than the performance delta.
- **Silent skip on missing endpoints.** Movies TMDB couldn't match have `NaN` in their `directors` and `cast` cells; the reader drops those rows. Same goes for movies with an empty cast list. No warnings, no logs — the unmatched count was already surfaced in T-10.
- **RATED is chunked, the other three aren't.** 100K edges in one `UNWIND` would stress AuraDB Free's transaction limit; the other three (≤16K each) fit comfortably in a single managed transaction.

---

## The Two-Key Principle

Every endpoint has a unique key, and the load does a constraint-backed `MATCH` on both before creating the edge. The keys were established as uniqueness constraints in T-10:

| Endpoint | Unique key | Constraint name |
|---|---|---|
| `:Movie` | `movieId` | `movie_id` |
| `:User` | `userId` | `user_id` |
| `:Genre` | `name` | `genre_name` |
| `:Director` | `name` | `director_nm` |
| `:Actor` | `name` | `actor_name` |

The names *are* the keys for the categorical/person nodes — there's no separate ID. That's why we set uniqueness constraints on them in T-10; they're effectively foreign keys.

Why this matters for performance: a uniqueness constraint creates a backing index automatically. So when Cypher runs `MATCH (a:Actor {name: "Tom Hanks"})`, it does an index lookup, not a scan. At 100K RATED edges and ~16K actor edges, the difference is "seconds" vs "minutes."

---

## The Edge-Row Pattern

Each load follows the same three-step rhythm: **read → load → verify**.

The conceptual move that makes all four loads structurally identical is this:

> **Python's job is to produce edge rows — a flat DataFrame where every row represents one future edge.**
> **Cypher's job is to look up both endpoints by key and `MERGE` the edge between them.**

This means messy source shapes (boolean matrices, JSON-in-CSV lists) get cleaned up in `etl.py`, and the notebook's Cypher stays clean and almost identical across the four sections.

### Example: from `cast` column to FEATURES_ACTOR edge rows

```
movieId=1, cast=['Tom Hanks', 'Tim Allen', 'Don Rickles', ...]

      ▼  Python explode (with index → billing_order)

(movieId=1, name="Tom Hanks",   billing_order=1)
(movieId=1, name="Tim Allen",   billing_order=2)
(movieId=1, name="Don Rickles", billing_order=3)
...
```

Once the DataFrame is shaped like that, the Cypher writes itself.

---

## The Cypher Shape (Same for All Four)

Every load uses this pattern:

```cypher
UNWIND $rows AS row
MATCH (a:LabelA {keyA: row.fieldA})
MATCH (b:LabelB {keyB: row.fieldB})
MERGE (a)-[r:REL_TYPE]->(b)
SET r.prop = row.prop   -- only when the relationship has properties
```

- `UNWIND` turns the parameter list into one row per iteration.
- Both `MATCH`es hit the constraint-backed indexes — fast lookups, no scans.
- `MERGE` is idempotent: finds the edge if it exists, creates it if not.
- `SET` writes the relationship properties. For property-less edges (`IN_GENRE`, `DIRECTED_BY`) it's omitted.

The shape is identical across all four — only the labels, keys, and properties change.

---

## Per-Edge Walkthrough

### RATED (100,000 edges)

```cypher
UNWIND $rows AS row
MATCH (u:User  {userId:  row.userId})
MATCH (m:Movie {movieId: row.movieId})
MERGE (u)-[r:RATED]->(m)
SET r.rating = row.rating, r.timestamp = row.timestamp
```

`u.data` is already a flat table (`userId | movieId | rating | timestamp`), so the reader is the simplest of the four — read the TSV, cast `rating` to float, return the DataFrame.

The notable thing here is **how the load runs**, not how it's read: `run_write_query_chunked` splits the 100K rows into batches of 5,000 and sends one managed write transaction per chunk, wrapped in a `tqdm` progress bar. See "Chunked Writes" below.

### IN_GENRE (~3,000 edges)

```cypher
UNWIND $rows AS row
MATCH (m:Movie {movieId: row.movieId})
MATCH (g:Genre {name:    row.genre})
MERGE (m)-[:IN_GENRE]->(g)
```

No properties on the edge — a movie is either in a genre or it isn't. The reader's job is to turn `u.item`'s 19 boolean columns into long-form edge rows:

```
u.item row:  movieId=1, genre_0=0, genre_1=0, ..., genre_3=1, genre_4=1, genre_5=1, ...
            (cols 3, 4, 5 are Animation, Children's, Comedy)

           ▼  melt to long form, filter present==1, rename cols → names

edge rows: (movieId=1, genre="Animation")
           (movieId=1, genre="Children's")
           (movieId=1, genre="Comedy")
```

The 19 column names come from `read_genres()` — the same source of truth used to create the `:Genre` nodes in T-10. That's how we guarantee every edge has a matching `:Genre` node to attach to.

### DIRECTED_BY (~2,000 edges)

```cypher
UNWIND $rows AS row
MATCH (m:Movie    {movieId: row.movieId})
MATCH (d:Director {name:    row.name})
MERGE (m)-[:DIRECTED_BY]->(d)
```

The reader explodes the `directors` column from `enriched_movies.csv` — a CSV-encoded list parsed with `ast.literal_eval`. Most movies produce one edge; multi-director films (the Coens, the Wachowskis, anthology films) produce several. Movies TMDB couldn't match have `NaN` in the column — those rows are silently skipped.

### FEATURES_ACTOR (~16,000 edges)

```cypher
UNWIND $rows AS row
MATCH (m:Movie {movieId: row.movieId})
MATCH (a:Actor {name:    row.name})
MERGE (m)-[r:FEATURES_ACTOR]->(a)
SET r.billing_order = row.billing_order
```

Same explode pattern as directors, with one extra column. The `cast` list in `enriched_movies.csv` is already ordered by TMDB billing, so we use `enumerate(start=1)` in Python to produce `billing_order` — 1 for top billing, 2 for second, etc., up to 10. That property is what lets the future Streamlit demo show "Top 3 actors" rather than three random names.

---

## Chunked Writes — Why and How

`run_write_query_chunked` in `src/graph.py` exists for one reason: AuraDB Free's per-transaction limits. A single `UNWIND` of 100,000 rows is one transaction — if it runs long, it can time out, and there's no partial commit. Splitting into chunks gives us:

- **Smaller transactions** that comfortably finish on Free tier.
- **Progress visibility** via `tqdm` — twenty `[████░░░░] 5/20 chunks` updates beats staring at a frozen cell.
- **Graceful failure mode** — if chunk 7 fails, chunks 1-6 are committed; you can fix and re-run idempotently from where it broke.

The helper signature:

```python
run_write_query_chunked(
    cypher: str,
    rows: list[dict],
    chunk_size: int = 5000,
    param_name: str = "rows",
    desc: str = "loading",
) -> None
```

It's a thin loop over `run_write_query` — about ten lines including the docstring. Used only for RATED; the other three loads send their (smaller) row lists in a single transaction.

---

## Verification

The notebook ends with a summary cell that counts edges per type:

```cypher
MATCH ()-[r]->()
RETURN type(r) AS relationship, count(*) AS n
ORDER BY n DESC
```

On a clean load you should see roughly:

| Relationship | Count |
|---|---|
| `RATED` | 100,000 |
| `FEATURES_ACTOR` | ~16,000 |
| `IN_GENRE` | ~3,000 |
| `DIRECTED_BY` | ~1,700–2,000 |

### Proving idempotency

Same drill as T-10: **run the summary cell a second time, then re-run any load cell, then run the summary again.** All three numbers should be byte-for-byte identical. That's `MERGE` working — both for nodes (in T-10) and for relationships (here).

---

## The Spot-Check Queries (the payoff)

Two queries at the end of the notebook are the point of all this work — they show what the graph can now do that the source CSVs can't.

### Query 1 — Multi-hop traversal: a user's genre affinity

```cypher
MATCH (u:User {userId: 196})-[r:RATED]->(m:Movie)-[:IN_GENRE]->(g:Genre)
WHERE r.rating >= 4
RETURN g.name AS genre, count(*) AS high_ratings
ORDER BY high_ratings DESC LIMIT 5
```

Two hops, three lines, one traversal. In SQL this would be three JOINs (users → ratings → movies → movie_genres → genres) plus a `GROUP BY`. The graph version is closer to how you'd describe the question in English.

This is the **SQL JOIN explosion vs. Cypher multi-hop** teaching moment from the project's design goals.

### Query 2 — One-shot neighborhood: everything we know about a movie

```cypher
MATCH (m:Movie {movieId: 1})
OPTIONAL MATCH (m)-[:DIRECTED_BY]->(d:Director)
OPTIONAL MATCH (m)-[fa:FEATURES_ACTOR]->(a:Actor)
OPTIONAL MATCH (m)-[:IN_GENRE]->(g:Genre)
RETURN m.title                          AS title,
       collect(DISTINCT d.name)         AS directors,
       collect(DISTINCT a.name)[..3]    AS top_actors,
       collect(DISTINCT g.name)         AS genres
```

Director, top 3 actors, and genres — pulled in one query. `OPTIONAL MATCH` makes it robust to missing data (an unmatched movie still returns a row with empty lists). `collect(DISTINCT ...)` aggregates each neighbor type into its own list. This is the shape of query that the future recommender will produce alongside every result — the explainability path.

---

## What's Not in This Step

| Out of scope | Lands in |
|---|---|
| `:HAS_OCCUPATION`, `:HAS_GENDER` edges (with `:Occupation` / `:Gender` nodes) | The task that adds those node labels |
| Derived `:COLLABORATED_WITH` (actor co-appearance) | A later projection step |
| Derived `:SIMILAR_TO` (movie-movie similarity) | A later projection step |
| Any indexes on relationship properties (e.g. `RATED.rating`) | Not needed for current query patterns; revisit if recommendation queries get slow |

---

## Quick Sanity Check Before Running

If the load errors on the first edge cell, it's almost always one of these:

1. **T-10 nodes not loaded yet.** Every `MATCH` here assumes the endpoint node exists. Run [`04_load_nodes.ipynb`](../notebooks/04_load_nodes.ipynb) first.
2. **AuraDB instance paused.** Free-tier instances auto-pause; resume from [console.neo4j.io](https://console.neo4j.io).
3. **`.env` missing or stale.** `print(os.environ.get("NEO4J_URI"))` should return your URI, not `None`.
4. **`u.data` or `enriched_movies.csv` missing.** `u.data` ships with ml-100k; `enriched_movies.csv` is produced by [`02_tmdb_enrichment.ipynb`](../notebooks/02_tmdb_enrichment.ipynb).
