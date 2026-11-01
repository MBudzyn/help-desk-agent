"""One tool-calling loop: the model chooses a tool, the code runs it, and the result comes back."""

import os
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agent.prompts import SYSTEM_PROMPT
from agent.state import AgentState
from agent.tools import SHOP_TOOLS
from config import CURRENT_TIME

MAX_TOOL_ROUNDS = 4
STAFF_FALLBACK = (
    "I could not finish this from the shop's records. "
    "Please contact the staff at help@citywheels.example or +48 000 000 000."
)


def build_graph(model: Any) -> Any:
    """Compile the LangGraph agent with the three CityWheels tools."""
    bound_model = model.bind_tools(SHOP_TOOLS)

    def call_model(state: AgentState) -> dict[str, list[Any]]:
        tool_rounds = sum(isinstance(message, ToolMessage) for message in state["messages"])
        if tool_rounds >= MAX_TOOL_ROUNDS:
            return {"messages": [AIMessage(content=STAFF_FALLBACK)]}
        response = bound_model.invoke([SystemMessage(content=SYSTEM_PROMPT), *state["messages"]])
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(SHOP_TOOLS))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    return graph.compile()


def answer(question: str, model: Any | None = None) -> str:
    """Run one question through the agent and return its final text."""
    graph = build_graph(model if model is not None else _real_model())
    state = graph.invoke({"messages": [_customer_message(question)]})
    return _message_text(state["messages"][-1])


def _real_model() -> Any:
    key = os.environ.get("GOOGLE_API_KEY", "")
    name = os.environ.get("MODEL_NAME", "")
    if key == "" or name == "":
        raise RuntimeError("GOOGLE_API_KEY and MODEL_NAME must be set")
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(model=name, google_api_key=key)


def _customer_message(question: str) -> HumanMessage:
    stamp = CURRENT_TIME.strftime("%Y-%m-%d %H:%M")
    return HumanMessage(content=f"Current time: {stamp} Europe/Warsaw\n\n{question.strip()}")


def _message_text(message: Any) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    return str(content)
