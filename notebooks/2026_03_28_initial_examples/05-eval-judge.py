# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # LLM-as-Judge Evals with MLflow (new `mlflow.genai.evaluate` API)
#
# Uses the MLflow 3 `mlflow.genai.evaluate()` API with LLM judge scorers:
# 1. Define a dataset with `inputs` / `expectations` dicts
# 2. Define a `predict_fn` callable
# 3. Use built-in scorers (`Correctness`, `Guidelines`)
# 4. Define a custom LLM judge with `make_judge`
# 5. Define a code-based scorer with `@scorer`
# 6. View results in MLflow UI

# %%
import utils

# %%
import mlflow
import mlflow.genai
from mlflow.genai import make_judge, scorer
from mlflow.genai.scorers import Correctness, Guidelines
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# %% [markdown]
# ## 1. Define the dataset
#
# Each example is a dict with:
# - `inputs` — kwargs passed to `predict_fn`
# - `expectations` — ground truth used by scorers
# - `outputs` (optional) — pre-computed predictions (skips `predict_fn`)

# %%
dataset = [
    {
        "inputs": {"question": "What is the capital of France?"},
        "expectations": {"expected_response": "Paris"},
    },
    {
        "inputs": {"question": "What is 2 + 2?"},
        "expectations": {"expected_response": "4"},
    },
    {
        "inputs": {"question": "Who wrote Hamlet?"},
        "expectations": {"expected_response": "Shakespeare"},
    },
    {
        "inputs": {"question": "What color is the sky?"},
        "expectations": {"expected_response": "blue"},
    },
]

# %% [markdown]
# ## 2. Define the chain and predict_fn
#
# `predict_fn` receives the unpacked `inputs` dict as keyword arguments
# and must return a single string.

# %%
llm = ChatOpenAI(model="gpt-4o-mini")
prompt = PromptTemplate.from_template(
    "Answer the following question in one word or short phrase: {question}"
)
chain = prompt | llm


def predict_fn(question: str) -> str:
    print("invoking")
    response = chain.invoke({"question": question})
    print("invoked")
    return response.content

# %% [markdown]
# ## 4. Define a code-based scorer with `@scorer`
#
# For deterministic checks — no LLM call needed.

# %%
@scorer
def exact_match(outputs: str, expectations: dict) -> bool:
    return outputs.strip().lower() == expectations["expected_response"].strip().lower()

# %% [markdown]
# ## 5. Run evaluation
#
# Disable LangChain autolog before evaluating — autolog instruments every `chain.invoke()`
# and creates competing traces that conflict with `mlflow.genai.evaluate()`'s own tracing,
# causing evaluation traces to never close.

# %%
mlflow.langchain.autolog(disable=True)

results = mlflow.genai.evaluate(
    data=dataset,
    predict_fn=predict_fn,
    scorers=[
        exact_match,
    ],
)

# %% [markdown]
# ## 6. Inspect results

# %%
print("Aggregate metrics:")
print(results.metrics)

# %%
print("\nPer-row results:")
results.tables["eval_results_table"]
