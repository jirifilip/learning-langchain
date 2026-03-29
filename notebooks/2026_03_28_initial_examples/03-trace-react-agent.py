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
# # Tracing a ReAct Agent
#
# Demonstrates a LangGraph ReAct agent with MLflow tracing.
# The agent uses tools to answer questions step-by-step.

# %%
import utils

# %%
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# %% [markdown]
# ## Define Tools

# %%
@tool
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    weather_data = {
        "london": "Cloudy, 12°C",
        "paris": "Sunny, 18°C",
        "new york": "Rainy, 9°C",
        "tokyo": "Clear, 22°C",
    }
    return weather_data.get(city.lower(), f"Weather data not available for {city}")


# %% [markdown]
# ## Create and Run the ReAct Agent

# %%
llm = ChatOpenAI(model="gpt-4o-mini")
tools = [add, multiply, get_weather]

agent = create_react_agent(llm, tools)

# %%
result = agent.invoke({
    "messages": [
        {"role": "user", "content": "What is (3 + 5) * 12? Also, what's the weather in Paris?"}
    ]
})

for message in result["messages"]:
    print(f"[{message.type}] {message.content}")

# %%
