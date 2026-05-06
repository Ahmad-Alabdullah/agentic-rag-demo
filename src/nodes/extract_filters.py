from llm.providers import get_llm_for_extraction
from prompts.extraction_prompt import EXTRACTION_PROMPT
from schemas.query_filters import QueryFilters
from state.agent_state import AgentState


def extract_filters(state: AgentState) -> AgentState:
    """
    Node 1: Extrahiert strukturierte Filter aus der User-Query.
    Beispiel: "Was hat Thews in TOP 6 gesagt?"
    → {speaker_lastname: "Thews", top_nr: "6"}
    """
    llm = get_llm_for_extraction()
    structured_llm = llm.with_structured_output(QueryFilters)

    try:
        filters = structured_llm.invoke(EXTRACTION_PROMPT.format(query=state["query"]))
        filters_dict = filters.model_dump(exclude_none=True)
    except Exception as e:
        print(f"Filter-Extraktion fehlgeschlagen: {e}")
        filters_dict = {}

    print(f"Extrahierte Filter: {filters_dict}")
    return {**state, "filters": filters_dict}
