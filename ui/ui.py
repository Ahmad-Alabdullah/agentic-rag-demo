"""
Gradio Chat-Interface für den Bundestags-RAG-Chatbot.
"""

import gradio as gr
from workflow import run_query


def _format_sources(sources: list) -> str:
    """Formatiert die Quellen als lesbare Markdown-Tabelle."""
    if not sources:
        return ""

    lines = ["\n\n---\n### 📎 Verwendete Quellen\n"]
    for src in sources:
        speaker = src["speaker"]
        # Optionale Felder nur einbauen wenn vorhanden, sonst leerer String
        fraktion = f" ({src['fraktion']})" if src["fraktion"] else ""
        session = src["session"]
        date = f", {src['date']}" if src["date"] else ""
        top = f"\n   *{src['top']}*" if src["top"] else ""
        preview = src["text_preview"]

        # Jede Quelle als Markdown-Block: fette Überschrift + Blockzitat für den Textausschnitt
        lines.append(
            f"**[{src['nr']}] {speaker}{fraktion}**  "
            f"Sitzung {session}{date}{top}\n"
            f"> {preview}\n"
        )

    return "\n".join(lines)


def _format_filters(filters: dict) -> str:
    """Zeigt erkannte Filter als Info-Box."""
    if not filters:
        return ""

    parts = []
    if filters.get("speaker_lastname"):
        # Vor- und Nachname zusammensetzen; Vorname kann leer sein
        name = filters.get("speaker_firstname", "")
        name += f" {filters['speaker_lastname']}"
        parts.append(f"👤 Sprecher: {name.strip()}")
    if filters.get("fraktion"):
        parts.append(f"🏛️ Fraktion: {filters['fraktion']}")
    if filters.get("session_number"):
        parts.append(f"📋 Sitzung: {filters['session_number']}")

    if not parts:
        return ""

    # Als eingerücktes Blockzitat dargestellt, damit es sich optisch von der Antwort abhebt
    return "\n> 🔍 Erkannte Filter: " + " | ".join(parts) + "\n"


def chat(message: str, history: list):
    """
    Hauptfunktion für den Gradio-Chat.
    Verwendet das Gradio-6-Nachrichtenformat: Liste von {role, content}-Dicts.
    """
    # Leere Eingaben sofort ignorieren, ohne den LangGraph-Workflow zu starten
    if not message.strip():
        yield history, ""
        return

    # Sofort einen Lade-Zustand in den Chat einfügen und yielden, damit der Nutzer
    # sieht, dass die Anfrage verarbeitet wird (Streaming-Pattern ohne echtes Streaming)
    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": "⏳ Suche in den Protokollen..."},
    ]
    yield history, ""

    try:
        # Blockierender LangGraph-Aufruf (extract_filters → retrieve → synthesize)
        result = run_query(message)

        # Antwort aus drei optionalen Teilen zusammensetzen:
        # 1. Filter-Info-Box (wenn Filter erkannt wurden)
        # 2. Eigentliche LLM-Antwort
        # 3. Quellen-Block
        filters_info = _format_filters(result["filters"])
        sources_text = _format_sources(result["sources"])

        full_response = ""
        if filters_info:
            full_response += filters_info + "\n"
        full_response += result["answer"]
        if sources_text:
            full_response += sources_text

        # Den vorläufigen Lade-Text im letzten History-Eintrag durch die echte Antwort ersetzen
        history[-1]["content"] = full_response

    except Exception as e:
        history[-1]["content"] = f"❌ Fehler: {str(e)}"

    yield history, ""


def create_ui():
    """Erstellt das Gradio-Interface."""

    example_questions = [
        "Was hat Michael Thews zur Energiesteuer gesagt?",
        "Welche Argumente brachte die AfD gegen das 9-Euro-Ticket?",
        "Was wurde in Tagesordnungspunkt 4 zum Gasnetz diskutiert?",
        "Was hat die SPD zur Erwerbsminderungsrente gefordert?",
        "Welche Positionen hat Die Linke zur Energiepolitik vertreten?",
    ]

    with gr.Blocks(
        title="Bundestag RAG",
    ) as demo:

        gr.Markdown("""
        # 🏛️ Bundestags-Chatbot
        Stelle Fragen zu Plenarprotokollen des Deutschen Bundestags.

        **Tipp:** Du kannst nach bestimmten Sprechern, Sitzungen oder Themen fragen.
        """)

        # Zweispaltiges Layout: breiter Chat-Bereich (scale=3) + schmale Info-Sidebar (scale=1)
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    value=[],
                    elem_classes=["chatbot-container"],
                    show_label=False,
                    render_markdown=True,  # Markdown in Antworten aktivieren
                )

                # Eingabezeile: Textfeld nimmt den Großteil der Breite ein (scale=5),
                # Senden-Button ist kompakter (scale=1)
                with gr.Row():
                    msg_input = gr.Textbox(
                        placeholder="Stelle eine Frage zu den Protokollen...",
                        show_label=False,
                        scale=5,
                        container=False,
                    )
                    submit_btn = gr.Button(
                        "Senden",
                        variant="primary",
                        scale=1,
                    )

                # Beispiel-Fragen befüllen das Textfeld per Klick — kein automatisches Absenden
                gr.Examples(
                    examples=example_questions,
                    inputs=msg_input,
                    label="Beispiel-Fragen",
                )

            with gr.Column(scale=1):
                gr.Markdown("### ℹ️ Informationen")
                gr.Markdown("""
                **Modell:** Mistral Small 4
                **Embeddings:** bge-m3 (lokal)
                **Vector Store:** Chroma
                **Framework:** LangGraph

                **Unterstützte Filter:**
                - 👤 Sprecher (Name)
                - 🏛️ Fraktion (SPD, CDU/CSU, ...)
                - 📋 Sitzungsnummer
                """)

                clear_btn = gr.Button("🗑️ Chat leeren", variant="secondary")

        # Event Handler: Button-Klick und Enter-Taste lösen denselben chat()-Generator aus.
        # outputs=[chatbot, msg_input] leert das Textfeld nach dem Absenden (chat() yieldet "").
        submit_btn.click(
            fn=chat,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input],
        )
        msg_input.submit(
            fn=chat,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input],
        )
        # Chat leeren setzt History auf [] und Textfeld auf "" zurück
        clear_btn.click(
            fn=lambda: ([], ""),
            outputs=[chatbot, msg_input],
        )

    return demo
