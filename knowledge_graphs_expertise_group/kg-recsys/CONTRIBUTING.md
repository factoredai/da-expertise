# Contributing Guide

This project is being built by a small team of course collaborators.
This guide covers everything you need to contribute effectively.

---

## Getting Started

Follow the setup walkthrough in [docs/01_setup.md](docs/01_setup.md) —
it covers environment, credentials, and how to verify your Neo4j connection.

---

## Branching Convention

Work on a dedicated branch per task, using the task ID from the tracker:

```
feature/<task-id>-short-description
```

Examples:
- `feature/t-07-tmdb-enrichment`
- `feature/t-15-cypher-101-notebook`

---

## Pull Requests

- Open a PR against `main` when your task is ready for review
- **At least one approval from another team member is required before merging**
- Keep PRs scoped to a single task — avoid bundling unrelated changes

---

## What's Fixed vs. What's Open

**Fixed — discuss before changing:**
- Graph schema (node labels, relationship types, property names)
- Recommendation strategies (4 defined, Cypher-only, no ML fallbacks)
- Stack choices (Neo4j, Streamlit, pyvis)

**Open — contribute freely:**
- Notebook content and explanations
- Documentation and course copy
- Cypher query implementations in `queries/`
- Streamlit UI details

---

## Conventions by Artifact

**`queries/*.cyp`**
- Every strategy query must return an explainability path
- Match the existing naming convention (`strategy_N_name.cyp`)
- Include a comment header describing the logic and expected outputs

**`notebooks/`**
- Teaching tone: explain the *why*, not just the *what*
- Step-by-step structure — one concept per cell block
- Audience has no assumed ML background; assume SQL familiarity

**`docs/`**
- Target audience: Data Analysts, ML Engineers, Data Engineers
- Keep language concrete — use examples over abstract descriptions
- Reference the relevant notebook where applicable
