import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import chromadb
from config import get_settings

_s = get_settings()


def main():
    client = chromadb.PersistentClient(path=_s.chroma_dir)
    col = client.get_collection(_s.chroma_collection)

    print(f"=== ChromaDB Inspektion: '{_s.chroma_collection}' ===")
    print(f"Gesamt Chunks: {col.count()}\n")

    result = col.get(limit=1, include=["metadatas"])
    print("=== Metadaten-Felder ===")
    for field in result["metadatas"][0].keys():
        print(f"  - {field}")
    print()

    result = col.get(limit=5, include=["documents", "metadatas"])
    print("=== Erste 5 Chunks ===")
    for i, (doc, meta) in enumerate(zip(result["documents"], result["metadatas"])):
        print(f"--- Chunk {i + 1} ---")
        for field, value in meta.items():
            print(f"  {field}: {value}")
        print(f"  text: {doc}")
        print()


if __name__ == "__main__":
    main()
