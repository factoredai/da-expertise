# PLATFORMS.md — Deployment Reference

The EDA skill runs locally without any platform-specific configuration. This document covers deployment on Databricks, where several default assumptions the skill makes about the filesystem do not hold.

---

## Databricks

### Skill file location

Databricks clusters have local storage, but it is ephemeral — when a cluster terminates, the local filesystem is destroyed. If you clone the skill repository to a local path on the cluster (e.g., `/home/ubuntu/factored-eda-skill`), those files will not be present when the cluster restarts and the skill will be unavailable in a new session.

Install the skill files on a path that persists independent of cluster state. Two options work: a DBFS path under a mounted storage container, or a Databricks workspace Git folder attached via the repo integration. The workspace Git approach has the advantage of version-controlled updates. Either way, the skill directory must be readable from any cluster without manual reinstallation each time.

### PROJECT_ROOT

**Set PROJECT_ROOT to a DBFS path, not a local path.** This is the most important Databricks-specific configuration decision in the entire skill. Everything the skill produces — canonical output files, the constraint register, notebooks, the running notes file — is written under PROJECT_ROOT. If PROJECT_ROOT points to a local cluster path, all of that output is destroyed when the cluster terminates.

Use a path on a mounted storage container:

```
/dbfs/mnt/[mount-name]/[client-name]/[engagement-name]/
```

DBFS paths (`/dbfs/mnt/...`) map to Azure Data Lake, S3, or GCS depending on your workspace configuration. Files written there survive cluster termination and are accessible from any cluster that mounts the same storage. Confirm the mount exists and is writable before starting Stage 1.

If you are unsure which mount to use, ask your workspace administrator before beginning — do not use a local path and assume it will persist.

### Python libraries

Standard Databricks clusters include pandas, numpy, scipy, scikit-learn, matplotlib, and plotly. Two additional libraries must be installed at the start of each session:

```python
%pip install mlxtend statsforecast
```

Run this in a notebook cell, not the Web Terminal. The `%pip` magic installs into the cluster's Python environment and makes the libraries available to all subsequent notebook cells in the session. Installation takes 30–60 seconds and does not need to be repeated until the cluster restarts.

### Auto-termination

Databricks auto-termination tracks notebook cell execution activity, not terminal activity. Running Claude Code in the Web Terminal — even continuously — does not reset the idle timer. If no notebook cells execute for the configured idle period (typically 30–120 minutes depending on workspace settings), the cluster will terminate mid-session.

To prevent this during extended terminal sessions, run a lightweight notebook cell periodically:

```python
# keep-alive
print("alive")
```

This cell can be run in any open notebook — it does not need to be in the engagement notebook.

Running this every 20–30 minutes is sufficient. If the cluster does terminate before you catch it, restart it, re-run the `%pip install` cell above, and continue. As long as PROJECT_ROOT points to DBFS, no output is lost.

### OAuth token expiry

Databricks OAuth tokens expire periodically. If Claude Code loses workspace access mid-session — authentication errors, inability to write files — re-authenticate using your standard Databricks login and resume. All canonical output files written to DBFS before the token expired are intact. Resume from the last completed stage checkpoint: the skill's canonical output files in `other/` contain everything needed to re-establish context without reopening any notebook.
