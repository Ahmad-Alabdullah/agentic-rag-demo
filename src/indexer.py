"""
Embedding und Indexing in Chroma.
Chunkt Redebeiträge und speichert mit Metadaten.
"""

from typing import List, Dict
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

EMBED_MODEL = "bge-m3:latest"
OLLAMA_BASE = "http://localhost:11434"
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "bundestag"
MAX_CHUNK_CHARS = 1500
CHUNK_OVERLAP_CHARS = 150


def get_embeddings():
    return OllamaEmbeddings(
        model=EMBED_MODEL,
        base_url=OLLAMA_BASE,
    )


def get_vector_store():
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=CHROMA_DIR,
    )


def _split_long_paragraph(para: str) -> List[str]:
    """Hard-splittet einen Absatz > MAX_CHUNK_CHARS an Wortgrenzen."""
    if len(para) <= MAX_CHUNK_CHARS:
        return [para]
    parts = []
    while len(para) > MAX_CHUNK_CHARS:
        split_at = para.rfind(" ", 0, MAX_CHUNK_CHARS)
        if split_at == -1:
            split_at = MAX_CHUNK_CHARS
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

    if len(text) <= MAX_CHUNK_CHARS:
        return [{**speech, "chunk_index": 0, "total_chunks": 1}]

    # Absätze expandieren — überlange Absätze werden hart gesplittet
    raw_paragraphs = text.split("\n\n")
    paragraphs = []
    for para in raw_paragraphs:
        paragraphs.extend(_split_long_paragraph(para))

    chunks = []
    current_text = ""
    chunk_index = 0

    for para in paragraphs:
        if len(current_text) + len(para) > MAX_CHUNK_CHARS and current_text:
            chunks.append({
                **{k: v for k, v in speech.items() if k != "text"},
                "text": current_text.strip(),
                "chunk_index": chunk_index,
            })
            # Overlap: letzte CHUNK_OVERLAP_CHARS des vorherigen Chunks übernehmen
            overlap = current_text[-CHUNK_OVERLAP_CHARS:].lstrip()
            current_text = f"{overlap}\n\n{para}" if overlap else para
            chunk_index += 1
        else:
            current_text = f"{current_text}\n\n{para}" if current_text else para

    if current_text.strip():
        chunks.append({
            **{k: v for k, v in speech.items() if k != "text"},
            "text": current_text.strip(),
            "chunk_index": chunk_index,
        })

    for chunk in chunks:
        chunk["total_chunks"] = len(chunks)

    return chunks


def _speech_to_document(chunk: Dict) -> Document:
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

    embeddings = get_embeddings()
    batch_size = 50

    vector_store = Chroma.from_documents(
        documents=documents[:batch_size],
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME,
    )

    for i in range(batch_size, len(documents), batch_size):
        batch = documents[i: i + batch_size]
        vector_store.add_documents(batch)
        print(f"  {min(i + batch_size, len(documents))}/{len(documents)} Chunks indexiert")

    print(f"Indexing abgeschlossen. {len(documents)} Chunks im Vector Store.")
    return vector_store
