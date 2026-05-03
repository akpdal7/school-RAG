# End-to-End School RAG App

This project is a GitHub-ready retrieval augmented generation (RAG) demo for school documents and teacher emails. It ingests PDF, Markdown, text, JSON, and exported Gmail messages into Qdrant Cloud using LlamaIndex, then exposes question answering through FastAPI and Streamlit. Chat calls go through MeshAPI using its OpenAI-compatible API. Embeddings run locally by default because MeshAPI may not expose embedding models for every account.

## Architecture

```text
data/documents
  pdf, md, txt, json
        |
        v
data/gmail_json <--- Gmail sender export
        |
        v
LlamaIndex readers -> chunking -> local embeddings
        |
        v
Qdrant Cloud vector collection
        |
        v
FastAPI /chat, /ingest, /gmail/ingest
        |
        v
Streamlit demo UI
```

## Features

- Ingests `.pdf`, `.md`, `.markdown`, `.txt`, and `.json` files.
- Exports Gmail messages from a teacher or sender into JSON files.
- Ingests exported Gmail JSON into Qdrant Cloud.
- Uses LlamaIndex for loading, chunking, indexing, retrieval, and answer synthesis.
- Uses MeshAPI as the OpenAI-compatible chat model gateway.
- Uses local dependency-free embeddings by default, so document indexing does not require OpenAI embedding calls.
- FastAPI backend and Streamlit frontend.
- Shows token counts and estimated API cost after ingestion and chat.

## Project Layout

```text
.
|-- data/
|   |-- documents/
|   |-- gmail_json/
|   `-- secrets/
|-- scripts/
|   |-- gmail_to_qdrant.py
|   `-- ingest_folder.py
|-- src/
|   `-- rag_app/
|       |-- api.py
|       |-- config.py
|       |-- gmail_ingestion.py
|       |-- ingestion.py
|       |-- models.py
|       |-- qdrant_store.py
|       |-- query.py
|       `-- usage.py
|-- streamlit_app.py
|-- requirements.txt
|-- .env.example
`-- lightning.md
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`:

```env
MESH_API_KEY=your-meshapi-key
MESH_API_BASE_URL=https://api.meshapi.ai/v1

QDRANT_URL=https://your-qdrant-cloud-url
QDRANT_API_KEY=your-qdrant-api-key
QDRANT_COLLECTION=school_rag_demo

OPENAI_LLM_MODEL=gpt-4.1-nano
EMBEDDING_PROVIDER=local_hash
OPENAI_EMBED_MODEL=text-embedding-3-small
FASTEMBED_MODEL_NAME=BAAI/bge-small-en-v1.5
LOCAL_HASH_EMBEDDING_DIM=384

LLM_INPUT_PRICE_PER_1M=0.15
LLM_OUTPUT_PRICE_PER_1M=0.60
EMBEDDING_PRICE_PER_1M=0.00

GMAIL_CREDENTIALS_FILE=data/secrets/gmail_credentials.json
GMAIL_TOKEN_FILE=data/secrets/gmail_token.json
GMAIL_JSON_OUTPUT_FOLDER=data/gmail_json
```

MeshAPI's docs say the integration is OpenAI-compatible: use your MeshAPI key, replace the SDK base URL, and pass model IDs normally. This project uses `MESH_API_BASE_URL=https://api.meshapi.ai/v1` for chat calls. Embeddings use a local hash embedding model unless you set `EMBEDDING_PROVIDER=openai_compatible` and configure a MeshAPI-supported embedding model.

## Data Folders

Use these folders:

- `data/documents`: school PDFs, Markdown files, text files, and JSON files.
- `data/gmail_json`: teacher emails exported as JSON.
- `data/secrets`: Gmail OAuth credentials and token files.

The folder structure is committed, but the actual document, email, and secret files are ignored by Git.

## Ingest School Documents

Put files in:

```text
data/documents
```

Then run:

```powershell
python .\scripts\ingest_folder.py --folder "data\documents"
```

Or use **Ingest folder** in Streamlit.

## Gmail Teacher Email Ingestion

The Gmail ingestion flow:

1. Searches Gmail for messages from a sender.
2. Saves each email as a JSON file in `data/gmail_json`.
3. Ingests the JSON files into Qdrant.
4. Makes those emails available as RAG sources.

### Gmail OAuth Setup

1. Create or open a Google Cloud project.
2. Enable the Gmail API.
3. Configure the OAuth consent screen.
4. Create an OAuth client ID for a desktop app.
5. Download the client JSON file.
6. Save it here:

```text
data/secrets/gmail_credentials.json
```

The first Gmail run opens a browser OAuth flow and creates:

```text
data/secrets/gmail_token.json
```

Both files are ignored by Git.

### Gmail CLI

```powershell
python .\scripts\gmail_to_qdrant.py --sender "teacher@school.edu" --max-results 25 --newer-than-days 365
```

Each email JSON includes sender, recipients, subject, date, snippet, and extracted message text.

For a full local deployment, direct Gmail extraction, and optional Zapier walkthrough, see [docs/LOCAL_DEPLOYMENT_AND_GMAIL_GUIDE.md](docs/LOCAL_DEPLOYMENT_AND_GMAIL_GUIDE.md).

## Run the App

Start FastAPI:

```powershell
uvicorn src.rag_app.api:app --host 0.0.0.0 --port 8000 --reload
```

Start Streamlit in a second terminal:

```powershell
streamlit run streamlit_app.py
```

Open:

```text
http://localhost:8501
```

## API Endpoints

### Ingest Folder

```http
POST /ingest
Content-Type: application/json

{
  "folder_path": "data/documents"
}
```

### Gmail Sender Ingest

```http
POST /gmail/ingest
Content-Type: application/json

{
  "sender": "teacher@school.edu",
  "max_results": 25,
  "newer_than_days": 365,
  "output_folder": "data/gmail_json",
  "credentials_file": "data/secrets/gmail_credentials.json",
  "token_file": "data/secrets/gmail_token.json"
}
```

### Chat

```http
POST /chat
Content-Type: application/json

{
  "question": "What homework did the teacher assign?",
  "top_k": 5
}
```

## API Cost Tracking

The app reports estimated MeshAPI/OpenAI-compatible usage after ingestion and each chat answer:

- LLM input tokens
- LLM output tokens
- Embedding tokens
- Estimated LLM cost
- Estimated embedding cost
- Estimated total cost

These are demo-friendly estimates from local token counts and the configured per-token prices. MeshAPI is the authoritative source for billed chat credits. Local embeddings run on your machine and are configured with zero API cost.

## Lightning AI Demo

See [lightning.md](lightning.md). For Gmail in a hosted demo, generate `data/secrets/gmail_token.json` locally first, then upload it privately to the Studio.
