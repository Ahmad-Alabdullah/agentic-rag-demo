"""
Embedding und Indexing in Chroma.
Chunkt Redebeiträge und speichert mit Metadaten.
"""

from typing import List, Dict
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from config import get_settings
from retrieval.vector_store import get_embeddings

_s = get_settings()


def _split_long_paragraph(para: str) -> List[str]:
    """Hard-splittet einen Absatz > MAX_CHUNK_CHARS an Wortgrenzen."""
    if len(para) <= _s.max_chunk_chars:
        return [para]
    parts = []
    while len(para) > _s.max_chunk_chars:
        # rfind sucht die letzte Leerstelle *vor* dem Zeichenlimit — so wird an
        # Wortgrenzen geschnitten und kein Wort mitten durch getrennt
        split_at = para.rfind(" ", 0, _s.max_chunk_chars)
        # Wenn kein Leerzeichen existiert (z. B. ein einzelnes sehr langes Token),
        # wird hart am Zeichenlimit geschnitten
        if split_at == -1:
            split_at = _s.max_chunk_chars
        parts.append(para[:split_at].strip())
        para = para[split_at:].strip()
    if para:
        parts.append(para)
    return parts


def _split_speech(speech: Dict) -> List[Dict]:
    """
    Splittet lange Reden in Sub-Chunks mit Overlap.
    Kurze Reden bleiben als ein Chunk.
    """
    text = speech["text"]

    # Kurze Reden passen vollständig in einen Chunk — kein Splitting nötig
    if len(text) <= _s.max_chunk_chars:
        return [{**speech, "chunk_index": 0, "total_chunks": 1}]

    # Zweistufige Strategie: erst an natürlichen Absatzgrenzen ("\n\n") aufteilen,
    # dann überlange Einzelabsätze an Wortgrenzen weiter aufbrechen
    raw_paragraphs = text.split("\n\n")
    paragraphs = []
    for para in raw_paragraphs:
        paragraphs.extend(_split_long_paragraph(para))

    chunks = []
    current_text = ""
    chunk_index = 0

    for para in paragraphs:
        # Neuen Chunk beginnen, wenn das Hinzufügen des nächsten Absatzes das Limit
        # überschreiten würde und bereits Inhalt im aktuellen Chunk vorhanden ist
        if len(current_text) + len(para) > _s.max_chunk_chars and current_text:
            chunks.append(
                {
                    **{k: v for k, v in speech.items() if k != "text"},
                    "text": current_text.strip(),
                    "chunk_index": chunk_index,
                }
            )
            # Overlap: die letzten chunk_overlap_chars des abgeschlossenen Chunks
            # werden an den Anfang des nächsten kopiert, damit Kontext über
            # Chunk-Grenzen hinweg erhalten bleibt und Sätze nicht abrupt enden
            overlap = current_text[-_s.chunk_overlap_chars :].lstrip()
            current_text = f"{overlap}\n\n{para}" if overlap else para
            chunk_index += 1
        else:
            current_text = f"{current_text}\n\n{para}" if current_text else para

    if current_text.strip():
        chunks.append(
            {
                **{k: v for k, v in speech.items() if k != "text"},
                "text": current_text.strip(),
                "chunk_index": chunk_index,
            }
        )

    # total_chunks wird erst hier gesetzt, weil die Gesamtanzahl erst nach dem
    # vollständigen Durchlauf aller Absätze bekannt ist
    for chunk in chunks:
        chunk["total_chunks"] = len(chunks)

    return chunks


def _speech_to_document(chunk: Dict) -> Document:
    """
    Wandelt einen Chunk-Dict in ein LangChain Document um, das ChromaDB speichern kann.
    Alle Metadaten-Felder werden explizit übernommen; der Redetext wird als page_content gesetzt.
    """
    metadata = {
        "rede_id": chunk.get("rede_id", ""),
        "speaker_full": chunk.get("speaker_full", ""),
        "nachname": chunk.get("nachname", ""),
        "vorname": chunk.get("vorname", ""),
        "fraktion": chunk.get("fraktion", ""),
        "rolle": chunk.get("rolle", ""),
        "session_number": chunk.get("session_number", ""),
        "session_date": chunk.get("session_date", ""),
        "wahlperiode": chunk.get("wahlperiode", ""),
        "top_nr": chunk.get("top_nr", ""),
        # ChromaDB-Metadaten-Strings werden intern begrenzt; Titel auf 150 Zeichen
        # kürzen verhindert Fehler bei sehr langen Tagesordnungstiteln
        "top_titel": chunk.get("top_titel", "")[:150],
        "source_file": chunk.get("source_file", ""),
        "chunk_index": chunk.get("chunk_index", 0),
        "total_chunks": chunk.get("total_chunks", 1),
    }
    return Document(
        page_content=chunk["text"],
        metadata=metadata,
    )


def index_speeches(speeches: List[Dict]) -> Chroma:
    """Indexiert alle Redebeiträge in Chroma."""
    print(f"Starte Indexing von {len(speeches)} Redebeiträgen...")

    all_chunks = []
    for speech in speeches:
        all_chunks.extend(_split_speech(speech))
    print(f"Nach Chunking: {len(all_chunks)} Chunks")

    documents = [_speech_to_document(chunk) for chunk in all_chunks]

    print("Embedding und Indexing läuft...")

    # get_embeddings() liefert die zentral konfigurierte Ollama-Verbindung aus vector_store.py
    embeddings = get_embeddings()
    # Ollama verarbeitet Embeddings synchron; 50 Dokumente pro Batch vermeiden Timeouts
    # und ermöglichen Fortschrittsanzeige während des Indexings
    batch_size = 50

    # Der erste Batch erstellt die Chroma-Collection und schreibt sie atomisch auf Disk
    vector_store = Chroma.from_documents(
        documents=documents[:batch_size],
        embedding=embeddings,
        persist_directory=_s.chroma_dir,
        collection_name=_s.chroma_collection,
    )

    # Alle weiteren Batches werden inkrementell zur bestehenden Collection hinzugefügt
    for i in range(batch_size, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        vector_store.add_documents(batch)
        print(
            f"  {min(i + batch_size, len(documents))}/{len(documents)} Chunks indexiert"
        )

    print(f"Indexing abgeschlossen. {len(documents)} Chunks im Vector Store.")
    return vector_store
