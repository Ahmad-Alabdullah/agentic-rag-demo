EXTRACTION_PROMPT = """Analysiere die folgende Bundestags-Recherche-Frage und extrahiere strukturierte Filter.
Extrahiere nur Filter, die explizit in der Frage genannt werden. Lasse nicht genannte Felder null.

Frage: {query}

Hinweise:
- top_nr: Nur die Zahl extrahieren. "TOP 6", "Tagesordnungspunkt 6" und "Punkt 6" → "6"
- fraktion: Originalbezeichnung übernehmen (SPD, CDU/CSU, AfD, GRÜNE, Linke)
- speaker_lastname und speaker_firstname: Nur wenn ein konkreter Name genannt wird

Antwort:"""
