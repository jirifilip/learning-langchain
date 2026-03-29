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

# Plans

Do not commit plans to git. Plans are ephemeral and belong in the conversation context only.
