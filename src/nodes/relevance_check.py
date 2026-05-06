from llm.providers import get_llm_for_extraction
from prompts.relevance_check_prompt import RELEVANCE_CHECK_PROMPT
from schemas.relevance_check import RelevanceCheck
from state.agent_state import AgentState


def relevance_check(state: AgentState) -> dict:
    iteration = state.get("iteration", 0) + 1

    if iteration >= 2:
        return {
            "relevance": True,
            "relevance_reason": "Maximale Iterationen erreicht",
            "iteration": iteration,
        }

    docs = state["retrieved_docs"]
    context_preview = "\n\n".join(
        f"[{i+1}] {doc.page_content}..." for i, doc in enumerate(docs)
    )

    llm = get_llm_for_extraction()
    structured_llm = llm.with_structured_output(RelevanceCheck)

    try:
        relevance_result = structured_llm.invoke(
            RELEVANCE_CHECK_PROMPT.format(
                query=state["query"],
                answer=state["answer"],
                retrieved_docs=context_preview,
            )
        )

        return {
            "relevance": relevance_result.relevant,
            "relevance_reason": relevance_result.reason,
            "relevance_suggested_action": relevance_result.suggested_action,
            "iteration": iteration,
        }
    except Exception as e:
        print(f"Relevanzprüfung fehlgeschlagen: {e}")
        return {
            "relevance": True,
            "relevance_reason": f"Relevanzprüfung fehlgeschlagen, durchlassen: {e}",
            "iteration": iteration,
        }
