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
# # ReAct Agent — Internal Implementation
#
# Builds a ReAct agent from scratch using LangGraph primitives to show
# exactly how `create_react_agent` works under the hood.
#
# Architecture:
# ```
# __start__ → agent → should_continue → tools → agent → ...
#                                     ↘ __end__
# ```

# %%
import utils

# %%
from typing import Annotated

from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# %% [markdown]
# ## State
#
# `add_messages` is a reducer that appends new messages rather than replacing the list.
# This gives the agent its full conversation history on every step.

# %%
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# %% [markdown]
# ## Tools

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


tools = [add, multiply, get_weather]
tools_by_name = {t.name: t for t in tools}

# %% [markdown]
# ## LLM with tools bound
#
# `.bind_tools()` attaches the tool schemas to every LLM call so the model
# can emit structured `tool_calls` in its response.

# %%
llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools)

# %% [markdown]
# ## Node 1: agent
#
# Calls the LLM with the full message history. Returns an `AIMessage`
# that may contain `tool_calls` if the model wants to use a tool.

# %%
def agent_node(state: AgentState) -> AgentState:
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# %% [markdown]
# ## Node 2: tools
#
# Reads `tool_calls` from the last `AIMessage`, executes each tool,
# and wraps the result in a `ToolMessage` so the LLM can see the output.

# %%
def tools_node(state: AgentState) -> AgentState:
    last_message = state["messages"][-1]
    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool_fn = tools_by_name[tool_call["name"]]
        result = tool_fn.invoke(tool_call["args"])
        tool_messages.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"],
            )
        )
    return {"messages": tool_messages}


# %% [markdown]
# ## Conditional edge: should_continue
#
# Routes to `tools` if the LLM emitted tool calls, otherwise ends.

# %%
def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return "__end__"


# %% [markdown]
# ## Build the graph

# %%
graph_builder = StateGraph(AgentState)

graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", tools_node)

graph_builder.add_edge(START, "agent")
graph_builder.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", "__end__": END},
)
graph_builder.add_edge("tools", "agent")  # always loop back after tool execution

agent = graph_builder.compile()

# %% [markdown]
# ## Visualise the graph structure

# %%
try:
    from IPython.display import Image, display
    display(Image(agent.get_graph().draw_mermaid_png()))
except Exception:
    print(agent.get_graph().draw_mermaid())

# %% [markdown]
# ## Run the agent

# %%
result = agent.invoke({
    "messages": [
        {"role": "user", "content": "What is (3 + 5) * 12? Also, what's the weather in Paris?"}
    ]
})

for message in result["messages"]:
    print(f"[{message.type}] {message.content}")

# %% [markdown]
# ## Stream step-by-step
#
# `stream()` yields the state delta after each node executes, making the
# think → act → observe loop visible.

# %%
for step in agent.stream(
    {"messages": [{"role": "user", "content": "Add 7 and 9, then multiply the result by 3."}]},
    stream_mode="updates",
):
    node_name, state_delta = next(iter(step.items()))
    last_msg = state_delta["messages"][-1]
    print(f"[{node_name}] {last_msg.type}: {last_msg.content or last_msg.tool_calls}")

# %%
