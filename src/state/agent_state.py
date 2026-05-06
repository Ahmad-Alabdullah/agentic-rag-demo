from typing import Any, Dict, List, TypedDict
from langchain_core.documents import Document


class AgentState(TypedDict):
    query: str
    filters: Dict[str, Any]
    retrieved_docs: List[Document]
    answer: str
    sources: List[Dict]
    relevance: bool
    relevance_reason: str
    relevance_suggested_action: str
    iteration: int
