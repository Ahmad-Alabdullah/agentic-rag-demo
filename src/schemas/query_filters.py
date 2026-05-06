from typing import Optional

from pydantic import BaseModel, Field


class QueryFilters(BaseModel):
    speaker_lastname: Optional[str] = Field(
        None, description="Nachname des gesuchten Redners (z.B. 'Thews')"
    )
    speaker_firstname: Optional[str] = Field(
        None, description="Vorname des gesuchten Redners (z.B. 'Michael')"
    )
    fraktion: Optional[str] = Field(
        None, description="Fraktion: SPD, CDU/CSU, AfD, GRÜNE, Linke, fraktionslos"
    )
    session_number: Optional[str] = Field(
        None, description="Sitzungsnummer als String (z.B. '75')"
    )
    top_nr: Optional[str] = Field(
        None,
        description="Tagesordnungspunkt-Nummer als String (z.B. '6' für TOP 6 oder Tagesordnungspunkt 6)",
    )
