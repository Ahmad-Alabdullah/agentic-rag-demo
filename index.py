from dotenv import load_dotenv
from src.parser import parse_all_protocols
from src.indexer import index_speeches
from pathlib import Path

load_dotenv()


def main():
    data_dir = "./data"

    if not Path(data_dir).exists():
        print(f"Verzeichnis '{data_dir}' existiert nicht.")
        print("Bitte XML-Dateien in ./data ablegen.")
        return

    print("=== Bundestag RAG: Indexing ===\n")

    # Parsen
    print("1. Parsing XML-Protokolle...")
    speeches = parse_all_protocols(data_dir)

    if not speeches:
        print("Keine Redebeiträge gefunden. Abbruch.")
        return

    # Indexieren
    print(f"\n2. Indexing {len(speeches)} Redebeiträge...")
    index_speeches(speeches)

    print("\n=== Indexing abgeschlossen ===")


if __name__ == "__main__":
    main()
