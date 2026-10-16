# KG-Based RecSys — Full Context Handover

## What We Are Building
An end-to-end **Knowledge Graph-based Recommendation System** designed as a **course/use case** to demonstrate KG value to a technical audience. The project is meant to be followed step by step — it includes code, notebooks, an interactive app, and written documentation. It is being built by one person (Diego) dedicating ~3 hours/week over 6 weeks.

---

## Audience & Goals
- **Primary audience:** Data Analysts, ML Engineers, Data Engineers
- **Goal:** Show what a KG enables that tabular/SQL approaches can't do easily — multi-hop queries, explainability, cold-start handling
- **Format:** Jupyter notebooks (step-by-step) + Markdown docs (reference) + Streamlit app (interactive demo)
- **Key teaching moments to preserve:**
  - The "join explosion" in SQL vs. a simple Cypher traversal
  - Cold-start: new user with 1 rating still gets explainable recs
  - Recommendation explainability — show the actual graph path that produced each result

---

## Stack (Final Decisions)
| Layer | Tool | Reason |
|---|---|---|
| Dataset | MovieLens 100K + TMDB API | Small, clean, well-understood domain |
| Graph DB | Neo4j AuraDB Free Tier | No infra, hosted, built-in browser UI |
| Python driver | `neo4j` official driver | Clean, well-documented |
| RecSys logic | Pure Cypher queries | The whole point — native graph traversal |
| App | Streamlit + `pyvis` | Fastest path to interactive demo |
| Docs | Markdown + Jupyter | Notebooks for walkthrough, MD for reference |

---

## Graph Schema (Agreed Design)
```
(:User)-[:RATED {rating, timestamp}]->(:Movie)
(:Movie)-[:IN_GENRE]->(:Genre)
(:Movie)-[:DIRECTED_BY]->(:Director)
(:Movie)-[:FEATURES_ACTOR]->(:Actor)
(:Actor)-[:COLLABORATED_WITH]->(:Actor)   ← derived
(:Movie)-[:SIMILAR_TO]->(:Movie)          ← derived
```

**Node labels:** `Movie`, `User`, `Actor`, `Director`, `Genre`

**Important ontology note:** The ontology layer (class hierarchy, domain/range constraints, cardinality rules, property definitions) needs to be defined in Phase 1 before any ETL code is written. It was not added as a formal task yet but should be treated as part of T-08 (schema design). Example open decisions: can a `Director` also be an `Actor`? Is `rating` an integer or float?

---

## Recommendation Strategies (4 Levels)
All implemented as Cypher queries, ordered by complexity:

1. **Genre affinity** — user's top-rated genres → unseen movies in those genres. Single-hop. Simplest baseline.
2. **Director/Actor affinity** — user's top-rated movies → extract directors/actors → their other works. Multi-hop.
3. **Collaborative filtering via graph** — find users with overlapping high ratings → recommend what they liked that target user hasn't seen. Most complex Cypher.
4. **Composite multi-signal** — weighted combination of signals 1–3 into a single ranked list. Capstone strategy.

Each recommendation must return an **explainability path** (e.g. *"You rated Inception 5★ → Nolan directed it → he also directed The Prestige"*).

---

## Streamlit App — 3 Screens
1. **User Profile** — user ID selector, rating history table, `pyvis` subgraph of KG neighborhood
2. **Recommendation Engine** — strategy dropdown, ranked results, explanation path per result
3. **Graph Explorer** — free-form entity search (movie or actor name), renders local subgraph. Called the "wow screen" — key demo moment.

---

## Project Structure
```
kg-recsys/
├── data/
│   ├── raw/                  # MovieLens CSVs
│   └── enriched/             # After TMDB enrichment
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_graph_schema.ipynb
│   ├── 03_load_neo4j.ipynb
│   ├── 04_cypher_queries.ipynb
│   └── 05_recsys_logic.ipynb
├── src/
│   ├── etl.py                # Data loading & TMDB enrichment
│   ├── graph.py              # Neo4j connection & query helpers
│   └── recommender.py        # 4 strategies, unified interface
├── app/
│   └── streamlit_app.py
└── docs/
    ├── 00_overview.md
    ├── 01_setup.md
    ├── 02_schema_design.md
    └── 03_recsys_explained.md
```

---

## Timeline & Current Status
**Start:** May 5, 2026 · **End:** June 15, 2026 · **Pace:** 3h/week

| Week | Dates | Focus | Status |
|---|---|---|---|
| 1 | May 5–11 | Environment setup + EDA | 🔲 Not started |
| 2 | May 12–18 | TMDB enrichment + schema design | 🔲 Not started |
| 3 | May 19–25 | Full ETL into Neo4j | 🔲 Not started |
| 4 | May 26–Jun 1 | Cypher exploration + Strategies 1 & 2 | 🔲 Not started |
| 5 | Jun 2–8 | Strategies 3 & 4 + recommender.py | 🔲 Not started |
| 6 | Jun 9–15 | Streamlit app + all documentation | 🔲 Not started |

**Checkpoint to watch:** End of Week 3 (May 25) — full graph loaded and queryable in Neo4j Browser. If this is working, the rest follows cleanly.

---

## Task List (31 tasks)

### Phase 0 — Project Setup
| ID | Task | Due |
|---|---|---|
| T-01 | Create project repository and folder structure | May 6 |
| T-02 | Set up Python environment and install dependencies | May 7 |
| T-03 | Download MovieLens 100K dataset | May 7 |
| T-04 | Create Neo4j AuraDB free instance and save credentials | May 8 |
| T-05 | Obtain TMDB API key | May 8 |

### Phase 1 — Data Exploration & Schema Design
| ID | Task | Due |
|---|---|---|
| T-06 | EDA on MovieLens raw files (users, ratings, movies) | May 11 |
| T-07 | Enrich data via TMDB API (actors, directors, genres) | May 15 |
| T-08 | Design the Knowledge Graph schema + ontology | May 18 |
| T-09 | Validate schema with a small sample load into Neo4j | May 18 |

### Phase 2 — ETL: Load the Knowledge Graph
| ID | Task | Due |
|---|---|---|
| T-10 | Build entity loading scripts (Movie, User, Actor, Director, Genre) | May 21 |
| T-11 | Build relationship loading scripts (RATED, IN_GENRE, DIRECTED_BY, FEATURES_ACTOR) | May 22 |
| T-12 | Build derived relationship scripts (COLLABORATED_WITH, SIMILAR_TO) | May 23 |
| T-13 | Add Neo4j indexes and constraints | May 24 |
| T-14 | Full load validation (node counts, relationship counts, spot checks) | May 25 |

### Phase 3 — Cypher Exploration & Graph Validation
| ID | Task | Due |
|---|---|---|
| T-15 | Write Cypher 101 notebook | May 28 |
| T-16 | Document KG vs SQL multi-hop comparison | May 29 |
| T-17 | Build graph.py helper module | May 30 |
| T-18 | Validate graph neighborhood visually in Neo4j Browser | May 30 |

### Phase 4 — RecSys Logic
| ID | Task | Due |
|---|---|---|
| T-19 | Implement Strategy 1 — Genre affinity | Jun 1 |
| T-20 | Implement Strategy 2 — Director/Actor affinity (multi-hop) | Jun 1 |
| T-21 | Implement Strategy 3 — Collaborative filtering via graph | Jun 4 |
| T-22 | Implement Strategy 4 — Composite multi-signal scoring | Jun 6 |
| T-23 | Wrap all strategies in recommender.py with unified interface | Jun 8 |

### Phase 5 — Streamlit Interactive App
| ID | Task | Due |
|---|---|---|
| T-24 | Build Screen 1 — User profile view | Jun 10 |
| T-25 | Build Screen 2 — Recommendation engine | Jun 11 |
| T-26 | Build Screen 3 — Graph explorer ("wow screen") | Jun 12 |
| T-27 | Polish UX — loading states, error handling, navigation | Jun 13 |

### Phase 6 — Documentation & Course Content
| ID | Task | Due |
|---|---|---|
| T-28 | Write setup guide (environment, Neo4j, TMDB) | Jun 14 |
| T-29 | Write schema design module with ontology rationale | Jun 14 |
| T-30 | Write RecSys explained module (strategies + Cypher walkthrough) | Jun 15 |
| T-31 | Write overview doc — why KGs vs tabular/SQL | Jun 15 |

---

## Deliverables
- GitHub repo with full source code
- 5 annotated Jupyter notebooks
- Streamlit interactive demo app
- 4 Markdown course documentation files
- Excel task tracker (31 tasks, deadlines, phase color coding, status tracking) — already generated

---

## Where to Pick Up Next
The **next action is T-01** — create the GitHub repository and folder structure. After that, T-02 through T-05 are all environment/infra setup and can be done in one sitting (~90 min).

When resuming, use this prompt to re-orient a new conversation:

> *"I'm building a KG-based RecSys course project using MovieLens 100K, Neo4j AuraDB, and Streamlit. I have a full task tracker and project plan already defined. I'm starting on [CURRENT TASK ID and NAME]. Here's the full context: [paste this document]"*
