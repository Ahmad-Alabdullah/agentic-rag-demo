from config import get_settings
from retrieval.filter_builder import build_chroma_filter
from retrieval.vector_store import get_vector_store
from state.agent_state import AgentState

_s = get_settings()


def retrieve(state: AgentState) -> AgentState:
    """
    Node 2: Semantische Suche mit Metadaten-Filtern.
    Filter werden als harte Einschränkung angewendet.
    """
    vector_store = get_vector_store()
    chroma_filter = build_chroma_filter(state["filters"])

    # Bei Iteration > 0 und Routing entscheidet sich für "retreive"
    # dann erweitern wir die Anzahl der zurückgegebenen Dokumente, um mehr Kontext für die Überarbeitung zu bieten.
    k = _s.retrieval_k_expanded if state.get("iteration", 0) > 0 else _s.retrieval_k

    try:
        if chroma_filter:
            docs = vector_store.similarity_search(
                state["query"],
                k=k,
                filter=chroma_filter,
            )
        else:
            docs = vector_store.similarity_search(
                state["query"],
                k=k,
            )
    except Exception as e:
        print(f"Retrieval-Fehler: {e}")
        docs = []

    print(f"Gefundene Chunks: {len(docs)}")
    return {**state, "retrieved_docs": docs}
