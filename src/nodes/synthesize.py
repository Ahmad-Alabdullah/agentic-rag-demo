from llm.providers import get_llm
from prompts.synthesize_prompt import SYNTHESIZE_PROMPT
from state.agent_state import AgentState


def synthesize(state: AgentState) -> AgentState:
    """Node 3: Generiert Antwort aus den gefundenen Chunks."""
    if not state["retrieved_docs"]:
        return {
            **state,
            "answer": "Ich konnte leider keine passenden Informationen in den Protokollen finden. Bitte prüfe, ob die gesuchte Person, Fraktion oder Sitzung in den indizierten Dokumenten enthalten ist.",
            "sources": [],
        }

    context_parts = []
    for i, doc in enumerate(state["retrieved_docs"]):
        meta = doc.metadata
        speaker = meta.get("speaker_full", "Unbekannt")
        session = meta.get("session_number", "?")
        date = meta.get("session_date", "")
        fraktion = meta.get("fraktion", "")

        header = f"[{i+1}] {speaker}"
        if fraktion:
            header += f" ({fraktion})"
        header += f", Sitzung {session}"
        if date:
            header += f" vom {date}"

        context_parts.append(f"{header}:\n{doc.page_content}")

    context = "\n\n---\n\n".join(context_parts)

    llm = get_llm()
    response = llm.invoke(SYNTHESIZE_PROMPT.format(query=state["query"], context=context))
    answer = response.content

    sources = []
    for i, doc in enumerate(state["retrieved_docs"]):
        meta = doc.metadata
        sources.append(
            {
                "nr": i + 1,
                "speaker": meta.get("speaker_full", "Unbekannt"),
                "fraktion": meta.get("fraktion", ""),
                "session": meta.get("session_number", ""),
                "date": meta.get("session_date", ""),
                "top": meta.get("top_titel", ""),
                "text_preview": (
                    doc.page_content[:300] + "..."
                    if len(doc.page_content) > 300
                    else doc.page_content
                ),
            }
        )

    return {**state, "answer": answer, "sources": sources}
