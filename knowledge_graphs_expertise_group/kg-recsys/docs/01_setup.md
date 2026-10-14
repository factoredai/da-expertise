# Setup Guide

End-to-end instructions to take a blank machine to a populated graph plus a running Streamlit demo. Estimated time: **~60 minutes** if nothing breaks.

> Looking for the course shape (modules, objectives, learning path) instead? See [docs/00_overview.md](00_overview.md).

---

## 0. What you'll have when you finish

- A free **Neo4j AuraDB** instance loaded with the MovieLens 100K knowledge graph (~10k nodes, ~110k edges)
- A local **conda env** with every dependency installed
- The **Streamlit demo** running locally with all three screens working
- A **3-query verification** confirming the data loaded correctly

When you finish here you can open [notebook 01 (EDA)](../notebooks/01_eda.ipynb) and start the course.

---

## 1. Prerequisites

- Python 3.10+ with [conda](https://docs.conda.io/en/latest/miniconda.html) (Miniconda or Anaconda)
- A web browser + email for AuraDB signup
- ~2 GB free disk (mostly the conda env)

---

## 2. Create your Neo4j AuraDB Free instance

1. Go to [console.neo4j.io](https://console.neo4j.io) and sign up / sign in.
2. Click **New Instance** → **AuraDB Free**.
3. Name it (e.g. `kg-recsys`) and pick the closest region.
4. Click **Create Instance**.
5. **Download the credentials file** — it appears **once**. If you lose it, you must rotate the password from the instance settings page.
6. Wait until the instance status shows **Running** in the console (~60 seconds).
7. Keep the credentials file open — you'll paste from it in Section 5.

> Free-tier AuraDB **auto-pauses after 3 days of inactivity**. If queries start failing with `ServiceUnavailable`, resume the instance from the console.

---

## 3. (Optional) Get a TMDB API key

You only need this if you want to run [notebook 02 (TMDB enrichment)](../notebooks/02_tmdb_enrichment.ipynb) yourself. The pre-enriched data is already committed at `data/enriched/enriched_movies.csv` — the loaders work without it.

1. Create a free account at [themoviedb.org](https://www.themoviedb.org/signup) and verify your email.
2. Go to **Settings → API → Create**.
3. Request a **Developer** (free) key. Approval is usually instant.
4. Copy the **v3 API Key** — *not* the Read Access Token.

---

## 4. Clone the repo and create the conda env

```bash
git clone https://github.com/diegosanchezfactored/kg-recsys.git
cd kg-recsys
conda create -n kg-recsys python=3.10 -y
conda activate kg-recsys
pip install -r requirements.txt
```

---

## 5. Configure credentials (`.env`)

```bash
cp .env.example .env
```

Open the credentials file you downloaded in Section 2 and paste each value into `.env`:

```env
NEO4J_URI=neo4j+s://<your-instance>.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your-password>
NEO4J_DATABASE=neo4j
AURA_INSTANCEID=<your-instance-id>
AURA_INSTANCENAME=Free instance

# Only if you plan to run notebook 02 (TMDB enrichment)
TMDB_API_KEY=<your-tmdb-key>
```

> **Never commit `.env`.** It's gitignored — only `.env.example` lives in the repo.

---

## 6. Download MovieLens 100K

1. Download `ml-100k.zip` from [grouplens.org/datasets/movielens/100k](https://grouplens.org/datasets/movielens/100k/).
2. Extract it so the final layout is:

```
data/raw/ml-100k/u.data    # ratings (tab-separated, no header)
data/raw/ml-100k/u.user    # user demographics (pipe-separated, no header)
data/raw/ml-100k/u.item    # movie titles + genres (pipe-separated, no header, latin-1)
data/raw/ml-100k/...       # supporting files
```

> MovieLens 100K ships as plain-text files — **not CSVs**. `u.data` is tab-separated; `u.user` and `u.item` are pipe-separated (`|`). All three are headerless, and `u.item` uses `latin-1` encoding (for accented movie titles). The loaders know how to parse them.

The pre-enriched movie data is already in `data/enriched/enriched_movies.csv` — you don't need to generate it.

---

## 7. Verify the Neo4j connection

From the project root, with the conda env active:

```bash
python -c "from src.graph import run_query; print(run_query('RETURN 1 AS ok'))"
# Expected: [{'ok': 1}]
```

If this fails, jump to [Section 12 — Troubleshooting](#12-troubleshooting).

---

## 8. Load the graph

Run notebooks 04 → 07 end-to-end, in order. Each takes 1-3 minutes against a Free-tier instance.

| Notebook | What it loads |
|---|---|
| [04_load_nodes.ipynb](../notebooks/04_load_nodes.ipynb) | All node labels (User, Movie, Genre, Director, Actor, Occupation, Gender) |
| [05_load_relationships.ipynb](../notebooks/05_load_relationships.ipynb) | Movie-side edges (IN_GENRE, DIRECTED_BY, FEATURES_ACTOR, RATED) |
| [06_load_user_attributes.ipynb](../notebooks/06_load_user_attributes.ipynb) | User-side edges (HAS_OCCUPATION, HAS_GENDER) |
| [07_collaborated_with.ipynb](../notebooks/07_collaborated_with.ipynb) | Derived COLLABORATED_WITH edge between actors |

> **Want to learn *how* the loading works?** These notebooks teach idempotent `MERGE`, schema constraints, and how the derived edge is computed. For setup, just **Run All Cells** in each — come back for the lessons during the course.

---

## 9. Verify the data loaded

Run these three Cypher queries in [Neo4j Browser](https://console.neo4j.io) or from a Python cell using `run_query`:

```cypher
MATCH (m:Movie) RETURN count(m) AS movies;
// Expected: 1682

MATCH ()-[r:RATED]->() RETURN count(r) AS ratings;
// Expected: 100000

MATCH (u:User) RETURN count(u) AS users;
// Expected: 943
```

If all three match, the core graph is loaded correctly. For the full integrity check (5 invariants, schema, indexes), run [notebook 08](../notebooks/08_verification.ipynb).

---

## 10. (Optional) Run the TMDB enrichment yourself

The repo ships with the enriched data pre-built, so Section 8 already loaded it. Run [notebook 02](../notebooks/02_tmdb_enrichment.ipynb) only if you want to see *how* the enrichment was done — the notebook walks through TMDB API calls, retry logic, and manual fallbacks for failed matches.

Requires `TMDB_API_KEY` in `.env` (Section 3).

---

## 11. Launch the Streamlit app

```bash
streamlit run app/streamlit_app.py
```

A browser tab opens at `localhost:8501` with three screens. Sanity-check:

- **Screen 1 (User Profile):** load user `196`. You should see a depth-1 neighborhood.
- **Screen 2 (Recommendation Engine):** pick `Genre Affinity` and click **Get Recommendations**. Five movies render with explanations.
- **Screen 3 (Graph Explorer):** search `toy story`, pick a result, click **Show Subgraph**. A pyvis network renders.

If all three render, setup is complete.

---

## 12. Troubleshooting

**1. `ServiceUnavailable: Cannot reach Neo4j AuraDB`** — instance is paused. Resume from [console.neo4j.io](https://console.neo4j.io); wait until status shows **Running**.

**2. `AuthError`** — `NEO4J_PASSWORD` in `.env` doesn't match the AuraDB instance. Re-paste from the credentials file. If you lost the file, rotate the password from the instance settings page.

**3. `python-dotenv` isn't loading `.env`** — `.env` must sit in the project root (same directory as `README.md`). Both the notebooks and `src/graph.py` look there.

**4. `pip install` fails on `neo4j` or `pyvis`** — Python version mismatch. Confirm `python --version` shows 3.10.x inside the activated env. If conda gave you something else, recreate with `python=3.10` explicit.

**5. `conda activate` does nothing on Windows** — use Anaconda Prompt, not regular `cmd` / PowerShell (unless you've run `conda init powershell`).

**6. Notebook 04 fails with `FileNotFoundError: data/raw/ml-100k/u.data`** — extracted to the wrong location. The zip extracts to a folder named `ml-100k/`, which must land *inside* `data/raw/`, giving the final path `data/raw/ml-100k/u.data`.

**7. TMDB returns `401 Unauthorized`** — you used the Read Access Token instead of the v3 API Key. The free tier also rate-limits at 40 requests / 10 sec — notebook 02 handles that with backoff.

---

## 13. Where to go next

- **Why a KG? Course shape and modules** → [docs/00_overview.md](00_overview.md)
- **Start the course** → [notebook 01 (EDA)](../notebooks/01_eda.ipynb)
- **Cypher 101** → [notebook 09](../notebooks/09_cypher_queries.ipynb)
- **SQL vs Cypher side-by-side** → [notebook 10](../notebooks/10_sql_vs_cypher.ipynb)
- **The four recommendation strategies** → [notebooks 11-14](../notebooks/11_strategy_genre_affinity.ipynb)
- **Streamlit screen design notes (reference)** → [docs/16-19](16_streamlit_user_profile.md)