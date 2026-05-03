import chromadb

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "bundestag"


def main():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    col = client.get_collection(COLLECTION_NAME)

    print(f"=== ChromaDB Inspektion: '{COLLECTION_NAME}' ===")
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
