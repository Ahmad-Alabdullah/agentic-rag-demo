from llm.providers import get_llm
from prompts.synthesize_prompt import SYNTHESIZE_PROMPT
from state.agent_state import AgentState


def synthesize(state: AgentState) -> AgentState:
    """Node 3: Generiert Antwort aus den gefundenen Chunks."""
    # Wenn der retrieve-Node keine Dokumente gefunden hat, direkt mit einer
    # erklärenden Meldung abbrechen — kein LLM-Aufruf nötig
    if not state["retrieved_docs"]:
        return {
            **state,
            "answer": "Ich konnte leider keine passenden Informationen in den Protokollen finden. Bitte prüfe, ob die gesuchte Person, Fraktion oder Sitzung in den indizierten Dokumenten enthalten ist.",
            "sources": [],
        }

    # Jeden Chunk mit einem nummerierten Header versehen, damit das LLM die Quellen
    # im Antworttext als [1], [2] usw. zitieren kann
    context_parts = []
    for i, doc in enumerate(state["retrieved_docs"]):
        meta = doc.metadata
        speaker = meta.get("speaker_full", "Unbekannt")
        session = meta.get("session_number", "?")
        date = meta.get("session_date", "")
        fraktion = meta.get("fraktion", "")

        # Header-Zeile: "[1] Vorname Nachname (Fraktion), Sitzung 42 vom 01.01.2022"
        header = f"[{i+1}] {speaker}"
        if fraktion:
            header += f" ({fraktion})"
        header += f", Sitzung {session}"
        if date:
            header += f" vom {date}"

        context_parts.append(f"{header}:\n{doc.page_content}")

    # Einzelne Quellen durch einen horizontalen Trenner voneinander abgrenzen,
    # damit das LLM die Grenzen zwischen Redebeiträgen klar erkennt
    context = "\n\n---\n\n".join(context_parts)

    # Synthesis-LLM aufrufen (temperature 0.1 für konsistente, faktentreue Antworten)
    llm = get_llm()
    response = llm.invoke(SYNTHESIZE_PROMPT.format(query=state["query"], context=context))
    answer = response.content

    # Quellen-Liste für die UI aufbauen — getrennt von der Antwort, damit die UI
    # sie strukturiert darstellen kann (z. B. als aufklappbare Blöcke)
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
                # Vorschau auf 300 Zeichen begrenzen, damit die UI nicht überflutet wird
                "text_preview": (
                    doc.page_content[:300] + "..."
                    if len(doc.page_content) > 300
                    else doc.page_content
                ),
            }
        )

    return {**state, "answer": answer, "sources": sources}
