# Data Analytics CoE Plugin Marketplace

Welcome to the official **Data Analytics CoE** Plugin Marketplace for Claude Code and the Claude Agent SDK.

This repository serves as a centralized registry of domain-driven plugins built by our analytics expertise groups. Each plugin packages specialized prompts, domain instructions, deterministic tools, and workflows to accelerate data analysis, experimentation, modeling, and pipeline development across the organization.

---

## 📦 Available Plugins

| Plugin ID | Expertise Group / Category | Description | Included Skills |
| :--- | :--- | :--- | :--- |
| **`growth-optimization-analytics`** | Growth & Optimization | Comprehensive toolkit for statistical experimentation, variance weighting, churn forecasting, and conversion funnel attribution. | `weighting-experiment-metrics`<br>`exploratory-data-analysis`|

---

## 🚀 Getting Started

### 1. How to Add the DA CoE Marketplace

To register this marketplace in your local CLI environment, run the following command in your terminal:

**Claude Code:**
```bash
claude plugin marketplace add factoredai/da-expertise
```

**Codex:**
```bash
codex plugin marketplace add factoredai/da-expertise
```

> **Note:** Ensure you have read access to `Factored` GitHub organization and that your SSH/HTTPS credentials are configured for GitHub.

---

### 2. How to Install & Activate Plugins

Once the marketplace is registered, you can search for and install domain plugins directly into your workspace.

#### Install a Plugin
To install the **Growth & Optimization Analytics Suite**:

**Claude Code:**
```bash
claude plugin install growth-optimization-analytics@da-marketplace
```
After installation, reload your plugins or restart your Claude Code session to activate all associated skills:

```bash
/reload-plugins
```

**Codex:**
```bash
codex plugin add growth-optimization-analytics@da-marketplace 
```

#### Test an Installed Skill
Once reloaded, Claude will automatically leverage the skills based on context, or you can invoke them directly in conversation:

> *Help me evaluate whether a recent experiment was succesful*

> *I want to perform an EDA on a dataset*

---

## 🛠️ How to Contribute

We encourage expertise groups to add new skills to existing domain plugins or introduce new domain plugins.

### Repository Layout Rules

The marketplace catalog, plugins, and validation tooling live at the root of this repository (`da-expertise`), alongside the other expertise-group directories:

A plugin lives directly inside its expertise group's own directory. A directory becomes a plugin by containing a `.claude-plugin/plugin.json` manifest (Claude Code) or a `plugin.json` (Codex) and a `skills/` folder. 

The directory's name (e.g. `growth_optimization_analytics`) don't need to match the plugin's kebab-case `name` (e.g. `growth-optimization-analytics`) in that manifest.

```text
da-expertise/
├── .agents/
│   └── plugins/
│       └── marketplace.json               # Central Catalog for Portable Agent Plugins
├── .claude-plugin/
│   └── marketplace.json                   # Central Catalog Index (Auto-synced via CI)
├── growth_optimization_analytics/         # Expertise Group directory AND its plugin
│   ├── plugin.json                        # Portable Agent Plugins manifest
│   ├── .claude-plugin/
│   │   └── plugin.json                    # Claude Plugin Manifest
│   └── skills/                            # Skill Payloads
│       └── <skill-name>/
│           ├── SKILL.md                   # Primary skill prompt & metadata
│           └── reference.md               # Optional reference documentation
├── tests/, utils/, pytest.ini, requirements-test.txt  # Validation suite & sync tooling
├── MARKETPLACE.md                         # This file
├── analytics_engineering_platform/        # Other expertise-group directories
├── strategic_executive_analytics/
└── README.md                              # Top-level repo overview
```

### Contribution Workflow

1. **Fork or Branch:** Create a feature branch named `feat/<domain-or-skill-name>` from `main`.
2. **Add / Update Skills:**
   * If adding to an existing domain (e.g., `growth-optimization-analytics`), create a new folder under `growth_optimization_analytics/skills/<skill-name>/` containing a valid `SKILL.md`.
   * Update the `version` field in `growth_optimization_analytics/.claude-plugin/plugin.json` following [Semantic Versioning](https://semver.org/).
3. **Validate Manifests:** Run local validation or ensure JSON syntax is valid.
4. **Submit Pull Request:** Open a PR against `main`. Our GitHub Actions workflow will automatically validate the manifest schema and update `.claude-plugin/marketplace.json`.
5. **Release Tagging:** Upon merging to `main`, CI creates a release tag formatted as `<plugin-id>@v<semver>` (e.g., `growth-optimization-analytics@v1.0.0`).

---

## 💬 Support & Feedback

* **Maintained by:** Data Analytics CoE
* **Contact:** `juan.argueta@factored.ai`
* **Issues:** Submit feature requests or bug reports via PENDING.