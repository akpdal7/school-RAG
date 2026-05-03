# Lightning AI Demo Guide

Use this checklist to demo the school RAG app from GitHub in Lightning AI Studio.

## 1. Push to GitHub

```powershell
git init
git add .
git commit -m "Add school RAG demo"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## 2. Create a Lightning AI Studio

1. Open Lightning AI.
2. Create a new Studio from your GitHub repo.
3. Open a terminal in the Studio.
4. Install dependencies:

```bash
pip install -r requirements.txt
```

## 3. Add Environment Variables

Add these as Lightning AI environment variables or secrets:

```text
MESH_API_KEY
MESH_API_BASE_URL
QDRANT_URL
QDRANT_API_KEY
QDRANT_COLLECTION
```

Optional:

```text
OPENAI_LLM_MODEL
OPENAI_EMBED_MODEL
CHUNK_SIZE
CHUNK_OVERLAP
SIMILARITY_TOP_K
LLM_INPUT_PRICE_PER_1M
LLM_OUTPUT_PRICE_PER_1M
EMBEDDING_PRICE_PER_1M
GMAIL_CREDENTIALS_FILE
GMAIL_TOKEN_FILE
GMAIL_JSON_OUTPUT_FOLDER
```

## 4. Upload Demo Files

Use:

```text
data/documents
```

for school PDFs, Markdown files, text files, and JSON files.

Use:

```text
data/gmail_json
```

for exported teacher email JSON files.

## 5. Gmail Demo Notes

For Gmail ingestion, enable the Gmail API in Google Cloud, create a desktop OAuth client, and place the downloaded credentials JSON at:

```text
data/secrets/gmail_credentials.json
```

The first Gmail run creates:

```text
data/secrets/gmail_token.json
```

For hosted demos, it is usually easiest to generate `gmail_token.json` locally first, then upload it privately into the Lightning Studio. Do not commit Gmail credential or token files to GitHub.

## 6. Start the Backend

```bash
uvicorn src.rag_app.api:app --host 0.0.0.0 --port 8000
```

## 7. Start the Frontend

Open a second terminal:

```bash
export API_BASE_URL="http://localhost:8000"
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

Open the Streamlit port from Lightning AI's exposed ports panel.

## Demo Flow

1. Show `data/documents` and `data/gmail_json`.
2. Click **Ingest folder** for local school files.
3. Enter a teacher sender and click **Fetch Gmail and ingest**.
4. Ask a question whose answer appears in either a document or teacher email.
5. Expand **API usage estimate** to show token counts and estimated cost.
6. Expand **Sources** to show retrieved chunks and file provenance.
7. Mention that Qdrant Cloud persists the vectors across app restarts.
