from llm.providers import get_llm
from prompts.revision_prompt import REVISION_PROMPT
from state.agent_state import AgentState


def revise(state: AgentState) -> dict:
    llm = get_llm()

    context = "\n\n".join(
        f"[{i+1}] {doc.page_content}" for i, doc in enumerate(state["retrieved_docs"])
    )

    prompt = REVISION_PROMPT.format(
        query=state["query"],
        answer=state["answer"],
        relevance_reason=state["relevance_reason"],
        iteration=state.get("iteration", 1),
        context=context,
    )

    try:
        result = llm.invoke(prompt)
        return {"answer": result.content}
    except Exception as e:
        print(f"Fehler beim Überarbeiten der Antwort: {e}")
        return {}
