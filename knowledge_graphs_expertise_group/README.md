# Knowledge Graphs Expertise Group

Home of the Data Analytics CoE's **Knowledge Graphs** work: reusable projects, walkthroughs, and reference material that show where graph databases outperform tabular/SQL approaches for analytics.

---

## 🎯 Focus

- **Graph modeling:** designing node and relationship schemas that answer real business questions.
- **Graph querying:** multi-hop traversal with Cypher, and how it compares to equivalent SQL.
- **Graph-powered applications:** recommendation, explainability, and cold-start handling on top of a knowledge graph.
- **Enablement:** step-by-step documentation so other analysts can reproduce and learn from each project.

**Key tech:** `Neo4j (AuraDB)`, `Cypher`, `Python`, `Streamlit`, `Jupyter`.

---

## 📦 Projects

| Project | Description | Directory |
| :--- | :--- | :--- |
| **KG-Based Recommendation System** | End-to-end movie recommender on a Neo4j knowledge graph (MovieLens 100K enriched with TMDB). Includes four recommendation strategies, a SQL vs Cypher comparison, a Streamlit demo, and a 19-part course-style documentation set. | [`kg-recsys/`](kg-recsys/) |

Start with [`kg-recsys/README.md`](kg-recsys/README.md), then [`kg-recsys/docs/00_overview.md`](kg-recsys/docs/00_overview.md) for the learning path.

---

## 🗂️ Directory Layout

```text
knowledge_graphs_expertise_group/
├── README.md        # This file
├── kg-recsys/       # Knowledge graph recommendation system project
├── coe-slide/       # Slide material presenting the group's work
└── context/         # Project context and planning notes
```

---

## 🚀 Getting Started

Each project is self-contained and documents its own setup. For `kg-recsys`:

```bash
cd kg-recsys
conda create -n kg-recsys python=3.10
conda activate kg-recsys
pip install -r requirements.txt
cp .env.example .env     # then fill in your own Neo4j and TMDB credentials
```

Full walkthrough, including how to create a free AuraDB instance and obtain a TMDB key: [`kg-recsys/docs/01_setup.md`](kg-recsys/docs/01_setup.md).

---

## 🔒 Security

- Never commit `.env` files, Neo4j credential downloads, or API keys. Each user creates their own AuraDB instance and TMDB key.
- Projects here use only public datasets (MovieLens, TMDB metadata). No client or proprietary data belongs in this directory.

---

## 🛠️ Contributing

Follow the repository-wide rules in the [root README](../README.md#%EF%B8%8F-repository-governance--contributions): feature branches only, at least one approved review, and every added tool or notebook documented in its folder's `README.md`. Project-specific conventions are in [`kg-recsys/CONTRIBUTING.md`](kg-recsys/CONTRIBUTING.md).

---

## 💬 Contact

Maintained by the Knowledge Graphs Expertise Group, Data Analytics CoE.
