REVISION_PROMPT = """Die ursprüngliche Antwort war nicht relevant genug, um die Frage zu beantworten.
Dies ist Überarbeitungsversuch {iteration}.

Frage: {query}

Verfügbare Quellen:
{context}

Ursprüngliche Antwort: {answer}
Relevanzbegründung: {relevance_reason}

Überarbeite die Antwort, indem du die verfügbaren Quellen gezielt nutzt, um die genannte Schwäche zu beheben."""
