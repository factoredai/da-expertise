## Stage 4c — Formal Hypothesis Testing

**Goal:** Test the finalized hypothesis list with statistical rigor plus client-language verdicts.

### Batch Protocol (→ Context Preservation)

**Batch size:** 2–3 hypotheses per batch. This is the most context-intensive stage — each hypothesis requires the full validation gate battery, client narrative, convergent evidence search, and Simpson's check. Extensions and post-hoc analyses receive the same structural treatment as formal hypotheses; they are not addenda with relaxed requirements.

**Self-interruption:** After each batch, stop and present:
> "Batch [N] complete: [hypothesis IDs]. [1-2 sentence summary]. Context carry-forward: [cross-references to prior findings, analytical threads for next batch]. Proceeding to batch [N+1] ([hypothesis IDs]). Confirm or provide corrections."

**Structural self-check (per hypothesis, before moving to the next):**
- [ ] Finding tier assigned and validation gates listed
- [ ] All applicable gates from the gate map executed; in Standard mode, S11 and S6 are legitimately excluded for Tier A — confirm mode is recorded and exclusions are noted in the label justification
- [ ] "What this means for the client" section present with plain business language
- [ ] Convergent evidence section present (with active search against 4a and 4b findings)
- [ ] Simpson's Paradox check documented (both official and data-derived groupings if dual spine active)
- [ ] Segmentation lens specified
- [ ] Confidence label assigned with specific justification

**Thematic grouping:** Batch related hypotheses together where possible — all temporal hypotheses in one batch, all segmentation hypotheses in another. The batch size is a maximum; if a thematic group contains fewer items, complete the group and self-interrupt.

### Execution Rules

*Mode-dependent gates: S11 (step 5) and S6 (step 9) are mode-conditional for Tier A findings — behavior is specified within each step. All other steps apply identically in Standard and Deep modes. The declared mode is recorded in `other/stage1_catalog.md`.*

- For every hypothesis, first assign the finding tier (see gate map in SKILL.md), then execute the applicable gates:
  1. Run appropriate statistical test [Tier A, B]
  2. Report effect size alongside p-value (→ S3, S9) [Tier A, B]
  3. Test survival on commercially significant subset (→ S4, P6) [Tier A, B]
  4. **Confound control test:** Apply procedure S10. Report attenuation table. Apply automatic degradation rule before assigning label. (→ S10) [Tier A only]
  5. **Causal direction test (→ S11, mode-conditional):** [Tier A only]
     - **Standard mode:** For any finding that generates an action recommendation, flag the assumed causal direction in the finding narrative and note it was not formally tested: "Causal direction assumed [X → Y] — not verified (Standard mode, S11 not applied)." Skip the two-step protocol.
     - **Deep mode:** Apply S11 Step 1 (mechanical plausibility test) for all findings generating action recommendations. Apply S11 Step 2 (conditional Granger test) only if the dataset meets the temporal requirements.
  6. **Check Simpson's Paradox** — does the finding hold across all primary segments, including both official and data-derived groupings from the dual spine? If the finding holds under one grouping but reverses under the other, classify as a segmentation divergence finding. (→ S8) [Tier A, B]
  7. **Detrend before cross-series correlation (→ S12):** For time-series correlations on datasets spanning more than two years, detrend both series before computing rho. If the detrended correlation is not significant, the raw correlation is confounded by time and must not be reported as a finding. When a contemporaneous macro-indicator test is null, extend to lagged correlations at multiple period lags in both directions with BH-FDR correction before closing the hypothesis. [Tier A, B]
  8. Apply multiple comparison correction where applicable (→ S2) [Tier A, B]
  9. **Bootstrap stability for rankings (→ S6, mode-conditional):** [Tier A only]
     - **Standard mode:** Skip. Present the ranking without a stability classification. Note in the finding narrative: "Ranking stability not assessed (Standard mode, S6 not applied) — position confidence has not been tested."
     - **Deep mode:** For rankings that inform high-impact recommendations, execute the full 200x bootstrap resample per S6. Report stability classification per entity. Apply the presentation rule: Stable (≥80%) = ordered list; Qualified (60–80%) = candidate pool; Unstable (<60%) = investigate before presenting.
  10. Assign confidence label: HIGH / QUALIFIED / FRAGILE / POPULATION-ONLY. In Standard mode, S11 and S6 were not applied for Tier A findings — their absence does not prevent HIGH. A Tier A finding in Standard mode can receive HIGH if effect size meets threshold, segment stability is confirmed under both spine groupings, and no material dataset limitations apply (→ SKILL.md § Confidence Labeling System).
  11. Justify label by listing all gates run and their results. For Standard mode: note S11 and S6 as skipped (mode-dependent), confirm they are not factors in any label degradation, and include the causal direction flag from step 5 in the justification if applicable.

  **Tier C findings** skip all statistical gates — they are facts, not hypotheses. Document them with full narrative (→ N3) but no validation machinery.

### Mandatory Per-Hypothesis Output

```markdown
**Finding Tier:** [A / B / C] — [one-sentence justification]
**Validation gates to apply:** [list from gate map]

### H[N]: [Title]
**Verdict:** [CONFIRMED / REJECTED] — Confidence: [HIGH / QUALIFIED / FRAGILE / POPULATION-ONLY]

**Evidence:** [specific numbers, test results, effect sizes]

**What this means for the client:**
[Plain business language, no statistical jargon, one concrete recommendation
a grocery/retail/whatever business could act on within 12 months.
If rejected, explain what the rejection tells us about the business.]

**Convergent evidence:**
Does any analysis already executed in Stage 4a or Stage 4b point in the same
direction from a different angle? List each one with a one-sentence justification
of why it constitutes an independent confirmation (different variable, different
subpopulation, different method).

- If 1 convergent confirmation exists: record in the Stage 4d column.
- If 2 or more exist: the finding has strong convergent evidence — this
  contributes positively toward a HIGH label.
- If none exist: document "No convergent confirmation identified." This does not
  penalize the label but signals that the finding rests on a single test.

Active search rule: before closing any hypothesis in Stage 4c, explicitly
review the list of findings from 4a and 4b and ask: "Does any of these point
in the same direction from a different angle?" This review is active — do not
wait for convergence to be obvious.
```

### Rejected Hypothesis Follow-Up Rule

For every rejected hypothesis, propose at least one follow-up question before closing the test. A rejection is a finding — explain what it tells us about the business.

### Narrative Quality Rules (→ NQ1-NQ4)

- **"This matters because..."** — mandatory sentence completing the logic chain from observation to business implication
- **"The surprising part is..."** — mandatory for contrast-based findings, before the recommendation
- All statistical metrics followed by plain-language translation in parentheses
  - Example: "Cramér's V = 0.23 (moderate practical effect, comparable to the difference between weekday and weekend shopping patterns)"
- Effect size and practical significance explicitly distinguished from statistical significance

### Required Output
- All hypotheses tested with verdicts and client-language paragraphs
- Phase summary table: insight number, title, verdict, confidence, one-line finding
- Exclusion log (every dropped analysis with one-line reason)

### Canonical Output

After completing all Stage 4c hypothesis testing, write `$PROJECT_ROOT/other/stage4c_verdicts.md`. This is the Stage 4c canonical output per SKILL.md Rule 7 — the session-portable record Stage 4d reads to construct its confidence audit table without opening the notebook. The notebook remains the analyst's full working interface and the primary review surface.

`other/stage4c_verdicts.md` must contain:
- **Hypothesis verdicts** — one entry per hypothesis with: H-number, finding tier (A / B / C), verdict (CONFIRMED / REJECTED), confidence label (HIGH / QUALIFIED / FRAGILE / POPULATION-ONLY), effect size metric and value, segment status (Uniform / Amplified / Attenuated / Divergent — under both official and data-derived groupings if dual spine is active), convergent evidence count, and one-line client summary
- **Mode-dependent gate log** — for each Tier A finding: S11 status (run — [verdict] / skipped — Standard mode, causal direction flagged as [assumed direction]); for each Tier A ranking: S6 status (run — [stability classification per entity] / skipped — Standard mode, stability not assessed); Stage 4d reads this log to populate its Bootstrap Stability column and confirm gate coverage; Stage 5 reads it for narrative depth treatment of any finding where causal direction was flagged but not tested
- **Phase summary table** — the complete table from the Required Output (insight number, title, verdict, confidence, one-line finding) in markdown table form
- **Exclusion log** — every dropped analysis with one-line reason

Write the file as structured markdown: one section per content area above, suitable for direct reading without executing any code. Stage 4d reads this file directly to populate its confidence audit table.

### Running Notes Update

Before the checkpoint confirmation, append the completed Stage 4c section to `$PROJECT_ROOT/other/skill_notes.md` with the current date and any qualifying observations. Apply the threshold test and qualifying criteria from SKILL.md § Running Notes Protocol. If no observations qualify, write "No qualifying observations."

### CHECKPOINT — DO NOT PROCEED TO STAGE 4d WITHOUT USER CONFIRMATION
> "Stage 4c complete. [N] hypotheses tested: [K] confirmed, [J] rejected. Confidence labels assigned — [A] HIGH, [B] QUALIFIED, [C] FRAGILE, [D] POPULATION-ONLY. [E] hypotheses excluded with documented reasons in the exclusion log. Canonical output written to `other/stage4c_verdicts.md` — please review all verdicts and confidence labels alongside the notebook before confirming. **Every hypothesis must have a verdict before Stage 4d confidence auditing begins.** Ready to proceed to Stage 4d?"

**Mid-Flow Mode Adjustment:** Before confirming, assess whether any Tier A finding encountered during Stage 4c warrants targeted depth upgrades: a finding where causal direction is genuinely contestable in a way that could reverse the action recommendation (S11 trigger), or a Tier A ranking that will directly inform a high-stakes recommendation where position instability would materially change the advice (S6 trigger). If either condition is present, surface the observation and suggest running the relevant protocol for that specific finding even in Standard mode. See SKILL.md § Engagement Modes — Standard and Deep for the asymmetric override rule.
