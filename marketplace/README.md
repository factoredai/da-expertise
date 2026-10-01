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

To register this marketplace in your local Claude Code CLI environment, run the following command in your terminal:

```bash
/plugin marketplace add factoredai/da-marketplace
```

> **Note:** Ensure you have read access to `Factored` GitHub organization and that your SSH/HTTPS credentials are configured for GitHub.

---

### 2. How to Install & Activate Plugins

Once the marketplace is registered, you can search for and install domain plugins directly into your workspace.

#### Install a Plugin
To install the **Growth & Optimization Analytics Suite**:

```bash
/plugin install growth-optimization-analytics@da-marketplace
```

#### Activate & Reload Session
After installation, reload your plugins or restart your Claude Code session to activate all associated skills:

```bash
/reload-plugins
```

#### Test an Installed Skill
Once reloaded, Claude will automatically leverage the skills based on context, or you can invoke them directly in conversation:

> *Help me evaluate whether a recent experiment was succesful*

> *I want to perform an EDA on a dataset*

---

## 🛠️ How to Contribute

We encourage expertise groups to add new skills to existing domain plugins or introduce new domain plugins.

### Repository Layout Rules

All plugin contributions must follow this directory structure:

```text
da-marketplace/
├── .claude-plugin/
│   └── marketplace.json                   # Central Catalog Index (Auto-synced via CI)
├── plugins/
│   └── <domain-plugin-id>/                # Expertise Group Plugin (e.g., growth-optimization-analytics)
│       ├── .claude-plugin/
│       │   └── plugin.json                # Plugin Manifest (SSOT for metadata)
│       └── skills/                        # Skill Payloads
│           └── <skill-name>/
│               ├── SKILL.md               # Primary skill prompt & metadata
│               └── reference.md           # Optional reference documentation
└── README.md
```

### Contribution Workflow

1. **Fork or Branch:** Create a feature branch named `feat/<domain-or-skill-name>` from `main`.
2. **Add / Update Skills:**
   * If adding to an existing domain (e.g., `growth-optimization-analytics`), create a new folder under `plugins/growth-optimization-analytics/skills/<skill-name>/` containing a valid `SKILL.md`.
   * Update the `version` field in `plugins/<domain-plugin-id>/.claude-plugin/plugin.json` following [Semantic Versioning](https://semver.org/).
3. **Validate Manifests:** Run local validation or ensure JSON syntax is valid.
4. **Submit Pull Request:** Open a PR against `main`. Our GitHub Actions workflow will automatically validate the manifest schema and update `.claude-plugin/marketplace.json`.
5. **Release Tagging:** Upon merging to `main`, CI creates a release tag formatted as `<plugin-id>@v<semver>` (e.g., `growth-optimization-analytics@v1.0.0`).

---

## 💬 Support & Feedback

* **Maintained by:** Data Analytics CoE
* **Contact:** `juan.argueta@factored.ai`
* **Issues:** Submit feature requests or bug reports via PENDING.