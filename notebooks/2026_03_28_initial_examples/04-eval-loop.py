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
# # Eval Loop with MLflow
#
# A full evaluation loop using LangChain + MLflow:
# 1. Define a dataset as a list of input/expected output pairs
# 2. Register it with MLflow
# 3. Run a LangChain chain over each example
# 4. Score the outputs with an evaluator
# 5. Log metrics and results to MLflow

# %%
import utils

# %%
import mlflow
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# %% [markdown]
# ## 1. Define the dataset

# %%
examples = [
    {"input": "What is the capital of France?", "expected": "Paris"},
    {"input": "What is 2 + 2?", "expected": "4"},
    {"input": "Who wrote Hamlet?", "expected": "Shakespeare"},
    {"input": "What color is the sky?", "expected": "blue"},
]

dataset_df = pd.DataFrame(examples)

mlflow_dataset = mlflow.data.from_pandas(
    dataset_df,
    name="qa-eval-dataset",
    targets="expected",
)

# %% [markdown]
# ## 2. Define the chain

# %%
llm = ChatOpenAI(model="gpt-4o-mini")
prompt = PromptTemplate.from_template(
    "Answer the following question in one word or short phrase: {input}"
)
chain = prompt | llm

# %% [markdown]
# ## 3. Define an evaluator
#
# Simple exact-match after lowercasing and stripping whitespace.

# %%
def exact_match(prediction: str, expected: str) -> float:
    return float(prediction.strip().lower() == expected.strip().lower())


# %% [markdown]
# ## 4. Run the eval loop

# %%
with mlflow.start_run(run_name="qa-eval"):
    mlflow.log_input(mlflow_dataset, context="eval")

    results = []
    for example in examples:
        response = chain.invoke({"input": example["input"]})
        prediction = response.content

        score = exact_match(prediction, example["expected"])
        results.append({
            "input": example["input"],
            "expected": example["expected"],
            "prediction": prediction,
            "exact_match": score,
        })

    results_df = pd.DataFrame(results)

    # Log aggregate metrics
    mlflow.log_metric("exact_match_mean", results_df["exact_match"].mean())
    mlflow.log_metric("num_examples", len(results_df))

    print(results_df.to_string(index=False))
    print(f"\nExact match: {results_df['exact_match'].mean():.0%}")
