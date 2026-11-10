# KG-Based Recommendation System

An end-to-end Knowledge Graph recommendation system built as a course use-case to demonstrate KG value over tabular/SQL approaches.

> **Status:** Implemented end to end. The graph is loaded (notebooks 04–08), all four recommendation strategies are built and exposed through a unified `get_recommendations()` interface (notebooks 11–14), and the three-screen Streamlit demo is running. Still open: the demographic cold-start fallback (T-22b) and a pyvis rendering bug for `:COLLABORATED_WITH` edges (see [Known Limitations](#known-limitations)).

## What This Demonstrates
- **Multi-hop queries** — a single Cypher pattern replaces multi-JOIN SQL (six paired SQL ↔ Cypher examples in [notebook 10](notebooks/10_sql_vs_cypher.ipynb); the gap widens with every hop, and the actor-triangle example needs a CTE plus three self-joins in SQL)
- **Recommendation explainability** — every result includes the graph path that produced it (e.g. *"You rated Toy Story 5★ → Tom Hanks → Apollo 13"*)
- **Cold-start behavior** — users with no ≥4★ ratings (or unknown users) get an empty list rather than a guess. A demographic-pivot fallback is planned (T-22b) but not built yet.

## The Graph at a Glance
About **13k nodes** and **190k relationships**: Actor 9,301 · Movie 1,682 · Director 1,128 · User 943 · Occupation 21 · Genre 19 · Gender 2, plus 100,000 `:RATED` edges and 70,139 derived `:COLLABORATED_WITH` edges.

## Stack
| Layer | Tool |
|---|---|
| Dataset | MovieLens 100K + TMDB API |
| Graph DB | Neo4j AuraDB Free Tier |
| Python driver | `neo4j` official driver |
| RecSys logic | Pure Cypher queries |
| App | Streamlit + `pyvis` |
| Docs | Markdown + Jupyter |

## Project Structure
```
kg-recsys/
├── data/
│   ├── raw/          # MovieLens 100K source files (not committed — download separately)
│   └── enriched/     # TMDB-enriched movies (enriched_movies.csv is committed, so notebook 02 is optional)
├── notebooks/        # 14 step-by-step notebooks: EDA, enrichment, schema, loading, verification, Cypher, strategies
├── queries/          # Standalone Cypher queries (runnable in Neo4j Browser)
├── src/              # Core Python modules (graph.py, etl.py, recommender.py)
├── app/              # Streamlit interactive demo
├── docs/             # Course documentation (setup, enrichment approach, schema diagram)
├── CLAUDE.md         # Project conventions for AI-assisted contributions
└── CONTRIBUTING.md   # How to contribute
```

## Quick Start
```bash
conda create -n kg-recsys python=3.10
conda activate kg-recsys
pip install -r requirements.txt
cp .env.example .env        # copy the template — then fill in your Neo4j credentials (TMDB key only for notebook 02)
# Download ml-100k.zip from grouplens.org and extract it to data/raw/ml-100k/
# Run notebooks 04 → 05 → 06 → 07 in order to populate the graph, then 08 to verify
streamlit run app/streamlit_app.py
```

> See [docs/01_setup.md](docs/01_setup.md) for the full setup walkthrough (~60 minutes), including AuraDB creation, credentials, MovieLens download, graph load, and troubleshooting. Free-tier AuraDB auto-pauses after 3 days of inactivity — resume it from the console if queries fail with `ServiceUnavailable`. For the graph schema and its rationale, see [notebooks/03_graph_schema.ipynb](notebooks/03_graph_schema.ipynb) and [docs/03_schema_diagram.md](docs/03_schema_diagram.md).

## Recommendation Strategies
All four are pure Cypher (no APOC), return an explainability path per recommendation, and are called through `get_recommendations(user_id, strategy, limit=10, **kwargs)` in `src/recommender.py`.

| # | Strategy | Signal | Score |
|---|---|---|---|
| 1 | **Genre affinity** | User's top 3 genres by ≥4★ ratings | Sum of genre affinity |
| 2 | **Director/Actor affinity** | Top 3 directors and top 5 actors (billing order ≤ 5) | Sum of affinity of connecting people |
| 3 | **Collaborative filtering** | Peers sharing ≥3 ≥4★ ratings (top 25) | Σ overlap × peer rating |
| 4 | **Composite multi-signal** | Weighted Reciprocal Rank Fusion of 1–3 | Σ weight / rank |

Ties break on `(score DESC, title ASC)`. Unknown strategy names raise `ValueError`.

## Graph Schema

**7 node labels, 7 relationship types.** Full specification, rationale, and Cypher constraints in [notebooks/03_graph_schema.ipynb](notebooks/03_graph_schema.ipynb). Color-coded diagram in [docs/03_schema_diagram.md](docs/03_schema_diagram.md).

```
(:User {userId, age})-[:RATED {rating, timestamp}]->(:Movie {movieId, title, year, tmdbId})
(:Movie)-[:IN_GENRE]->(:Genre {name})
(:Movie)-[:DIRECTED_BY]->(:Director {name})
(:Movie)-[:FEATURES_ACTOR {billing_order}]->(:Actor {name})
(:User)-[:HAS_OCCUPATION]->(:Occupation {name})
(:User)-[:HAS_GENDER]->(:Gender {name})
(:Actor)-[:COLLABORATED_WITH {movie_count}]->(:Actor)    // derived, see below
```

> `:COLLABORATED_WITH` is **materialized** by [notebook 07](notebooks/07_collaborated_with.ipynb) from shared `:FEATURES_ACTOR` edges (one canonical edge per actor pair, `a1.name < a2.name`, with a `movie_count`). `:SIMILAR_TO` is **not stored** and is computed at query time. Note that the schema notebook (03) predates this change and still records decision D9 ("no materialized `:COLLABORATED_WITH`") and a 6-relationship count.

## Known Limitations
- **No cold-start fallback yet.** All four strategies return `[]` for users with no ≥4★ ratings or unknown IDs. The demographic-pivot fallback is tracked as T-22b.
- **Coarse score ties in Strategies 1 and 2.** For user 196 every top Strategy 1 recommendation scores 31, so the order falls back to alphabetical.
- **Strategy 4 is unevaluated.** The fusion weights default to 1.0 each with no offline evaluation, and the three sub-strategies overlap little (for user 196 the union of the three top-15 pools is 44 movies).
- **TMDB match quality.** 1,679 of 1,682 movies are matched (99.8%), but the year-less retry pass accepted a few wrong matches (e.g. *Boys Life* → *Bad Boys for Life*) that were not manually corrected.
- **Strategy 4 emits a Neo4j deprecation warning** (`CALL {}` without a scope clause) on every call. It is harmless today.
- **pyvis `:COLLABORATED_WITH` edge rendering** in the Graph Explorer screen is a known bug, deferred.

## Documentation

| Doc | What's in it |
|---|---|
| [docs/00_overview.md](docs/00_overview.md) | Course front door — why a KG, project architecture, 6-module learning path with time budgets and exercises (T-31) |
| [docs/01_setup.md](docs/01_setup.md) | End-to-end setup — AuraDB instance, credentials, MovieLens, graph load, verification, troubleshooting (T-28) |
| [docs/02_enrichment_approach.md](docs/02_enrichment_approach.md) | How MovieLens is enriched with TMDB metadata (cast, directors, genres) |
| [docs/03_schema_diagram.md](docs/03_schema_diagram.md) | Mermaid schema diagram, color-coded by node tier |
| [docs/04_load_nodes.md](docs/04_load_nodes.md) | How nodes are loaded into Neo4j — idempotent, schema-aligned (T-10) |
| [docs/05_load_relationships.md](docs/05_load_relationships.md) | How relationships are loaded on top of those nodes (T-11) |
| [docs/06_load_user_attributes.md](docs/06_load_user_attributes.md) | How user attributes (occupation, gender) become edges in the graph |
| [docs/07_collaborated_with.md](docs/07_collaborated_with.md) | Why and how `:COLLABORATED_WITH` is derived from the graph itself |
| [docs/08_verification.md](docs/08_verification.md) | End-to-end integrity check: schema, counts, structural invariants, index proof (T-13, T-14) |
| [docs/09_cypher_queries.md](docs/09_cypher_queries.md) | Cypher 101 walkthrough on the recurring anchors (Toy Story, Tom Hanks, user 196, Comedy) |
| [docs/10_sql_vs_cypher.md](docs/10_sql_vs_cypher.md) | SQL vs Cypher side-by-side: scope decisions behind the six paired examples (T-16) |
| [docs/11_strategy_genre_affinity.md](docs/11_strategy_genre_affinity.md) | Scope decisions behind Strategy 1 (genre affinity) — score formula, cold-start contract, global-seeds explainability (T-19) |
| [docs/12_strategy_director_actor.md](docs/12_strategy_director_actor.md) | Scope decisions behind Strategy 2 (director/actor affinity) — multi-hop traversal, OR-joined routes, per-rec seed chains, billing filter (T-20) |
| [docs/13_strategy_collaborative_filtering.md](docs/13_strategy_collaborative_filtering.md) | Scope decisions behind Strategy 3 (collaborative filtering) — hybrid peer definition, combined-product score, per-rec peer chains (T-21) |
| [docs/14_strategy_composite_multi_signal.md](docs/14_strategy_composite_multi_signal.md) | Scope decisions behind Strategy 4 (composite multi-signal) — weighted Reciprocal Rank Fusion of 1/2/3, per-rec via_strategies + chains (T-22) |
| [docs/15_unified_interface.md](docs/15_unified_interface.md) | Scope decisions behind the unified `get_recommendations()` interface — display-string dispatch, kwargs pass-through, ValueError on unknown strategy (T-23) |
| [docs/16_streamlit_user_profile.md](docs/16_streamlit_user_profile.md) | Debugging reference for the User Profile screen — cache pitfalls, empty-state behavior, depth-1 neighborhood query shape (T-24) |
| [docs/17_streamlit_recommendation.md](docs/17_streamlit_recommendation.md) | Debugging reference for the Recommendation Engine screen — button-gated dispatch via `get_recommendations()`, per-strategy explanation rendering, session_state pattern (T-25) |
| [docs/18_streamlit_graph_explorer.md](docs/18_streamlit_graph_explorer.md) | Debugging reference for the Graph Explorer screen — 2-step search/pick/render flow, structured per-edge-type Cypher (not generic depth-2), `:COLLABORATED_WITH` rendering (T-26) |
| [docs/19_streamlit_polish.md](docs/19_streamlit_polish.md) | Debugging reference for the cross-cutting UX polish — central `safe_run_query` error wrapper, first-load empty states, sidebar title + captions + Clear-all-caches button (T-27) |
| [notebooks/01_eda.ipynb](notebooks/01_eda.ipynb) | Exploratory data analysis of MovieLens 100K |
| [notebooks/02_tmdb_enrichment.ipynb](notebooks/02_tmdb_enrichment.ipynb) | TMDB enrichment pipeline (matches → retries → manual fallbacks) |
| [notebooks/03_graph_schema.ipynb](notebooks/03_graph_schema.ipynb) | Full schema design doc: CQs, node/relationship specs, constraints, decision log |
| [notebooks/04_load_nodes.ipynb](notebooks/04_load_nodes.ipynb) | Loads every node label into AuraDB (idempotent `MERGE`) |
| [notebooks/05_load_relationships.ipynb](notebooks/05_load_relationships.ipynb) | Loads every movie-side relationship type into AuraDB |
| [notebooks/06_load_user_attributes.ipynb](notebooks/06_load_user_attributes.ipynb) | Loads `:HAS_OCCUPATION` and `:HAS_GENDER` edges |
| [notebooks/07_collaborated_with.ipynb](notebooks/07_collaborated_with.ipynb) | Computes and writes `:COLLABORATED_WITH` from shared `:FEATURES_ACTOR` edges |
| [notebooks/08_verification.ipynb](notebooks/08_verification.ipynb) | Runs all five integrity checks against the loaded graph |
| [notebooks/09_cypher_queries.ipynb](notebooks/09_cypher_queries.ipynb) | Walks Cypher 101 — `MATCH`, `WHERE`, `RETURN`, `WITH`, multi-hop — on recurring anchors |
| [notebooks/10_sql_vs_cypher.ipynb](notebooks/10_sql_vs_cypher.ipynb) | Six paired SQL-on-SQLite ↔ Cypher-on-Neo4j examples |
| [notebooks/11_strategy_genre_affinity.ipynb](notebooks/11_strategy_genre_affinity.ipynb) | Walks Strategy 1 end-to-end on user 196 — phase-by-phase Cypher, unified query, function wrapper, knobs, cold-start |
| [notebooks/12_strategy_director_actor.ipynb](notebooks/12_strategy_director_actor.ipynb) | Walks Strategy 2 end-to-end on user 196 — phase-by-phase Cypher, unified query, function wrapper, knobs, cold-start |
| [notebooks/13_strategy_collaborative_filtering.ipynb](notebooks/13_strategy_collaborative_filtering.ipynb) | Walks Strategy 3 end-to-end on user 196 — phase-by-phase Cypher, unified query, function wrapper, knobs, cold-start |
| [notebooks/14_strategy_composite_multi_signal.ipynb](notebooks/14_strategy_composite_multi_signal.ipynb) | Walks Strategy 4 end-to-end on user 196 — four phases as standalone Cypher, CALL-subquery unification, function wrapper, knobs, cold-start |
| [CLAUDE.md](CLAUDE.md) | Project conventions and locked design constraints |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |
