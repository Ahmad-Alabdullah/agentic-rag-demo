import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from preprocessing.parser import parse_all_protocols
from preprocessing.indexer import index_speeches

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
