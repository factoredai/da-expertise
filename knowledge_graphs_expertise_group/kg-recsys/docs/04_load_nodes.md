# Loading Nodes into Neo4j (T-10)

How we load every node label in the KG schema into Neo4j using the official Python driver, idempotently, and in a way that reads cleanly as a teaching artifact.

Reference notebook: [`notebooks/04_load_nodes.ipynb`](../notebooks/04_load_nodes.ipynb).

---

## What This Step Produces

After running the notebook against an AuraDB instance, the database contains all five node labels in T-10's scope, with uniqueness constraints in place and one fulltext index on movie titles.

| Label | Source | Expected count |
|---|---|---|
| `:Genre` | `data/raw/ml-100k/u.genre` | 19 |
| `:User` | `data/raw/ml-100k/u.user` | 943 |
| `:Movie` | `data/raw/ml-100k/u.item` + `data/enriched/enriched_movies.csv` | 1,682 |
| `:Director` | `data/enriched/enriched_movies.csv` (`directors`) | ~1,300–1,500 unique |
| `:Actor` | `data/enriched/enriched_movies.csv` (`cast`) | ~10,000 unique |

No relationships are created here — that lands in the next task.

---

## Scope Decisions

A few design calls were made up front and are worth surfacing:

- **Five labels only.** `:Occupation` and `:Gender` are in the project schema but are deferred to the task that creates their `HAS_OCCUPATION` / `HAS_GENDER` edges. Loading them now would leave orphan nodes — confusing and unhelpful.
- **`age` stays as a User property.** It's a scalar you'd filter on, not something you'd traverse to. Modelling every integer age as its own node would over-graphify.
- **`zip` is dropped.** No location-based recommendations are in scope, so it's dead weight.
- **All Movie nodes are created**, including the ~1% TMDB couldn't match. Those rows just don't get a `tmdbId` property.
- **No database wipe.** The notebook is designed to run on top of the T-09 sample data — `MERGE` makes that safe. A commented `MATCH (n) DETACH DELETE n` is provided if you ever want a clean slate.

---

## Architecture — How the Code Is Split

```
notebooks/04_load_nodes.ipynb     ← orchestration + inline Cypher (the interesting part)
       │
       ├──► src/etl.py            ← file readers only (pandas, regex, JSON-in-CSV parsing)
       │
       └──► src/graph.py          ← driver + run_query / run_write_query helpers
```

This split is deliberate. The boring plumbing (CSV parsing, NaN handling, regex on titles) lives in `etl.py` where it stays out of the way. The **Cypher** — the part a student needs to read and understand — lives inline in the notebook, one block per label. The driver and connection logic are encapsulated in `graph.py` so the notebook never carries credentials or boilerplate.

### Where the connection actually comes from

The notebook never mentions a URI or password. That's because `src/graph.py` calls `load_dotenv()` at import time and `get_driver()` reads `NEO4J_URI`, `NEO4J_USERNAME`, and `NEO4J_PASSWORD` from `.env` on first use. Every call to `run_query` or `run_write_query` goes through the same singleton driver.

---

## Schema Artifacts

Before any load runs, the notebook re-applies the constraints and fulltext index from T-09 so it's self-sufficient. Every statement uses `IF NOT EXISTS`, so it's a no-op if they're already there.

| Constraint | Label | Property |
|---|---|---|
| `user_id` | `:User` | `userId` UNIQUE |
| `movie_id` | `:Movie` | `movieId` UNIQUE |
| `genre_name` | `:Genre` | `name` UNIQUE |
| `director_nm` | `:Director` | `name` UNIQUE |
| `actor_name` | `:Actor` | `name` UNIQUE |

| Index | Type | Target |
|---|---|---|
| `movie_title_search` | FULLTEXT | `:Movie(title)` |

The constraints do double duty: they prevent accidental duplicates **and** create a backing index, which makes `MERGE` lookups fast.

---

## The MERGE Pattern

Every load uses `MERGE`, not `CREATE`. The semantics:

> `MERGE (n:Label {key: value})` finds a node matching that pattern, or creates it if none exists.

Combined with the uniqueness constraints above, this means:

- **First run** → creates all nodes.
- **Re-run on the same data** → finds them all, creates nothing, counts stay flat.
- **Re-run with one new row added** → finds the existing ones, creates only the new one.

That's idempotency — the notebook is safe to re-run as many times as you want, and safe to run on top of the T-09 sample data without producing duplicates.

---

## The Cypher Idioms

Three patterns show up repeatedly. Worth knowing.

### 1. `UNWIND` for batch loads

Rather than calling `MERGE` once per row from Python (slow — one network round trip each), we pass the whole batch as a single parameter and let Cypher iterate inside the server.

```cypher
UNWIND $rows AS row
MERGE (u:User {userId: row.userId})
SET u.age = row.age
```

`$rows` is a list of dicts passed from Python. One round trip, thousands of nodes.

### 2. Parameterized queries (always)

Values are **never** string-formatted into the Cypher text. They're passed as parameters (`$rows`, `$names`) so the query plan can be cached and there's no Cypher-injection surface.

### 3. `FOREACH … CASE` for conditional property assignment

Some movies have a `tmdbId`, some don't. We want to set the property only when it's not null — otherwise the property should be absent from the node, not set to `null`. The canonical Cypher idiom is:

```cypher
FOREACH (_ IN CASE WHEN row.tmdbId IS NULL THEN [] ELSE [1] END |
  SET m.tmdbId = row.tmdbId
)
```

The `CASE` evaluates to an empty list (skip) or a single-element list (run once). `FOREACH` only iterates the elements, so the `SET` either runs once or not at all. It looks odd; it's the standard pattern.

---

## Per-Label Walkthrough

Every label follows the same three-step rhythm: **read → load → verify**.

### Genres (19)

```cypher
UNWIND $names AS name
MERGE (:Genre {name: name})
```

Simplest case. A flat list of strings from `u.genre`, one `MERGE` per name.

### Users (943)

```cypher
UNWIND $rows AS row
MERGE (u:User {userId: row.userId})
SET u.age = row.age
```

T-10's strict scope means only `userId` and `age` land on the node. The reader (`read_users`) returns a DataFrame with just those two columns; the other source columns (`gender`, `occupation`, `zip`) are dropped before the load.

### Movies (1,682)

This is the only label with a join. `read_movies` left-joins `u.item` (movieId, title, year) with `enriched_movies.csv` (tmdbId). Movies that TMDB couldn't match keep all the basic fields and lose only `tmdbId`.

```cypher
UNWIND $rows AS row
MERGE (m:Movie {movieId: row.movieId})
SET m.title = row.title, m.year = row.year
FOREACH (_ IN CASE WHEN row.tmdbId IS NULL THEN [] ELSE [1] END |
  SET m.tmdbId = row.tmdbId
)
```

Title cleanup happens in Python. MovieLens stores titles as `"Toy Story (1995)"`; a regex (`_TITLE_YEAR_RE`) strips the trailing year and pulls it out as an integer. Verification prints both the total Movie count and the count with a `tmdbId` so you can confirm the match rate.

### Directors (~1,300–1,500)

```cypher
UNWIND $names AS name
MERGE (:Director {name: name})
```

The `directors` column in `enriched_movies.csv` is a CSV-encoded list (one movie can have multiple directors — the Coens, the Wachowskis, anthology films). `read_directors` uses `ast.literal_eval` to parse each cell, flattens across rows, and dedupes via a set.

### Actors (~10,000)

```cypher
UNWIND $names AS name
MERGE (:Actor {name: name})
```

Same shape as directors. `read_actors` flattens the `cast` column (top 10 per movie by billing order). Billing order itself is preserved for the future `FEATURES_ACTOR` edge load — it isn't a node property.

---

## NaN → None: a small but load-bearing helper

The Neo4j driver expects Python `None` for null values; pandas `NaN` does not serialize cleanly. Every DataFrame passes through `to_records` before being sent to Cypher:

```python
def to_records(df: pd.DataFrame) -> list[dict]:
    return [
        {k: (None if pd.isna(v) else v) for k, v in row.items()}
        for row in df.to_dict("records")
    ]
```

Skipping this step is what most "why is `tmdbId` set to the string `'nan'`" bugs come from.

---

## Verification

The notebook ends with a summary cell that counts nodes per label:

```cypher
MATCH (n)
RETURN labels(n)[0] AS label, count(*) AS n
ORDER BY n DESC
```

On a fresh load you should see roughly:

| Label | Count |
|---|---|
| `:Actor` | ~10,000 |
| `:Movie` | 1,682 |
| `:Director` | ~1,300–1,500 |
| `:User` | 943 |
| `:Genre` | 19 |

If you ran on top of T-09 sample data, you'll also see leftover `:Occupation` and `:Gender` nodes from that earlier step — that's expected.

### Proving idempotency

The thing worth seeing for yourself: **run the summary cell a second time**. Counts should be byte-for-byte identical. If you re-run any of the load cells, the counts still don't move. That's the `MERGE` pattern working.

---

## What's Not in This Step

| Out of scope | Lands in |
|---|---|
| `RATED`, `IN_GENRE`, `DIRECTED_BY`, `FEATURES_ACTOR` edges | T-11 |
| `:Occupation`, `:Gender` nodes + `HAS_*` edges | The task that creates their relationships |
| Derived relationships (`COLLABORATED_WITH`, `SIMILAR_TO`) | A later projection step |
| Any TMDB API calls | Already done in [`02_tmdb_enrichment.ipynb`](../notebooks/02_tmdb_enrichment.ipynb) |

---

## Quick Sanity Check Before Running

If the notebook errors on the first load cell, it's almost always one of these:

1. **`.env` missing or incomplete.** `print(os.environ.get("NEO4J_URI"))` should return your URI, not `None`.
2. **AuraDB instance paused.** Free-tier instances auto-pause after inactivity. Resume from [console.neo4j.io](https://console.neo4j.io).
3. **`enriched_movies.csv` missing.** Re-run [`02_tmdb_enrichment.ipynb`](../notebooks/02_tmdb_enrichment.ipynb) — it produces this file.
