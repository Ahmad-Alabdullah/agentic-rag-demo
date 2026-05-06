"""
App starten: python app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import gradio as gr
from dotenv import load_dotenv
from ui.ui import create_ui

load_dotenv()


if __name__ == "__main__":
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        theme=gr.themes.Soft(),
        css=".chatbot-container { height: 600px; } .source-box { font-size: 0.85em; }",
    )
