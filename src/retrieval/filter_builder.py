import re
from typing import Dict, Optional

_FRAKTION_EXACT = {
    "spd": "SPD",
    "cdu": "CDU/CSU",
    "csu": "CDU/CSU",
    "cdu/csu": "CDU/CSU",
    "union": "CDU/CSU",
    "afd": "AfD",
    "grüne": "BÜNDNIS 90/DIE GRÜNEN",
    "grünen": "BÜNDNIS 90/DIE GRÜNEN",
    "bündnis": "BÜNDNIS 90/DIE GRÜNEN",
    "die grünen": "BÜNDNIS 90/DIE GRÜNEN",
    "linke": "Die Linke",
    "die linke": "Die Linke",
    "linken": "Die Linke",
    "fraktionslos": "fraktionslos",
}


def _normalize_fraktion(raw: str) -> str:
    return _FRAKTION_EXACT.get(raw.lower().strip(), raw)


def _normalize_top_nr(raw: str) -> str:
    """Normalisiert 'TOP 6', '6', 'ZP 15' auf den exakten gespeicherten Wert."""
    num_match = re.search(r"\d+", raw)
    if not num_match:
        return raw
    num = num_match.group()
    if re.search(r"zusatz|zp\b", raw, re.IGNORECASE):
        return f"Zusatzpunkt {num}"
    return f"Tagesordnungspunkt {num}"


def build_chroma_filter(filters: Dict) -> Optional[Dict]:
    """Baut einen Chroma-kompatiblen Filter aus Pydantic-Filterwerten."""
    if not filters:
        return None

    conditions = []

    if filters.get("speaker_lastname"):
        conditions.append({"nachname": {"$eq": filters["speaker_lastname"]}})
    if filters.get("speaker_firstname"):
        conditions.append({"vorname": {"$eq": filters["speaker_firstname"]}})
    if filters.get("fraktion"):
        conditions.append(
            {"fraktion": {"$eq": _normalize_fraktion(filters["fraktion"])}}
        )
    if filters.get("session_number"):
        conditions.append({"session_number": {"$eq": filters["session_number"]}})
    if filters.get("top_nr"):
        conditions.append({"top_nr": {"$eq": _normalize_top_nr(filters["top_nr"])}})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}
