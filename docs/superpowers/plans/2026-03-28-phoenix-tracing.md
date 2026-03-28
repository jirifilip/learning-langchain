# Phoenix Tracing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Arize Phoenix as a local LLM tracing UI with a shared `setup_tracing()` utility and a `just trace` command to start the server.

**Architecture:** A `tracing` dependency group holds Phoenix packages. A root-level `tracing.py` exposes `setup_tracing()` which registers an OTEL tracer provider and instruments LangChain. The Justfile gets a `trace` recipe to start the Phoenix server.

**Tech Stack:** `arize-phoenix`, `openinference-instrumentation-langchain`, `uv`, `just`

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `pyproject.toml` | Add `tracing` dependency group |
| Create | `tracing.py` | `setup_tracing()` function |
| Create | `tests/test_tracing.py` | Unit test for `setup_tracing()` |
| Modify | `Justfile` | Add `trace` recipe |

---

### Task 1: Add tracing dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add the `tracing` dependency group**

In `pyproject.toml`, add after the existing `[dependency-groups]` section:

```toml
[dependency-groups]
research = [
    "jupyterlab>=4.5.6",
    "jupytext>=1.19.1",
]
tracing = [
    "arize-phoenix>=8.0.0",
    "openinference-instrumentation-langchain>=0.1.0",
]
```

- [ ] **Step 2: Install the new group**

```bash
uv sync --group tracing
```

Expected: resolves and installs `arize-phoenix` and `openinference-instrumentation-langchain` into `.venv`.

- [ ] **Step 3: Verify packages are available**

```bash
uv run python -c "import phoenix; import openinference.instrumentation.langchain; print('ok')"
```

Expected output: `ok`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add tracing dependency group with arize-phoenix"
```

---

### Task 2: Create `tracing.py`

**Files:**
- Create: `tracing.py`
- Create: `tests/test_tracing.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_tracing.py`:

```python
from unittest.mock import MagicMock, patch, call


def test_setup_tracing_registers_provider_and_instruments():
    mock_provider = MagicMock()

    with patch("phoenix.otel.register", return_value=mock_provider) as mock_register, \
         patch("openinference.instrumentation.langchain.LangChainInstrumentor") as mock_instrumentor_cls:

        mock_instrumentor = MagicMock()
        mock_instrumentor_cls.return_value = mock_instrumentor

        from tracing import setup_tracing
        setup_tracing()

        mock_register.assert_called_once_with(
            project_name="learning-langchain",
            endpoint="http://localhost:6006/v1/traces",
        )
        mock_instrumentor_cls.assert_called_once_with()
        mock_instrumentor.instrument.assert_called_once_with(tracer_provider=mock_provider)
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
uv run pytest tests/test_tracing.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'tracing'`

- [ ] **Step 3: Create `tracing.py`**

```python
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor


def setup_tracing():
    tracer_provider = register(
        project_name="learning-langchain",
        endpoint="http://localhost:6006/v1/traces",
    )
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
uv run pytest tests/test_tracing.py -v
```

Expected: PASS — `test_setup_tracing_registers_provider_and_instruments`

- [ ] **Step 5: Commit**

```bash
git add tracing.py tests/test_tracing.py
git commit -m "feat: add setup_tracing() utility with Phoenix OTEL integration"
```

---

### Task 3: Add `trace` recipe to Justfile

**Files:**
- Modify: `Justfile`

- [ ] **Step 1: Add the `trace` recipe**

Append to `Justfile`:

```just
trace:
    uv run python -m phoenix.server.main serve
```

The full file should look like:

```just
set shell := ["powershell.exe", "-c"]

research:
    uv run jupyter lab --config .jupyter/jupyter_lab_config.py

trace:
    uv run python -m phoenix.server.main serve
```

- [ ] **Step 2: Verify the recipe is listed**

```bash
just --list
```

Expected output includes:
```
research
trace
```

- [ ] **Step 3: Commit**

```bash
git add Justfile
git commit -m "feat: add just trace recipe to start Phoenix server"
```
