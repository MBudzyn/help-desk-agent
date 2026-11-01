"""Graph state. The message list grows as tools return results."""

from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Conversation state passed between LangGraph nodes."""

    messages: Annotated[list[Any], add_messages]
