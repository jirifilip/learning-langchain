# Notebooks

Notebooks are jupytext files in the percent format (`.py`).

**Naming convention:** `notebooks/%Y-%m-%d_%subprojectName/%d_%notebookName.py`

Example: `notebooks/2026_03_28_initial_examples/01-hello-world.py`

Every notebook file must include the jupytext frontmatter:

```python
# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---
```

Cells use `# %%` for code and `# %% [markdown]` for markdown.

# Tracing

MLFlow runs in Docker via `docker-compose.yml` with the `tracing` profile. Start it with:

```bash
just trace
```

This runs `docker compose --profile tracing up -d`, starting MLFlow on `http://localhost:5000`. Notebooks connect to this via `mlflow.set_tracking_uri("http://localhost:5000")` in `notebooks/2026_03_28_initial_examples/utils.py`.

# Plans

Do not commit plans to git. Plans are ephemeral and belong in the conversation context only.
