## Stage 1 — Data Source Inventory

**Goal:** Complete map of every data source before analysis begins. This is a control document — the user confirms data completeness here.

### 1.0 Create Project Folder Structure

**Declare `PROJECT_ROOT` first.** Before creating any folder or file, explicitly set and confirm `PROJECT_ROOT` as the absolute path of the project root directory. The correct value depends on the deployment environment — if the environment is unclear, ask the user before proceeding. Platform-specific defaults are documented in `PLATFORMS.md`; do not assume a value. No file or folder operation may begin until `PROJECT_ROOT` is confirmed.

**Databricks environment check.** Before accepting the PROJECT_ROOT value, check for Databricks environment indicators: the presence of a `/dbfs/` path in the filesystem, the `DATABRICKS_RUNTIME_VERSION` environment variable, or a `/databricks/` directory. If any indicator is present, confirm with the analyst that PROJECT_ROOT points to a DBFS path (e.g., `/dbfs/mnt/[mount]/[client]/[engagement]/`) and refer them to `PLATFORMS.md` for guidance on path selection. If the analyst provides a path that does not begin with `/dbfs/`, flag this explicitly: local paths on Databricks are ephemeral and all engagement output will be lost when the cluster terminates. Do not block execution if the analyst confirms the local path intentionally — but log the following warning in `skill_notes.md` under Stage 1: "PROJECT_ROOT set to a local path on a Databricks environment — output will not persist across cluster terminations." If no Databricks indicators are present, proceed without this check.

**Declare engagement mode.** Once `PROJECT_ROOT` is confirmed, ask the analyst to declare the engagement mode: **Standard** or **Deep**. Standard mode applies targeted depth reductions at seven specific operations across Stages 3, 4a-V, 4b, 4c, 4d, and 5; Deep mode runs all depth-dependent operations in full. The pipeline structure — all stages, all checkpoints, all canonical outputs — is identical in both modes. See SKILL.md § Engagement Modes — Standard and Deep for the full mode reference table and mid-flow adjustment protocol. If the mode has already been specified in the conversation, confirm it rather than re-asking.

Before any data inventory work, create the standard project folder structure per SKILL.md § Project File Structure. Create `data/`, `notebooks/`, `scripts/`, and `other/` subfolders under `PROJECT_ROOT`. If the project folder already exists with files, organize them into the correct subfolders first. Do **not** create `dashboard/` — it is created at Stage 5.

Create the Stage 1 notebook at `$PROJECT_ROOT/notebooks/stage1_inventory.ipynb`. The naming convention is `stage[N][letter]_[descriptor].ipynb` per SKILL.md Rule 2; adjust the descriptor to reflect the engagement's data domain where a more specific name is appropriate (e.g., `stage1_sales_inventory.ipynb`).

Confirm `PROJECT_ROOT`, declared engagement mode, folder creation, and notebook creation in the Stage 1 checkpoint message.

### For every table or file:

**TABLE-LEVEL:**
- Name and file identifier
- Business meaning in plain language (not technical jargon)
- Row count, column count, date range if temporal
- Granularity: what does one row represent?
- Primary key or unique identifier (confirmed or suspected)
- If multiple tables: foreign keys and join fields
- **Scale flag:** If any table exceeds ~5M rows, flag it explicitly as ABOVE NOTEBOOK-SAFE THRESHOLD. This flag drives architecture decisions in all subsequent stages (→ L1, L6).

**FIELD-LEVEL (every column):**
- Field name as it appears in the raw data
- Business meaning in plain language
- Data type (numeric, categorical, date/time, text, flag)
- Range or representative example values
- Preliminary flag: usable / suspicious / requires investigation
- Positive-events-only flag: does the fact table record only non-zero events? If yes, note that all averages are over positive-event periods only. Zeros must be imputed for demand estimation, intermittent demand classification, and stockout analysis.

### Exceptional Data Structures (Mandatory)

Whenever the dataset contains structural elements that deviate from the standard row-per-entity pattern, explain them **before any analysis begins**. The explanation must answer three questions:

1. **What is this structure?** (plain language, no assumed prior knowledge)
2. **Why does it exist?** (business or technical reason)
3. **What does it mean for what we can and cannot analyze?**

Common exceptional structures to watch for:
- Competition/ML splits (train/test/eval sets)
- Dual fact tables (prior history + current orders)
- Right-censored or capped fields (e.g., days_since_prior capped at 30)
- Pre-filtered populations (only users with N+ orders)
- Synthetic, modeled, or imputed data columns
- Hierarchical or nested identifiers
- Mid-dataset schema introductions (a column that begins being collected partway through the dataset, creating a structural analysis window — identify the exact boundary date and document which analyses are restricted to the post-introduction period)
- Purged dimension rows (dimension keys present in fact tables but absent from the dimension table — distinct from "Off" or "Inactive" status flags on rows that are still present. Common in data warehouses with periodic dimension maintenance. Identify by join yield < 100% and contiguous key-range gaps. Document the number of orphaned keys and which analyses cannot be enriched.)
- Scenario-replicated tables (fact tables containing identical row counts for multiple planning scenarios such as Actual/Budget/Forecast. The effective analytical size for most analyses is rows/N_scenarios. Note this in the scale flag assessment — a 7.5M row table with 3 scenarios is effectively 2.5M per scenario, potentially below the notebook-safe threshold.)

### CLI Output Richness Rule

The summary output printed to the CLI after data inventory must go beyond row counts and column names. It must include:
- **Record-level examples** (3-5 sample rows per table)
- **Value ranges** for every numeric field (min, max, median)
- **Key distributions** (top 5 values for categorical fields, histogram shape for numeric)
- **Enough context** that the analyst can form a mental model of the dataset from terminal output alone without opening a notebook

**Test:** If the CLI output wouldn't help a new analyst understand what they're working with in 60 seconds, it is not detailed enough.

### Large-Table Profiling Recipe (→ L7)

For tables above the notebook-safe threshold, use this five-step profiling procedure:
1. Read the header plus a small sample of rows (e.g., first 100) for schema detection and sample values
2. Count total rows via a single-column chunked read — never attempt to load the full table
3. Read the last few rows (e.g., via `tail`) for end-of-range date or ID values
4. Sample a manageable subset for distribution statistics (percentiles, skewness, value counts)
5. Stream the full file column-by-column to count nulls per field

This procedure produces all statistics required for the field-level catalog without loading the full table into memory.

### Relationship Handling

**Single table:** Note explicitly. Scan for denormalization signals (repeated entity names suggesting embedded joins). Document collapsed dimensions and analytical limitations this creates.

**Multiple tables:** Map the join structure. Compute preliminary join yield for every proposed join key. Flag any entity-dimension join yield (e.g., store_nbr, item_nbr) below 90% for Stage 2 investigation. Date-reference joins (e.g., daily sales to trading-day-only oil prices) often have inherently sparse coverage by design — for these, document the expected coverage pattern and the planned imputation method rather than flagging as a quality issue. Do not silently proceed with a low-yield join.

### Impossible Questions (Lightweight)

After the field-level catalog is complete, document 2–5 questions the data **cannot** answer. Focus on the most consequential impossibilities — the ones that would otherwise waste hypothesis design time in Stage 3. Common examples: no revenue/price data prevents margin analysis, no customer IDs prevents basket or segmentation analysis. Present these in the Stage 1 checkpoint so the user can supply supplementary data before the pipeline advances.

### Segmentation Spine

After the field-level catalog, identify all dimensions available for segmentation and document them as the **segmentation spine** for this engagement (see SKILL.md § Segmentation Spine and Default Segmentation Protocol). For each dimension in the spine, compute the volume share distribution. Flag an entity as a dominant entity candidate when its volume share is visibly disproportionate relative to other entities in the same dimension — meaning its inclusion could plausibly change aggregate statistics in a materially different direction than the rest of the population. When in doubt, flag with a sidenote reporting the share gap and let the analyst decide before Stage 4a begins. The assessment is qualitative and distribution-relative — no fixed threshold applies. Check all primary dimensions, not just the most obvious one. Dominant entities require priority conditioning throughout the analysis.

### Required Output
- One markdown header per table
- One styled pandas DataFrame per table (field names, types, non-null counts, sample values)
- Relationship map markdown cell (if multiple tables)
- Exceptional data structure explanations (if any)
- Summary: total tables, total fields, date range, flagged fields, join yield results, **scale flags**
- **No analysis. No charts. No insights. Description only.**

### Canonical Output

After completing all inventory work, write `$PROJECT_ROOT/other/stage1_catalog.md`. This is the Stage 1 canonical output per SKILL.md Rule 7 — the session-portable record Claude Code reads for continuity in later stages. The notebook remains the analyst's full working interface and the primary review surface; `stage1_catalog.md` is what Claude Code reads to re-establish context without opening the notebook.

`other/stage1_catalog.md` must contain:
- **Declared engagement mode** — Standard or Deep, for reading by subsequent stages without re-asking
- **Field-level catalog** — every table and field with data types, value ranges, and usability flags
- **Relationship map** — join structure, join yields, and any low-yield flags
- **Segmentation spine** — all identified dimensions, dominant entities, and volume share notes
- **Impossible questions** — the 2–5 questions the data cannot answer
- **Scale flags** — tables above the notebook-safe threshold, with row counts and any scenario-replication adjustments

Write the file as structured markdown: one section per content area above, suitable for direct reading without executing any code.

### Running Notes Initialization

As the final step before the checkpoint confirmation, create `$PROJECT_ROOT/other/skill_notes.md` with the full stage skeleton pre-populated (one section per stage from Stage 1 through Stage 6, each with a date placeholder and an empty bullet). Seed the Stage 1 section with any qualifying observations from this stage — rules that didn't work as documented, patterns the skill doesn't cover, rules that fired incorrectly, ambiguities requiring judgment calls, or generalizable patterns. Apply the threshold test from SKILL.md § Running Notes Protocol. If no observations qualify, write "No qualifying observations." — do not leave the section empty without explanation.

### Checkpoint
> "Stage 1 complete. `PROJECT_ROOT` set to `[path]`. Engagement mode: **[Standard/Deep]**. Project structure: [project-name]/ created with data/, notebooks/, scripts/, other/ subfolders; `notebooks/[notebook-name].ipynb` created. Inventoried [N] table(s) with [M] total fields covering [date range]. [K] tables above notebook-safe threshold (~5M rows). [J] fields flagged for investigation. [E] exceptional structures documented. [I] impossible questions identified. Canonical output written to `other/stage1_catalog.md` — please review alongside the notebook before confirming. Ready to proceed to Stage 2?"
