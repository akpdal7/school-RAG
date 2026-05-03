import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

from rag_app.config import get_settings


def print_env_status() -> None:
    env_path = Path.cwd() / ".env"
    settings = get_settings()
    checks = {
        "MESH_API_KEY": bool(settings.mesh_api_key or settings.openai_api_key),
        "QDRANT_URL": bool(settings.qdrant_url),
        "QDRANT_API_KEY": bool(settings.qdrant_api_key),
        "QDRANT_COLLECTION": bool(settings.qdrant_collection),
    }
    print(f"working_directory: {Path.cwd()}")
    print(f"env_path_checked: {env_path}")
    print(f"env_file_exists: {env_path.exists()}")
    print(f"MESH_API_BASE_URL: {settings.llm_api_base_url}")
    for name, is_set in checks.items():
        print(f"{name}: {'set' if is_set else 'missing'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Gmail messages from a sender as JSON and ingest them into Qdrant.")
    parser.add_argument("--sender", help="Teacher or sender email address to search with Gmail from:sender.")
    parser.add_argument("--output-folder", default="data/gmail_json", help="Folder where exported email JSON files are saved.")
    parser.add_argument("--credentials-file", default="data/secrets/gmail_credentials.json", help="Google OAuth client JSON file.")
    parser.add_argument("--token-file", default="data/secrets/gmail_token.json", help="OAuth token cache file.")
    parser.add_argument("--max-results", type=int, default=25, help="Maximum number of Gmail messages to export.")
    parser.add_argument("--newer-than-days", type=int, default=None, help="Only fetch messages newer than this many days.")
    parser.add_argument("--check-env", action="store_true", help="Print whether required environment values are loaded, without showing secrets.")
    args = parser.parse_args()

    if args.check_env:
        print_env_status()
        return
    if not args.sender:
        parser.error("--sender is required unless --check-env is used.")

    from rag_app.gmail_ingestion import export_and_ingest_gmail_sender

    result = export_and_ingest_gmail_sender(
        sender=args.sender,
        settings=get_settings(),
        output_folder=args.output_folder,
        credentials_file=args.credentials_file,
        token_file=args.token_file,
        max_results=args.max_results,
        newer_than_days=args.newer_than_days,
    )

    print(f"sender: {result['sender']}")
    print(f"gmail_query: {result['query']}")
    print(f"emails_exported: {result['emails_exported']}")
    print(f"output_folder: {result['output_folder']}")
    print(f"documents_loaded: {result['ingestion']['documents_loaded']}")
    print(f"collection: {result['ingestion']['collection']}")
    print(f"estimated_openai_cost_usd: {result['ingestion']['usage']['estimated_total_cost_usd']}")


if __name__ == "__main__":
    main()
