import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

from rag_app.config import get_settings
from rag_app.ingestion import ingest_folder


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a folder into Qdrant Cloud with LlamaIndex.")
    parser.add_argument("--folder", required=True, help="Path to a Windows folder containing PDF, MD, TXT, or JSON files.")
    args = parser.parse_args()

    result = ingest_folder(args.folder, get_settings())
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
