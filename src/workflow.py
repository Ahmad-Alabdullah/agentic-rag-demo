from typing import Dict
from langgraph.graph import StateGraph, END

from nodes.extract_filters import extract_filters
from nodes.retrieve import retrieve
from nodes.synthesize import synthesize
from nodes.relevance_check import relevance_check
from nodes.revise import revise
from state.agent_state import AgentState


def _route_after_relevance(state: AgentState) -> str:
    if state["relevance"]:
        return END
    action = state.get("relevance_suggested_action") or "revise"
    return "retrieve" if action == "expand_retrieval" else "revise"


def build_agent():
    workflow = StateGraph(AgentState)

    workflow.add_node("extract_filters", extract_filters)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("synthesize", synthesize)
    workflow.add_node("relevance_check", relevance_check)
    workflow.add_node("revise", revise)

    workflow.set_entry_point("extract_filters")
    workflow.add_edge("extract_filters", "retrieve")
    workflow.add_edge("retrieve", "synthesize")
    workflow.add_edge("synthesize", "relevance_check")
    workflow.add_conditional_edges("relevance_check", _route_after_relevance)
    workflow.add_edge("revise", "relevance_check")

    return workflow.compile()


def run_query(query: str) -> Dict:
    agent = build_agent()

    initial_state = AgentState(
        query=query,
        filters={},
        retrieved_docs=[],
        answer="",
        sources=[],
        relevance=False,
        relevance_reason="",
        relevance_suggested_action="",
        iteration=0,
    )

    result = agent.invoke(initial_state)
    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "filters": result["filters"],
    }
