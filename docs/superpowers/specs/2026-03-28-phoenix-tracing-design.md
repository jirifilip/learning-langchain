# Phoenix Tracing Setup Design

**Date:** 2026-03-28

## Overview

Add Arize Phoenix as a local LLM tracing UI for the project. Provides span-level visibility into LangChain and LangGraph execution during notebook development.

## Dependencies

New `tracing` dependency group in `pyproject.toml`:

- `arize-phoenix` — local Phoenix server and OTEL integration
- `openinference-instrumentation-langchain` — auto-instruments LangChain/LangGraph calls

## Components

### `tracing.py` (project root)

A single `setup_tracing()` function that registers the OTEL tracer provider and instruments LangChain:

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

Notebooks import and call it explicitly:

```python
from tracing import setup_tracing
setup_tracing()
```

### `Justfile` (project root)

A `trace` recipe to start the Phoenix server before running notebooks:

```just
trace:
    uv run python -m phoenix.server.main serve
```

Usage: `just trace` — then open `http://localhost:6006` in a browser.

## Workflow

1. Run `just trace` to start the Phoenix server
2. Open a notebook and call `setup_tracing()` at the top
3. Run notebook cells — traces appear in Phoenix UI at `http://localhost:6006`
