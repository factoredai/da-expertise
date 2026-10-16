# Loading User Attributes into Neo4j

The final step on the user side of the graph: load `:Occupation` and `:Gender` nodes and the two relationship types that connect users to them. After this step every user is fully described in the graph — age (on the node), occupation, and gender (as edges to reference nodes).

Reference notebook: [`notebooks/06_load_user_attributes.ipynb`](../notebooks/06_load_user_attributes.ipynb).

---

## What This Step Produces

| Element | Source | Expected count |
|---|---|---|
| `:Occupation {name}` | `data/raw/ml-100k/u.occupation` | 21 |
| `:Gender {name}` | hardcoded `['M', 'F']` | 2 |
| `(:User)-[:HAS_OCCUPATION]->(:Occupation)` | `u.user.occupation` | 943 |
| `(:User)-[:HAS_GENDER]->(:Gender)` | `u.user.gender` | 943 |

After this notebook runs cleanly, the AuraDB instance should report **6 relationship types** in the summary (the 4 from T-11 + these 2) and **7 node labels** (the 5 from T-10 + these 2).

---

## Scope Decisions

The decisions worth recording — most mirror T-10/T-11 calls, with two specific to this work.

- **`u.occupation` is the source of truth.** ml-100k ships a canonical occupation list (21 names, plain text). Reading from it instead of inferring distinct values from `u.user` mirrors the `u.genre` → `:Genre` pattern and keeps the taxonomy explicit.
- **Genders stay raw (`'M'` and `'F'`).** Two values, no `M`→`Male` normalization. Source fidelity over readability — and a one-character key is unambiguous in queries anyway.
- **Property-less edges.** `:HAS_OCCUPATION` and `:HAS_GENDER` carry no properties. A user belongs to exactly one occupation and one gender, full stop. Same shape as `:IN_GENRE`.
- **Surgical teardown, not a blanket wipe.** Unlike the optional teardowns in 04 and 05 (which delete everything), the teardown here only touches the four schema elements this notebook owns:
  ```cypher
  MATCH ()-[r:HAS_OCCUPATION|HAS_GENDER]->() DELETE r;
  MATCH (n:Occupation) DETACH DELETE n;
  MATCH (n:Gender)     DETACH DELETE n;
  ```
  Other nodes and edges are untouched, so 04 and 05 don't need to re-run. The teardown still ships commented because `MERGE` makes the load idempotent — uncomment only on first run if there's leftover state from a prior experiment (e.g. the 5+5 ghost edges that appeared after T-11).
- **Edge readers re-read `u.user` independently.** Rather than widen T-10's `read_users()` contract (which intentionally drops `gender`/`occupation`), the two new edge readers re-read the file. Two extra ~10ms reads vs. polluting a fixed contract — clear win.

---

## The Two-Key Principle, Continued

T-11 set up the rhythm: every endpoint has a unique key, every load does a constraint-backed `MATCH` on both before merging the edge. This step adds two more constraints, both backed by automatic indexes:

| Endpoint | Unique key | Constraint name |
|---|---|---|
| `:Occupation` | `name` | `occupation_name` |
| `:Gender` | `name` | `gender_name` |

`:User` already has `user_id` from T-10. With these constraints in place, both `HAS_*` loads run as index-hit lookups on both endpoints.

For the broader explanation of why constraint-backed `MATCH`es matter at load time (the "minutes vs. seconds" tradeoff), see [`docs/05_load_relationships.md`](05_load_relationships.md#the-two-key-principle).

---

## The Edge-Row Pattern, Continued

Same pattern as T-11 — Python produces edge rows, Cypher does `MATCH` + `MERGE`. The two new edges are the simplest case in the project: each edge row is already a row in `u.user`, no explode or melt needed. The reader is one `read_csv` plus a column projection.

```
u.user row:  userId=196, age=49, gender='M', occupation='writer', zip='55105'

      ▼  Python: just project the relevant columns

(userId=196, occupation='writer')   → HAS_OCCUPATION edge row
(userId=196, gender='M')            → HAS_GENDER edge row
```

The Cypher shape is the same `UNWIND $rows → MATCH a → MATCH b → MERGE edge` that T-11 already documented.

---

## Per-Element Walkthrough

### `:Occupation` nodes (21)

```cypher
UNWIND $rows AS row
MERGE (:Occupation {name: row.name})
```

The reader just reads `u.occupation` line by line and returns the list. No CSV parsing, no normalization — `u.occupation` is plain text, one name per line (unlike `u.genre`, which uses `name|index`). The reader is six lines including the docstring.

### `:Gender` nodes (2)

```cypher
UNWIND $rows AS row
MERGE (:Gender {name: row.name})
```

`read_genders()` returns the hardcoded list `['M', 'F']`. Hardcoding a two-element constant beats reading-and-deduping from `u.user` here — the contract is explicit and the source list is fixed by the dataset itself.

### `:HAS_OCCUPATION` edges (943)

```cypher
UNWIND $rows AS row
MATCH (u:User       {userId: row.userId})
MATCH (o:Occupation {name:   row.occupation})
MERGE (u)-[:HAS_OCCUPATION]->(o)
```

The reader returns a 943×2 DataFrame `[userId, occupation]` straight from `u.user`. Every user contributes exactly one row — there's no skip case here, because `u.user` has no `NaN`s in the occupation column.

### `:HAS_GENDER` edges (943)

```cypher
UNWIND $rows AS row
MATCH (u:User   {userId: row.userId})
MATCH (g:Gender {name:   row.gender})
MERGE (u)-[:HAS_GENDER]->(g)
```

Structurally identical to `HAS_OCCUPATION` — just different labels and column name. Same 943 rows, same one-to-one cardinality.

---

## Heads-up: `:Gender` Is a Super-Hub

`:Gender` has only 2 nodes for 943 users, so each gender node connects to ~470 users. Any query that fans out from a gender node (`(:Gender)<-[:HAS_GENDER]-(:User)`) hits ~470 neighbors in a single step.

This is fine for our query patterns (we always start from a user and traverse outward through gender, never the reverse) but worth knowing if you later visualize the graph: gender nodes will look enormous compared to the rest. `:Occupation` is milder — 21 nodes, ~45 users each on average — but the same pattern in miniature.

If a future query suffers from this fan-out (e.g. "find every movie ever rated by anyone with gender M"), the fix is usually a `LIMIT` early in the traversal or a pre-filtered subset, not a schema change.

---

## Verification

After running all four sections, the summary cell should report:

| Relationship | Count |
|---|---|
| `RATED` | 100,000 |
| `FEATURES_ACTOR` | ~16,000 |
| `IN_GENRE` | ~3,000 |
| `DIRECTED_BY` | ~1,700–2,000 |
| `HAS_OCCUPATION` | 943 |
| `HAS_GENDER` | 943 |

If you see additional `HAS_*` counts from prior experiments (the 5+5 ghost edges that appeared after T-11), uncomment the teardown cell once and re-run.

### Proving idempotency

Same drill as 04 and 05: **run the summary once, re-run any load cell, run the summary again.** All six counts should be byte-for-byte identical. That's `MERGE` doing its job a third time.

---

## The Spot-Check Queries

### Query 1 — User 196's full profile

```cypher
MATCH (u:User {userId: 196})
OPTIONAL MATCH (u)-[:HAS_OCCUPATION]->(o:Occupation)
OPTIONAL MATCH (u)-[:HAS_GENDER]->(g:Gender)
RETURN u.userId AS userId, u.age AS age, o.name AS occupation, g.name AS gender
```

The same "full neighborhood in one query" shape used for *Toy Story* in T-11, but on the user side. Three pieces of information about user 196 in one traversal. Pulls every attribute we know about that user.

`OPTIONAL MATCH` makes the query defensive — if some user is missing an attribute (shouldn't be, but the pattern is robust), the row still returns with `None` in that column.

### Query 2 — Genres liked by users sharing User 196's occupation

```cypher
MATCH (u:User {userId: 196})-[:HAS_OCCUPATION]->(o:Occupation)<-[:HAS_OCCUPATION]-(peer:User)
MATCH (peer)-[r:RATED]->(m:Movie)-[:IN_GENRE]->(g:Genre)
WHERE r.rating >= 4
RETURN g.name AS genre, count(*) AS high_ratings
ORDER BY high_ratings DESC LIMIT 5
```

**This is the payoff query.** Three hops in one Cypher block:

1. From user 196, hop to their occupation.
2. From that occupation, hop *back* to every other user who shares it (the "peers" set).
3. From each peer, hop through their high ratings to a genre.

This is a *collaborative-filtering-flavored* recommendation — "what do people like me enjoy?" — implemented in pure Cypher, with no GROUP BY tables, no joins, no SQL gymnastics. The traversal *is* the query.

This pattern is the foundation of recommendation strategy 3 from [`CLAUDE.md`](../CLAUDE.md) ("Collaborative filtering via shared graph neighborhood"). Without `:HAS_OCCUPATION` there's no axis along which to define "people like me."

---

## What's Not in This Step

| Out of scope | Lands in |
|---|---|
| Derived edges between users (e.g. `:SAME_OCCUPATION_AS`, `:SAME_GENDER_AS`) | A later projection step, if needed at all (the two-hop pattern in Q2 may make these unnecessary) |
| Property-level enrichment on `:Occupation` (e.g. category groupings like "STEM" / "creative") | Not in project scope — would require an external taxonomy |
| Demographic-aware recommendation logic | The recommender strategies that consume this data, downstream |

---

## Quick Sanity Check Before Running

If something errors on first run, it's almost always one of these:

1. **T-10 not loaded.** Every `HAS_*` edge requires a `:User` node on one end. Run [`04_load_nodes.ipynb`](../notebooks/04_load_nodes.ipynb) first.
2. **Ghost `:Occupation` / `:Gender` data from prior experiments.** Uncomment the teardown cell once, re-run, re-comment.
3. **`u.user` or `u.occupation` missing.** Both ship with ml-100k under `data/raw/ml-100k/`.
4. **AuraDB instance paused.** Free-tier instances auto-pause; resume from [console.neo4j.io](https://console.neo4j.io).
