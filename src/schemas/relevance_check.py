from typing import Optional

from pydantic import BaseModel, Field


class RelevanceCheck(BaseModel):
    relevant: bool = Field(
        description="True wenn die generierte Antwort die Frage ausreichend beantwortet, andernfalls False"
    )
    reason: str = Field(description="Kurze Begründung in 1-2 Sätzen")
    suggested_action: Optional[str] = Field(
        None,
        description="Falls nicht ausreichend: 'revise' (Antwort überarbeiten) oder 'expand_retrieval' (zusätzliche Dokumente abrufen und Antwort neu generieren)",
    )
