# EDA Analytics Skill

A six-stage analytical pipeline for Claude Code that turns raw transactional business data into a validated, confidence-labeled set of findings and dashboard-ready Plotly charts. Each stage ends at a mandatory checkpoint — Claude Code stops, presents an output notebook for review, and waits for analyst follow-ups, orientation and confirmation before continuing. The result is an auditable analytical record: every finding has an effect size, a confidence label with documented justification, and a segment breakdown, not just a number in a notebook.

## Repository Structure

| Path | Contents |
|------|----------|
| `SKILL.md` | Central skill file: core philosophy, pipeline overview, lesson index, engagement modes |
| `PLATFORMS.md` | Deployment reference for non-local environments (currently: Databricks) |
| `references/stages/` | Per-stage execution specifications (`stage1.md` through `stage6.md`, plus `stage4av.md`) |
| `references/lessons.md` | Methodological principles organized by type (data quality, statistical validity, technical execution, and others) |
| `references/industry/` | Domain-specific pattern catalogs and reference files (see scope note below) |
| `references/scripts/` | Python implementations of cataloged analytical patterns |

## Industry Library Scope

The domain files in `references/industry/` currently cover **retail and wholesale** only. The universal statistical methods (`statistical-methods.md`) and the patterns catalog apply to any sector. For engagements outside retail or wholesale, the domain-specific files will not be relevant — use Stage 3's web research step (§3.2) to build the industry context that would otherwise come from pre-loaded domain files. The analytical pipeline and all validation gates are sector-agnostic; only the pre-loaded domain knowledge is scoped.

## Installation

**Local:**

```bash
git clone https://github.com/sebastianrupani/factored-eda-skill.git ~/.claude/skills/user/eda-analytics
```

**Databricks:** The skill files must live on a persistent path — DBFS or a workspace Git folder — not on ephemeral cluster-local storage. See `PLATFORMS.md` for the full setup guide.

## New Analyst Quick Start

### What to read before starting

Read `SKILL.md` once before your first engagement: the Core Philosophy and Engagement Modes sections specifically. These establish the mental model the pipeline operates on. Do not preload the stage files — there are ten of them, they are detailed, and loading them all at once wastes your context budget. The skill instructs Claude Code to read each stage file only when that stage begins. You will not miss anything.

### Starting an engagement

Invoke Claude Code and describe the dataset location and client context. Claude Code will create the project folder structure and ask you to confirm `PROJECT_ROOT` — the absolute path where all engagement output is written. Declare it explicitly. On Databricks, this must be a DBFS path; see `PLATFORMS.md`. Then declare the engagement mode (Standard or Deep — covered below). Claude Code handles the rest of Stage 1 through the checkpoint.

### Your role vs Claude Code's role

Claude Code executes analytical work: data profiling, hypothesis listing, statistical testing, visualization, and writing every output file. Your role is to review canonical output files and notebooks at each checkpoint, make the two significant scope decisions (engagement mode and hypothesis filtering at Stage 3), and constantly critizise, adjust, re-scope and supply domain context about the client's business that cannot be inferred from the data alone.

Do not try to direct individual analytical steps within a stage — Claude Code follows the stage specification. Intervene at the checkpoint. Push back on findings that don't hold up, provide context that changes the interpretation, or flag a hypothesis the data supports but the client's business model rules out. That input is the one thing Claude Code cannot supply.

### Checkpoints

Every stage ends with a checkpoint message and stops. At each checkpoint you have two things to review: the output file in other/ (e.g., other/stage3_research_brief.md) and the stage notebook in notebooks/. The canonical output is a structured markdown file containing every finding, decision, and constraint flag from that stage — readable without executing any code, and the file Claude Code uses to re-establish context in a new session. The notebook is your working interface: it contains the full analytical code, outputs, and visualizations that produced those findings. Review both before confirming. If something looks wrong or you want to modify the work done by Claude, correct it at the checkpoint. Once you confirm, the prior stage's decisions are locked and the next stage begins.

Checkpoints exist because a finding that passes automated validation gates but fails your domain knowledge check is best caught before it becomes a chart in the deliverable. The checkpoint is the moment the analyst's judgment enters the pipeline.

### Engagement mode: Standard vs Deep

Declare mode at Stage 1. The mode determines analytical depth at seven specific operations — it does not change the pipeline structure, which runs identically in both modes.

**Standard** is the right default for most client engagements. It skips the formal causal direction test and bootstrap ranking stability for strategic findings (Tier A), limits the cross-dimensional validation pass (Stage 4a-V) to official dimensions only, applies temporal stability only to strategic findings, skips the macro data options, and uses a single narrative depth for all HIGH confidence findings.

**Deep** runs the full gate battery. Choose it when causal claims will be scrutinized, when ranking stability directly affects a high-stakes recommendation, or when the client context warrants macro data integration.

Mode can be adjusted mid-engagement at any stage checkpoint — depth upgrades are always available without justification, downgrades require a one-line reason logged in the output. The Stage 1 declaration is a starting point, not a commitment.

### Hypothesis filtering at Stage 3

After Stage 3 builds the full three-tier hypothesis floor, Claude Code presents the hypotheses grouped by analytical category, with a one-line signal for each — what the hypothesis could reveal if confirmed. You select which hypotheses proceed to Stage 4c. A soft cap guides the selection: 8 hypotheses in Standard mode, 12 in Deep. You can go above the cap with a one-line justification. Hypotheses you don't select are documented as scope-deferred, not analytically rejected — a distinction that matters at Stage 6, where scope-deferred hypotheses are treated as candidates for the next engagement rather than ideas that didn't hold up.

This is the most consequential decision you make mid-pipeline. The cap exists because Tier A hypothesis testing is thorough; an uncapped floor leads to shallow treatment of every hypothesis.

### The learning loop

Stage 6 is the skill update stage. After each engagement, Claude Code reviews `other/skill_notes.md` — a running notes file maintained incrementally at the end of every stage — and scans notebooks for `[SKILL-CANDIDATE]` tags flagged during Stage 4b exploration. It proposes new or updated rules for the skill files, which you review and confirm before anything is written. This is how the skill improves: patterns that appear in your engagements become encoded rules that apply to all future ones.

If you skip Stage 6, the engagement closes cleanly. The analytical lessons stay in the notes file and don't enter the skill.

---

## Databricks

See `PLATFORMS.md` for cluster setup, `PROJECT_ROOT` configuration, library installation, auto-termination keep-alive, and OAuth token recovery.