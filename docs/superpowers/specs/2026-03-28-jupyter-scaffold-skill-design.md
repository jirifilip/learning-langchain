# Jupyter Notebook Scaffold Skill — Design

## Overview

A Claude Code skill that scaffolds Jupyter/jupytext notebook research environments. Handles both first-time project setup and adding new notebook subprojects to an existing repo. Implemented as a pure instruction skill (Option A) — Claude uses its native file/edit tools directly.

---

## Entry Conditions

- **Trigger:** User asks to scaffold a Jupyter notebook project or add a new notebook subproject.
- **Guard:** Check for `pyproject.toml` in the working directory. If absent, stop and tell the user to set up a Python project first.
- **Mode detection:** If `.jupyter/jupyter_lab_config.py` does not exist → **Setup mode**. If it does exist → **Subproject mode**.

---

## Setup Mode

Runs when `.jupyter/jupyter_lab_config.py` is absent. Steps:

1. **Dependencies** — Inspect `pyproject.toml` for `jupyterlab` and `jupytext` in `[dependency-groups]` or `[project.dependencies]`. Add any that are missing.
2. **`[tool.jupytext]`** — Check for `[tool.jupytext]` section with `formats = "ipynb,py:percent"`. Add if missing.
3. **`.jupyter/jupyter_lab_config.py`** — Create with:
   ```python
   c.ServerApp.contents_manager_class = "jupytext.TextFileContentsManager"
   c.ContentsManager.default_jupytext_formats = "ipynb,py:percent"
   c.ContentsManager.notebook_dir = "notebooks"
   ```
4. **`notebooks/`** — Create the directory if it doesn't exist.
5. **Fall through to Subproject mode** — prompt for a subproject name and create the first notebook.

---

## Subproject Mode

Runs when setup is already done (or immediately after setup completes). Steps:

1. **Ask for subproject name** if not already provided (e.g. `initial_examples`).
2. **Derive folder name** using today's date: `notebooks/YYYY_MM_DD_<subprojectName>/`
3. **Create the folder.**
4. **Create `01-hello-world.py`** as a jupytext percent-format notebook:

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

# %% [markdown]
# # Hello World

# %%
print("Hello World")
```

---

## Notebook Naming Convention

```
notebooks/%Y_%m_%d_%subprojectName/%02d_%notebookName.py
```

Example: `notebooks/2026_03_28_initial_examples/01-hello-world.py`

---

## Non-Goals

- Does not scaffold the Python project itself (`pyproject.toml`, `.venv`, `.gitignore`).
- Does not install dependencies — only edits `pyproject.toml`.
- Does not create multiple starter notebooks.
