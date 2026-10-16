# KG-Based RecSys — CLAUDE.md

## What This Project Is
An end-to-end Knowledge Graph recommendation system built as a **course use-case**
for Data Analysts, ML Engineers, and Data Engineers. Every design decision should
serve the teaching goal: show what a KG enables that tabular/SQL can't do easily.

## Stack — Do Not Change Without Discussion
| Layer | Tool |
|---|---|
| Dataset | MovieLens 100K + TMDB API |
| Graph DB | Neo4j AuraDB Free Tier |
| Python driver | `neo4j` official driver |
| RecSys logic | Pure Cypher queries |
| App | Streamlit + `pyvis` |
| Docs | Markdown + Jupyter |

## Graph Schema — Fixed
Do not add new node labels or relationship types without explicit discussion.

```
(:User)-[:RATED {rating: float, timestamp: int}]->(:Movie)
(:User)-[:HAS_OCCUPATION]->(:Occupation)
(:User)-[:HAS_GENDER]->(:Gender)
(:Movie)-[:IN_GENRE]->(:Genre)
(:Movie)-[:DIRECTED_BY]->(:Director)
(:Movie)-[:FEATURES_ACTOR {billing_order: int}]->(:Actor)
(:Actor)-[:COLLABORATED_WITH {movie_count: int}]->(:Actor)   # derived
```

See [`docs/03_schema_diagram.md`](docs/03_schema_diagram.md) for the visual + property/cardinality tables.

## Recommendation Strategies
All logic must be implemented as Cypher queries — no Python-side filtering or ML
fallbacks. Every result must return an explainability path.

1. Genre affinity (single-hop)
2. Director/Actor affinity (multi-hop)
3. Collaborative filtering via shared graph neighborhood
4. Composite multi-signal (weighted combination of 1–3)

## Teaching Moments — Preserve These
- SQL JOIN explosion vs. a simple Cypher multi-hop traversal
- Cold-start: a user with 1 rating still gets explainable recommendations
- Explainability path per result (e.g. "You rated Inception 5★ → Nolan → The Prestige")

## Project Structure
```
src/graph.py          — Neo4j driver connection and query helpers only
src/etl.py            — Data loading and TMDB enrichment
src/recommender.py    — 4 strategies, unified interface
app/streamlit_app.py  — 3-screen Streamlit demo
```

## Do Not
- Commit `.env` — credentials go in `.env` (gitignored); template is `.env.example`
- Add ML-based recommendation logic (embeddings, matrix factorization, etc.)
- Add new graph schema elements without discussion
- Skip the explainability path on any recommendation result
- Write code without being explicitly asked to
