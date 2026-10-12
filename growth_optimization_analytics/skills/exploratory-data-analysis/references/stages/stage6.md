## Stage 6 — Skill Update

**Goal:** Harvest reusable methodological lessons from the completed engagement and update the EDA skill files. This is the only stage that modifies the skill itself. Every other stage operates within the skill's existing rules.

### 6a — Learning Harvest

Review the engagement systematically using **structured artifacts only** — do not rely on unstructured conversation history as the primary source. The mandatory source documents are, in priority order:

0. **Primary source — Running Notes file:** Read `$PROJECT_ROOT/other/skill_notes.md` first. This file was populated incrementally at the end of each stage (1–5) while context was fresh. It is the **floor** for the learning harvest — every observation in this file must appear in the Stage 6d review table. Context-window recall is additive on top: it may surface additional candidates that were not captured in the notes, but the notes file takes precedence as the most reliable source because observations were recorded at the moment they occurred, not reconstructed after the fact.
1. **[SKILL-CANDIDATE] tags:** Scan the Stage 4b and 4c notebooks for cells tagged [SKILL-CANDIDATE]. These are the highest-priority candidates for new patterns — they were flagged at the moment of discovery when the analytical insight was fresh. Every [SKILL-CANDIDATE] must appear in the Stage 6d review table regardless of whether it survives abstraction and threshold audit. If it is ultimately rejected, document why.
2. **Stage 4d confidence audit table** — every finding with its confidence label, effect size, segment stability result, and any limitations noted. Candidates: new lessons about effect size interpretation, segment analysis techniques, or confidence labeling edge cases.
3. **`other/stage3_research_brief.md` — Research Context section** — every hypothesis that was proposed but deferred or excluded, including those tagged "Deferred at hypothesis filtering — scope limit, not analytical exclusion." Candidates: new boundary-check rules, new applicability filters, or refinements to the three-tier system.
4. **Documented execution failures and corrections** — any methodological pivot, code failure, kernel crash, data quality surprise, or approach that was tried and abandoned during Stages 1–5. Candidates: new lessons (Lxx, Qxx, Nxx), new stage rules, or corrections to existing rules.

For each candidate, record:
- Proposed ID (following existing numbering: M6, Q11, S17, etc.)
- Target file (SKILL.md, stages/*.md, lessons.md, or the appropriate file in references/industry/ or references/scripts/)
- Target section within that file
- One-line description of the proposed rule or update

### 6b — Abstraction Review

For every candidate from 6a, verify it contains **zero dataset-specific content**: no product names, no column names from this engagement, no client names, no hardcoded thresholds derived from this dataset's distributions.

The test: *"Would this rule make sense to someone who has never seen this dataset?"*

Any candidate that fails: either generalize it (replace specific names with generic descriptions) or discard it with a one-line reason.

### 6c — Threshold Audit

For every candidate that proposes a numerical threshold: verify it is data-derived (percentile, elbow, distribution-based) or an established industry standard with citation.

The test: *"Would this threshold be correct on a dataset 10x larger or from a different market?"*

Any fixed number from this engagement must be replaced with a data-derived method. If no generalizable method exists, discard the candidate.

### CHECKPOINT — 6a through 6c are internal preparation. Present results at 6d.

### 6d — User Review

Present the full candidate list (post-abstraction, post-threshold-audit) to the user for confirmation. Format as a table:

| ID | Target File | Section | Proposed Text (abbreviated) | New / Update |
|----|-------------|---------|----------------------------|--------------|

Include a separate "Discarded" section listing candidates removed during 6b or 6c with one-line reasons.

**Do not modify any skill file until the user confirms.**

### 6e — Skill Update Execution

Apply all confirmed changes to the target files. After all edits:

**Consistency check (mandatory):**
- Every lesson ID referenced in SKILL.md's Lesson Index must exist in `references/lessons.md`
- Every pattern ID referenced in SKILL.md must exist in `references/industry/statistical-methods.md`
- Every stage referenced in the pipeline table must have a corresponding file in `references/stages/`
- Every pattern ID in `references/industry/patterns-catalog.md` must correspond to exactly one entry in a domain file
- Every domain file pattern must have a corresponding script in `references/scripts/[domain]/`
- New patterns go into the appropriate domain file (not a monolithic file), new scripts into the scripts directory, and `patterns-catalog.md` must be updated with a new index row for every new pattern added
- Fix any broken references found

### 6f — Inventory Output

Produce a closing summary:

- **N** new lessons/rules added (with IDs)
- **M** existing rules updated (with IDs)
- **K** candidates discarded (with one-line reasons)
- **J** threshold fixes applied
- **Files modified:** list each file and number of edits

### Canonical Output

After completing all Stage 6 skill update work, write `$PROJECT_ROOT/other/stage6_skill_update.md`. This is the Stage 6 canonical output per SKILL.md Rule 7 — the engagement closure record documenting what was harvested and what changed in the skill.

`other/stage6_skill_update.md` must contain:
- **Full candidate table** — the complete 6d review table (post-abstraction, post-threshold-audit) with all confirmed candidates: ID, target file, section, proposed text, and new/update classification
- **Discarded candidates list** — all candidates removed during 6b (abstraction) or 6c (threshold audit) with one-line reasons
- **Closing inventory** — the counts and file list from 6f: new lessons added (with IDs), existing rules updated (with IDs), candidates discarded, threshold fixes applied, and files modified

Write the file as structured markdown: one section per content area above, suitable for direct reading without executing any code.

### Checkpoint
> "Stage 6 complete. Skill updated: [N] new lessons, [M] updates, [K] discarded. Files modified: [list]. Canonical output written to `other/stage6_skill_update.md`. EDA engagement closed."
