# Strategy 2 — Director / Actor Affinity

The second of the four recommendation strategies named in [`CLAUDE.md`](../CLAUDE.md). Multi-hop: walk from a user, through their 4★+ ratings, to the **directors** and **top-billed actors** of those movies, then back out to *other* movies those people made — movies the user hasn't rated. The candidate pool is the **union** of the director route and the actor route; the score sums per-person affinity across every connecting top person; the explanation for one rec is a per-rec single chain.

Reference notebook: [`notebooks/12_strategy_director_actor.ipynb`](../notebooks/12_strategy_director_actor.ipynb).
Implementation: [`src/recommender.py`](../src/recommender.py) — `director_actor_affinity()` + `DIRECTOR_ACTOR_CYPHER`.

---

## What This Notebook Demonstrates

Sixteen cells, walking the strategy end-to-end on the recurring anchor user 196 (same anchor as notebooks 09 / 10 / 11). The first half builds the query in pieces (Phase 1 → Phase 2 → Phase 3 as standalone Cypher); the second half collapses them into the unified `DIRECTOR_ACTOR_CYPHER` constant, calls the wrapper, then explores the knobs and edge cases.

| # | Section | Takeaway |
|---|---|---|
| 0 | **Framing** | What "multi-hop director/actor affinity" means, why routes are OR-joined, why explainability is a per-rec chain (the structure of the query *is* the explanation). |
| 1 | **Setup** | Same `sys.path` + imports pattern as notebooks 04–11. Pulls `run_query` and `close_driver` only; `director_actor_affinity` is imported later (cell 9), once the phase-by-phase build has paid off. |
| 2 | **User 196's people profile** | Standalone Cypher: top 3 directors + top 5 top-billed actors (`billing_order <= 5`) by 4★+ count. Establishes what we *expect* Strategy 2 to surface. |
| 3 | **"Build the query phase by phase"** | Frame the next three cells: each phase ends with `RETURN` so it runs standalone; in cell 8's unified version those `RETURN`s become `WITH`. Direct callback to the `WITH` ↔ `RETURN` distinction from notebook 09. |
| 4 | **Phase 1 standalone** | The full Phase 1a + 1b block, ending with `RETURN` over `top_people`. Renders `(name, kind, affinity, n_seeds)`. Course-taker sees the top-people list as data, not as a black-box intermediate. |
| 5 | **Phase 2 standalone** | Given Phase 1's `top_people`, unwind the per-person `seeds` to surface the user's actual ≥4★ ratings that *earned* each person their affinity. Renders `(seed_title, person, kind, affinity)` — the bridge that each `seed_chain` will walk back to. |
| 6 | **Phase 3 standalone** | Given top people + seed evidence, walk forward to unseen recs, aggregate per rec, score, rank. Same final shape as the wrapper function output. Rendered as DataFrame: `(title, year, score, via_people, seed_chains)`. |
| 7 | **"Now bring it all together"** | Markdown narrates the collapse: standalone `RETURN`s become `WITH`s, the final `RETURN` lives at the end of Phase 3. |
| 8 | **The unified constant** | `from recommender import DIRECTOR_ACTOR_CYPHER; print(DIRECTOR_ACTOR_CYPHER)`. The same Cypher the reader just ran in pieces, now visible as the one query that ships. |
| 9 | **Call the wrapper** | `director_actor_affinity(196)`. Renders identically to cell 6 — same `movieId`s in the same order. The function is just the parameter-passing wrapper. |
| 10 | **Reading the explainability chain** | Markdown: how to read one rec — `via_people` as the connecting top people, one `seed_chain` walked end-to-end in prose. Why this is honest (vs. Strategy 1's global seeds — the structure of the query *is* the chain). |
| 11 | **Knob — `top_n_directors` / `top_n_actors`** | `(1, 1)` vs `(5, 10)`. Tighter = sharper per-rec story; wider = more multi-person overlap and bigger scores. |
| 12 | **Knob — `max_billing`** | `=999` (filter effectively off). Shows that walk-ons inflate affinity once the filter is lifted. Justifies the `≤ 5` default. |
| 13 | **Cold-start edge case** | (a) A user with zero 4★+ ratings → `[]`. (b) A non-existent user (99999) → `[]`. Contract: empty list = no signal. Strategy 4 owns the fallback. |
| 14 | **Anchor sanity** | Soft check: returned `movieId`s should not overlap with user 196's rated movies. Cypher counts the overlap; expected = 0. |
| 15 | **Cleanup** | `close_driver()`, same pattern as notebooks 04–11. |

Cell 10 is the load-bearing one — it teaches the reader how to *defend* one rec to a stakeholder using its `seed_chains`, which is the payoff that notebook 11 deliberately deferred.

---

## Scope Decisions

A few choices worth recording.

- **One unified query, OR-joining the two routes.** The candidate pool is the union of "movies sharing a top director" and "movies sharing a top top-billed actor." Intersection would collapse the pool — most movies share *either* a director *or* an actor with a user, rarely both. The schema treats `:DIRECTED_BY` and `:FEATURES_ACTOR` as independent edges, and a person can be reached via either. OR keeps the candidate pool wide; the scoring formula handles "connected via both" naturally by summing both affinities.
- **Score = `sum(affinity)` across matched top people.** Direct mirror of Strategy 1's `sum(affinity)` across matched top genres — keeps the two strategies comparable when Strategy 4 weights them. A rec connected by two top people outranks one connected by a single top person, weighted by how strong each affinity was. Honest aggregate; no calibration claimed.
- **`top_n_directors = 3`, `top_n_actors = 5`.** Asymmetric on purpose: most movies have one director but several billed actors, so the actor pool yields more bridging candidates and benefits from being deeper. Both defaults keep the per-rec story crisp; cell 11 shows what happens at the extremes (`(1,1)` vs `(5,10)`).
- **`billing_order <= 5` filter on actors, applied in *both* Phase 1 and Phase 3.** Without it, extras and bit parts inflate the affinity signal — `top_actors` becomes "actors that happen to appear in many of the user's 4★+ movies, regardless of role size," which surfaces walk-ons. Five is the conventional "above-the-title cast" line. The filter is applied at *both* hops because Phase 1 picks the top actors (their affinity should reflect lead/supporting credits only) and Phase 3 walks to new movies (a rec shouldn't enter the pool just because a top actor had a one-line cameo in it). Cell 12 demonstrates what happens with the filter off.
- **Per-rec `via_people` + `seed_chains` (capped at 3).** Strategy 2's score *is* a path-based aggregate: every contribution to the score comes from a concrete `(seed, person, rec)` triple. So per-rec single-chain explanations honestly mirror the query — a reader can defend one rec by reading one chain. `via_people` lists every top person connecting the user to the rec (e.g. `["Tom Hanks (actor)", "Robert Zemeckis (director)"]`) so a stakeholder sees the whole connective tissue at a glance. `seed_chains` is capped at 3 — enough evidence without UI noise. This is the *payoff* deferred from Strategy 1's global-seeds shape.
- **`head(p.seeds)` for each chain — arbitrary seed per person.** Seeds are evidence, not ranked output. We don't claim "this is the *strongest* seed for this person" — only "here's one ≥4★ movie this user rated that earned this person their top spot." If reproducibility ever matters (e.g. Strategy 4 calibration), we can `ORDER BY` seeds inside Phase 1.
- **`seed_chains` is order-by-unwind, not strength-ranked.** Directors are unwound first (Phase 1a precedes Phase 1b, both `ORDER BY affinity DESC`), then actors. The `[..3]` slice takes the first three chains in that order. All three chains are real; a reader inspecting `seed_chains` shouldn't infer position-1 is the "strongest" — only that director chains tend to come first when both routes apply.
- **`elementId()`, not `id()`.** Modern Neo4j 5.x replacement for the deprecated integer `id()`. AuraDB Free runs 5.x. Stable within a single query and unique across the database — exactly what the EXISTS subqueries need to match a person without re-binding labels.
- **Cold start returns an empty list.** Same contract as Strategy 1. Phase 1a's `LIMIT $top_n_directors` returns nothing for a user with zero ≥-threshold ratings; Phase 1b also returns nothing; `UNWIND top_people` in Phase 3 has nothing to expand; the query returns `[]`. No Python-side flag, no fallback inside Strategy 2. The "1-rating user still gets recs" teaching moment from [`CLAUDE.md`](../CLAUDE.md) lives in **Strategy 4** (composite with demographic pivots) where it fits naturally.
- **`NOT EXISTS { (u)-[:RATED]->(rec) }` excludes any rated movie, regardless of rating value.** Even movies the user disliked (1★ or 2★) are excluded from recs — we never recommend a movie the user has already formed an opinion on.
- **Tie-break by `(score DESC, title ASC)`.** Same as Strategy 1; simple, deterministic, no extra Cypher gymnastics. Popularity-weighted tie-breaks can come later in Strategy 4 if needed.
- **No APOC.** Plain `UNWIND`, `collect`, list comprehensions, `reduce()`, `head()`, the `[..3]` slice, and `elementId()` — all in core Cypher 5. Works on AuraDB Free out of the box.
- **No Python-side filtering or sorting.** Per [`CLAUDE.md`](../CLAUDE.md): *"All logic must be implemented as Cypher queries."* The `director_actor_affinity()` function is a thin parameter-passing wrapper around `DIRECTOR_ACTOR_CYPHER`. The verification step (`grep -nE "sort|filter|sorted|key=lambda"` against the new function body) confirms it has none.
- **Soft prints, no asserts.** Same policy as notebooks 08 / 09 / 10 / 11. The notebook is a teaching artifact, not a test. Cell 14's anchor sanity check prints `OK` or `MISMATCH` rather than raising.

---

## What's In vs. What's Out

| In scope | Out of scope | Where it lands |
|---|---|---|
| OR-joined director + actor routes | Director-only or actor-only sub-strategies | Possibly a Streamlit knob; not yet |
| Tunable `top_n_directors`, `top_n_actors`, `max_billing`, `threshold` | Per-person affinity weighting (e.g. some directors weighted higher than others) | Strategy 4 calibration if needed |
| Sum-of-affinity score across matched people | Path-length weighting (longer chains discounted) | Strategy 4 if Streamlit demos look off |
| Per-rec `via_people` + `seed_chains` (≤ 3) | Top-3-strongest-chains ranked by strength (vs. by unwind order) | Possibly Strategy 4 |
| `billing_order <= 5` filter on both hops | Role-type filter (lead vs. supporting vs. cameo) | Out — MovieLens / TMDB doesn't tag this reliably |
| Empty list on cold start | Demographic-pivot fallback for cold users | **Strategy 4** ([T-22]) — composite |
| `elementId()`, `UNWIND`, `collect`, `reduce()`, list comprehensions, `head()` | `apoc.*` helpers | Not needed |
| Read queries only | Write queries (`CREATE`, `MERGE`) | Notebooks 04 → 07 |
| Soft prints | Hard asserts / pytest | Out of project scope |
| Tie-break `(score DESC, title ASC)` | Popularity-weighted tie-breaks | Possibly Strategy 4 |

---

## Quick Sanity Check Before Running

If a cell errors on first run, it's almost always one of these:

1. **Notebooks 03 → 07 haven't been run against the current AuraDB instance.** Cell 2's people profile returns zeros — no data is loaded. Re-run the load notebooks.
2. **AuraDB instance paused.** Free-tier instances auto-pause; resume from [console.neo4j.io](https://console.neo4j.io).
3. **`.env` missing or stale.** `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` must point to the live instance.
4. **User 196 not in dataset.** Same recurring anchor as notebooks 09 / 10 / 11 — if those work, this will too.
5. **`from recommender import director_actor_affinity, DIRECTOR_ACTOR_CYPHER` fails.** [`src/recommender.py`](../src/recommender.py) must use `from graph import run_query` (not `from src.graph import …`), matching the notebook's `sys.path` setup.
6. **Sparse TMDB enrichment surfaces empty Phase 1b.** If notebook 02's enrichment run hit a low cast-coverage ratio for user 196's rated movies, `top_n_actors=5` may surface fewer than 5 people (or none). Workaround: drop `top_n_actors` to whatever the data supports, or check `top_actors` in cell 2 first.
