# Jupyter Notebook Scaffold Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a Claude Code skill at `~/.claude/skills/jupyter-scaffold/SKILL.md` that scaffolds Jupyter/jupytext notebook environments in Python projects.

**Architecture:** A pure-instruction skill (markdown) that Claude reads and follows directly. No scripts or code generation. Two modes: Setup (first-time project config) and Subproject (add a dated notebook folder). Setup falls through into Subproject automatically.

**Tech Stack:** Claude Code Skill system (`~/.claude/skills/`), jupytext percent format, JupyterLab config API.

---

## File Structure

| Action | Path | Purpose |
|--------|------|---------|
| Create | `~/.claude/skills/jupyter-scaffold/SKILL.md` | The skill instruction document |

---

### Task 1: Create the skill directory and write SKILL.md

**Files:**
- Create: `~/.claude/skills/jupyter-scaffold/SKILL.md`

- [ ] **Step 1: Create the skills directory**

Run:
```bash
mkdir -p ~/.claude/skills/jupyter-scaffold
```

Expected: directory created with no output.

- [ ] **Step 2: Write the skill file**

Create `~/.claude/skills/jupyter-scaffold/SKILL.md` with this exact content:

````markdown
---
name: jupyter-scaffold
description: Scaffold a Jupyter/jupytext notebook research environment in a Python project. Use when the user asks to set up Jupyter notebooks, add a notebook subproject, or scaffold a research folder. Handles both first-time setup and adding new subprojects to existing repos.
---

# Jupyter Notebook Scaffold

## Guard

Check for `pyproject.toml` in the current working directory.

```bash
ls pyproject.toml
```

If it does not exist, stop immediately and tell the user:

> "No `pyproject.toml` found. Please set up a Python project first, then run this skill again."

Do NOT proceed.

---

## Mode Detection

Check whether `.jupyter/jupyter_lab_config.py` exists:

```bash
ls .jupyter/jupyter_lab_config.py
```

- **Does not exist** → run **Setup Mode**, then fall through to **Subproject Mode**
- **Exists** → skip Setup Mode, go directly to **Subproject Mode**

---

## Setup Mode

Run only when `.jupyter/jupyter_lab_config.py` does not exist.

### 1. Dependencies

Read `pyproject.toml`. Check whether `jupyterlab` and `jupytext` appear anywhere in `[dependency-groups]` or `[project.dependencies]`.

- If `jupyterlab` is missing, add it to the appropriate section (prefer `[dependency-groups]` under a `research` group, creating the group if needed).
- If `jupytext` is missing, add it the same way.
- If both are present, skip this step.

Example result in `pyproject.toml`:
```toml
[dependency-groups]
research = [
    "jupyterlab>=4.0.0",
    "jupytext>=1.16.0",
]
```

### 2. `[tool.jupytext]`

Check `pyproject.toml` for a `[tool.jupytext]` section. If absent, append:

```toml
[tool.jupytext]
formats = "ipynb,py:percent"
```

### 3. Create `.jupyter/jupyter_lab_config.py`

```bash
mkdir -p .jupyter
```

Create `.jupyter/jupyter_lab_config.py` with exactly:

```python
c.ServerApp.contents_manager_class = "jupytext.TextFileContentsManager"
c.ContentsManager.default_jupytext_formats = "ipynb,py:percent"
c.ContentsManager.notebook_dir = "notebooks"
```

### 4. Create `notebooks/` directory

```bash
mkdir -p notebooks
```

---

## Subproject Mode

Run after Setup Mode completes, or directly if setup was already done.

### 1. Get subproject name

If the user has not already provided a subproject name, ask:

> "What would you like to name this subproject? (e.g. `initial_examples`)"

Wait for their response before continuing.

### 2. Derive folder path

Use today's date in `YYYY_MM_DD` format plus the subproject name:

```
notebooks/YYYY_MM_DD_<subprojectName>/
```

Example: `notebooks/2026_03_28_initial_examples/`

### 3. Create the folder

```bash
mkdir -p notebooks/YYYY_MM_DD_<subprojectName>
```

### 4. Create the starter notebook

Create `notebooks/YYYY_MM_DD_<subprojectName>/01-hello-world.py` with exactly:

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

For reference when the user creates additional notebooks:

```
notebooks/%Y_%m_%d_%subprojectName/%02d_%notebookName.py
```

Example: `notebooks/2026_03_28_initial_examples/02-my-experiment.py`
````

- [ ] **Step 3: Verify the file was created**

Run:
```bash
cat ~/.claude/skills/jupyter-scaffold/SKILL.md
```

Expected: full skill content printed, starting with `---` frontmatter.

- [ ] **Step 4: Commit the plan and confirm skill location**

```bash
git add docs/superpowers/plans/2026-03-28-jupyter-scaffold-skill.md
git commit -m "Add implementation plan for jupyter-scaffold skill"
```

---

### Task 2: Smoke-test the skill on the current project

The current project (`learning-langchain`) already has `.jupyter/jupyter_lab_config.py`, so this will exercise **Subproject Mode** only.

- [ ] **Step 1: Invoke the skill**

Use the Skill tool:
```
skill: jupyter-scaffold
```

- [ ] **Step 2: Provide subproject name when prompted**

Respond with a test name, e.g. `test_scaffold`.

- [ ] **Step 3: Verify output**

Confirm that:
- `notebooks/YYYY_MM_DD_test_scaffold/` was created (with today's date)
- `notebooks/YYYY_MM_DD_test_scaffold/01-hello-world.py` exists
- The file contains the jupytext frontmatter and `print("Hello World")`

- [ ] **Step 4: Clean up test folder**

```bash
rm -rf notebooks/YYYY_MM_DD_test_scaffold
```
