## Stage 4b — Autonomous Exploration

**Goal:** Interrogate the data for surprises. Clean prompt — zero enumerated items.

**Analytical mode: INTERROGATE** — What is surprising, contradictory, or actionable?

### Pre-Flight (Read Before Beginning Exploration)

Before writing any exploration code, read `$PROJECT_ROOT/other/stage3_research_brief.md`. This step is mandatory whether or not Stage 4b begins in a new session.

- **Recover the selected hypothesis floor** — the §3.6-filtered list with each hypothesis's H-number from the Stage 3 floor. This is the reference set that distinguishes Stage 3 floor hypotheses from Stage 4b additions.
- **Enable origin tagging** — the Stage 4b canonical output must tag every hypothesis by origin: Stage 3 floor hypotheses carry their H-number from `stage3_research_brief.md`; all hypotheses added during Stage 4b are tagged [4b-added] alongside their assigned H-number. This tagging is not possible without reading `stage3_research_brief.md` first.

Do not begin exploration until `stage3_research_brief.md` has been read and the selected hypothesis floor is in context.

### Batch Protocol (→ Context Preservation)

**Batch size:** Conditional. If total findings stay at or below 8, no batching — cross-finding synthesis requires shared context and is the primary value of this stage. If findings exceed 8, batch at 4–5 findings per pass. The second-order checklist and Consultant's First-Day Gate serve as natural bounds.

**Self-interruption (when batching):** After each batch, stop and present the batch summary. Include the Consultant's First-Day Gate assessment: "Of the findings so far, which 3 would make a client lean forward?"

**Structural self-check (per finding):**
- [ ] Trigger reason documented (what pattern in the data triggered this investigation)
- [ ] "What was expected" and "What was found" both present
- [ ] Finding tier assigned (A / B / C)

### The Four Moves

**Mode-conditional scope:** In Standard mode, apply Moves 1 and 2 only. In Deep mode, apply all four moves. The declared mode is recorded in `other/stage1_catalog.md`.

1. **Condition and compare:** For any entity whose presence is large enough that excluding it would materially change an aggregate finding, compare with vs. without. Data-derived cluster assignments from Stage 2.9 are first-class conditioning candidates — they may capture behavioral structure that official categories miss.
2. **Cross two metrics:** Intersect metrics examined independently in 4a Move 2 is typically the highest-yield exploration move — if constrained, prioritize it.
3. **Distributions not averages:** For every mean reported in 4a, examine the full shape
4. **Challenge assumptions:** Test the opposite of what a smart person would assume

**Constraint detection rule:** When examining temporal amplitude ratios across entities, identify any entity whose amplitude is a clear outlier relative to the distribution of amplitudes across all entities in the same dimension. Extreme amplitude outliers almost always reflect a regulatory, operational, or supply constraint rather than genuine demand variation. Investigate the constraint before interpreting as consumer behavior.

### Second-Order Checklist (mandatory before proceeding)

*This is the Stage 4b execution-time version of SKILL.md's Second-Order Analysis Checklist. Mode-conditional items below reflect the Engagement Modes table (→ SKILL.md § Engagement Modes — Standard and Deep).*

- [ ] Conditional splits on high-frequency entities
- [ ] Lifecycle curves across any sequence variable
- [ ] Quadrant analysis crossing top two metrics
- [ ] Distribution shapes for all means from 4a *(Deep mode only — maps to Move 3)*
- [ ] Cross-correlation matrix flagging unexpected sign directions
- [ ] Dual-spine divergence: for any finding where both official and data-derived groupings exist, check whether the segment status changes depending on which grouping is used

### Consultant's First-Day Gate

Before moving to 4c, answer:
> **If you had 30 minutes with a client who knows their business but has never seen this data, what 3 findings would make them lean forward?**

If no finding surprises, go deeper.

### Required Output
- Autonomous findings with trigger reasons (→ N5)
- Each finding: what was expected, what was found, why it matters
- **Exploration is uncapped. Reporting is curated.**

Explore as broadly as the data and time allow. Do not stop exploring because you have found 8 things. When preparing the Stage 4b output, select the findings that best satisfy the Consultant's First-Day Gate — the ones that would make a client lean forward. Present a maximum of 8 findings in the checkpoint summary, ranked by surprise value and actionability. Document additional findings that did not make the cut in an Exploration Notes section — they may become hypotheses in 4c or skill candidates in Stage 6.

**Finding tier assignment for autonomous findings:** Autonomous findings from 4b do not come from the hypothesis floor, so the Tier 1/2/3 → C/B/A default mapping does not apply directly. Instead, assign the finding tier based on the nature of the finding itself: if it is a descriptive observation (a distribution shape, a ranking), assign Tier C. If it reveals a contrast or comparison, assign Tier B. If it directly implies a strategic action, assign Tier A. Document the tier assignment alongside the trigger reason.

**[SKILL-CANDIDATE] tagging rule:** If any finding during Stage 4b represents an analytical move or pattern not present in `references/industry/patterns-catalog.md`, tag it with [SKILL-CANDIDATE] in the notebook cell and include a one-line description of the generalizable pattern it represents. These candidates are the primary input to Stage 6a Learning Harvest.

### Multiple Comparisons Correction (→ S2)

If the number of patterns explored autonomously in Stage 4b exceeds 10, apply BH-FDR correction (Benjamini-Hochberg False Discovery Rate) over all p-values generated during exploration before those findings enter the Stage 4d audit.

**Procedure:**
1. List all p-values from tests executed in 4b in ascending order.
2. Calculate the BH-adjusted threshold for each: `p_threshold_i = (i / N) × alpha`, where `i` = test rank, `N` = total tests, `alpha` = 0.05.
3. The largest p-value that is still smaller than its BH threshold defines the cutoff. All tests above that cutoff are degraded to FRAGILE regardless of their original p-value.
4. Document how many 4b findings survived the correction and how many were degraded.

If the number of explored patterns is 10 or fewer, the correction is not mandatory but the decision not to apply it must be documented.

Note: This correction applies to findings generated during Stage 4b autonomous exploration. Findings from the Stage 3 hypothesis floor have their own correction applied in Stage 4c step 6 (→ S2).

### Canonical Output

After completing all Stage 4b exploration and curation, write `$PROJECT_ROOT/other/stage4b_exploration.md`. This is the Stage 4b canonical output per SKILL.md Rule 7 — the session-portable record Claude Code reads for continuity in Stage 4c. The notebook remains the analyst's full working interface and the primary review surface; `stage4b_exploration.md` is what Claude Code reads to re-establish Stage 4b context without opening the notebook.

`other/stage4b_exploration.md` must contain:
- **Engagement mode and moves applied** — Standard (Moves 1–2) or Deep (Moves 1–4), from `stage1_catalog.md`; note which Second-Order Checklist items were skipped in Standard mode (distribution shapes)
- **Autonomous exploration findings** — all findings that passed the Consultant's First-Day Gate curation (up to 8), each with trigger reason, what was expected, what was found, why it matters, and finding tier (A / B / C); followed by any additional findings in the Exploration Notes section
- **SKILL-CANDIDATE tags** — a summary list of any findings tagged [SKILL-CANDIDATE], with the one-line description of the generalizable pattern each represents; these are the primary input to Stage 6a Learning Harvest
- **Finalized hypothesis list** — the complete hypothesis list as it enters Stage 4c, incorporating any additions from Stage 4b findings; this is the list Stage 4c will work from. Each hypothesis should indicate its origin: Stage 3 floor hypotheses carry their original H-number from `stage3_research_brief.md`; Stage 4b additions are tagged [4b-added] alongside their H-number

Write the file as structured markdown: one section per content area above, suitable for direct reading without executing any code.

### Running Notes Update

Before the checkpoint confirmation, append the completed Stage 4b section to `$PROJECT_ROOT/other/skill_notes.md` with the current date and any qualifying observations. Apply the threshold test and qualifying criteria from SKILL.md § Running Notes Protocol. If no observations qualify, write "No qualifying observations."

### CHECKPOINT — User reviews 4b findings. This is the final hypothesis list for Stage 4c.
> "Stage 4b complete. [N] autonomous findings produced; [K] selected for the checkpoint summary, [J] in Exploration Notes. [S] [SKILL-CANDIDATE tag / SKILL-CANDIDATE tags] applied. BH-FDR correction [applied — [M] of [N] p-values tested, [D] findings degraded to FRAGILE / not applied — [T] or fewer patterns explored, decision documented]. Canonical output written to `other/stage4b_exploration.md` — please review findings and the finalized hypothesis list alongside the notebook. **The hypothesis list in `stage4b_exploration.md` is the final list Stage 4c will work from — confirm or amend before proceeding.** Ready to proceed to Stage 4c?"

**Mid-Flow Mode Adjustment:** Before confirming, assess whether anything discovered during Stage 4b — new patterns, unexpected dimension interactions, or findings elevating to Tier A — materially changes the complexity, reliability, or analytical depth of the engagement relative to the declared mode. If so, surface the specific observation and suggest a targeted adjustment for the affected stage(s). See SKILL.md § Engagement Modes — Standard and Deep for the asymmetric override rule.
