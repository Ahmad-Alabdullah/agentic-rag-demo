RELEVANCE_CHECK_PROMPT = """Prüfe die Relevanz der folgenden Antwort auf die Frage mit Einbezug der bereitgestellten Informationen:
                        Frage: {query}
                        ursprüngliche Antwort: {answer}
                        Contextinformationen: {retrieved_docs}
                        
                        Bewerte:
                        - relevance: Ist die Antwort relevant genug, um die Frage zu beantworten? (True/False)
                        - reason: Begründung und Anleitung zur Korrektur der Antwort, falls sie nicht relevant ist.
                        - relevance_suggested_action:
                            - 'revise' (Antwort überarbeiten)
                            - 'expand_retrieval' (zusätzliche Dokumente abrufen und Antwort neu generieren)"""
