# Local Deployment and Gmail Extraction Guide

This guide shows exactly which files you edit, where data goes, how to run the app locally, and how Gmail ingestion works.

## 1. What You Are Building

Your RAG app has three source types:

```text
1. School files
   data/documents
   PDF, TXT, MD, JSON

2. Gmail teacher emails through direct Gmail API
   Gmail -> data/gmail_json/*.json -> Qdrant

3. Optional Zapier automation
   Gmail -> Zapier -> /zapier/gmail/ingest -> data/gmail_json/*.json -> Qdrant
```

You do not need Zapier for the normal local demo. Use direct Gmail API extraction first.

Use Zapier only if you want a no-code automation that sends new matching teacher emails into your RAG app.

## 2. Files You Must Update

### Required: `.env`

Create it from `.env.example`:

```powershell
copy .env.example .env
```

Then update:

```env
MESH_API_KEY=your_meshapi_key
MESH_API_BASE_URL=https://api.meshapi.ai/v1

QDRANT_URL=https://your-qdrant-cloud-url
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=school_rag_demo
```

Use the OpenAI-compatible `/v1` base URL:

```env
MESH_API_BASE_URL=https://api.meshapi.ai/v1
```

Keep or adjust these:

```env
OPENAI_LLM_MODEL=gpt-4.1-nano
EMBEDDING_PROVIDER=local_hash
OPENAI_EMBED_MODEL=text-embedding-3-small
FASTEMBED_MODEL_NAME=BAAI/bge-small-en-v1.5
LOCAL_HASH_EMBEDDING_DIM=384

CHUNK_SIZE=1024
CHUNK_OVERLAP=128
SIMILARITY_TOP_K=5

LLM_INPUT_PRICE_PER_1M=0.15
LLM_OUTPUT_PRICE_PER_1M=0.60
EMBEDDING_PRICE_PER_1M=0.00
```

`EMBEDDING_PROVIDER=local_hash` is recommended for your Python 3.13 environment because it needs no extra embedding package. This keeps ingestion local and avoids direct OpenAI embedding calls.

For Gmail:

```env
GMAIL_CREDENTIALS_FILE=data/secrets/gmail_credentials.json
GMAIL_TOKEN_FILE=data/secrets/gmail_token.json
GMAIL_JSON_OUTPUT_FOLDER=data/gmail_json
```

For optional Zapier:

```env
ZAPIER_INGEST_SECRET=choose_a_private_string
```

### Required for Gmail: `data/secrets/gmail_credentials.json`

You download this file from Google Cloud after creating a Gmail OAuth desktop app.

Put it here:

```text
data/secrets/gmail_credentials.json
```

Do not commit this file to GitHub.

### Auto-created after first Gmail login: `data/secrets/gmail_token.json`

This file is created the first time you run Gmail extraction and complete the browser login.

```text
data/secrets/gmail_token.json
```

Do not commit this file to GitHub.

### Data folders

Put school files here:

```text
data/documents
```

Gmail JSON files are saved here:

```text
data/gmail_json
```

## 3. Install and Run Locally

Open PowerShell:

```powershell
cd C:\Users\JMena\Documents\Codex\2026-05-02\write-an-end-to-end-rag

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Start FastAPI:

```powershell
uvicorn src.rag_app.api:app --host 0.0.0.0 --port 8000 --reload
```

Open API docs:

```text
http://localhost:8000/docs
```

Open a second PowerShell terminal:

```powershell
cd C:\Users\JMena\Documents\Codex\2026-05-02\write-an-end-to-end-rag
.\.venv\Scripts\Activate.ps1
streamlit run streamlit_app.py
```

Open Streamlit:

```text
http://localhost:8501
```

## 4. Ingest Local School Documents

Put files into:

```text
data/documents
```

Supported formats:

```text
.pdf
.txt
.md
.markdown
.json
```

Then run:

```powershell
python .\scripts\ingest_folder.py --folder "data\documents"
```

Or in Streamlit:

1. Keep folder path as `data/documents`.
2. Click **Ingest folder**.
3. Wait for document count and API cost estimate.

## 5. Gmail Extraction Without Zapier

This is the recommended approach for your local project.

### What This Does

The script searches Gmail for messages from a teacher:

```text
from:teacher@school.edu newer_than:365d
```

Then it:

1. Gets matching Gmail message IDs.
2. Downloads each message.
3. Extracts subject, sender, date, snippet, and body.
4. Saves each email as JSON in `data/gmail_json`.
5. Ingests `data/gmail_json` into Qdrant.

### Step 1: Create Google Cloud OAuth Credentials

1. Go to Google Cloud Console.
2. Create or select a project.
3. Enable the Gmail API.
4. Configure OAuth consent screen.
5. Create OAuth Client ID.
6. Choose **Desktop app** as the app type.
7. Download the JSON credentials file.
8. Rename it to:

```text
gmail_credentials.json
```

9. Put it here:

```text
data/secrets/gmail_credentials.json
```

### Step 2: Run Gmail Extraction

Make sure FastAPI does not need to be running for this CLI script. The script talks directly to Gmail, writes JSON, and ingests into Qdrant.

Run:

```powershell
.\.venv\Scripts\Activate.ps1
python .\scripts\gmail_to_qdrant.py --sender "teacher@school.edu" --max-results 25 --newer-than-days 365
```

Replace:

```text
teacher@school.edu
```

with the actual teacher sender email.

### Step 3: First-Run Browser Login

The first time you run the command:

1. A browser window opens.
2. You sign into Gmail.
3. You approve read-only Gmail access.
4. The app creates:

```text
data/secrets/gmail_token.json
```

After that, future runs reuse the token.

### Step 4: Confirm JSON Files Were Created

Check:

```text
data/gmail_json
```

You should see files like:

```text
2026-04-28T15_30_00_messageid_Homework_due_Friday.json
```

### Step 5: Ask Questions

In Streamlit, ask questions like:

```text
What homework did the teacher assign?
```

```text
What dates were mentioned by the teacher?
```

```text
Summarize the latest emails from the math teacher.
```

## 6. Gmail Extraction From Streamlit

You can also use the UI.

1. Start FastAPI.
2. Start Streamlit.
3. In the sidebar, find **Gmail sender**.
4. Enter the teacher email.
5. Keep:

```text
Gmail JSON folder: data/gmail_json
OAuth credentials JSON: data/secrets/gmail_credentials.json
OAuth token cache: data/secrets/gmail_token.json
```

6. Click **Fetch Gmail and ingest**.

The first run may open a browser login from the FastAPI process.

## 7. Do You Need Zapier?

For your current local demo: **No, you do not need Zapier.**

Use direct Gmail API extraction because it can backfill older teacher emails and is easier to debug locally.

Use Zapier only if you want automation for new incoming emails, for example:

```text
When a new email arrives from teacher@school.edu,
send it to my RAG app automatically.
```

## 8. Optional Zapier Setup

Important: Zapier cannot call your private `localhost:8000` URL directly.

To use Zapier, your FastAPI app must be reachable from the internet. You have two common choices:

```text
Option A: Run FastAPI on Lightning AI and use its public URL.
Option B: Use a tunnel such as ngrok for local testing.
```

### Zapier Flow

```text
Gmail trigger -> Webhooks by Zapier POST -> FastAPI /zapier/gmail/ingest
```

### Step 1: Set a Shared Secret

In `.env`:

```env
ZAPIER_INGEST_SECRET=choose_a_private_string
```

Restart FastAPI after changing `.env`.

### Step 2: Start FastAPI

```powershell
uvicorn src.rag_app.api:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Make FastAPI Public

For local testing with a tunnel, your public URL will look like:

```text
https://your-public-url.example.com
```

The Zapier endpoint is:

```text
https://your-public-url.example.com/zapier/gmail/ingest
```

For Lightning AI, use the public URL for your FastAPI service.

### Step 4: Create the Zap

In Zapier:

1. Create a new Zap.
2. Trigger app: **Gmail**.
3. Trigger event: **New Email Matching Search**.
4. Search string:

```text
from:teacher@school.edu
```

You can narrow it:

```text
from:teacher@school.edu newer_than:7d
```

5. Test the trigger.

Zapier's Gmail docs list **New Email Matching Search** as a Gmail trigger.

### Step 5: Add Webhook Action

1. Action app: **Webhooks by Zapier**.
2. Event: **POST**.
3. URL:

```text
https://your-public-url.example.com/zapier/gmail/ingest
```

4. Payload Type:

```text
json
```

5. Data fields:

```json
{
  "secret": "choose_a_private_string",
  "sender": "teacher@school.edu",
  "from_email": "<map Gmail From field>",
  "to": "<map Gmail To field>",
  "cc": "<map Gmail Cc field>",
  "subject": "<map Gmail Subject field>",
  "date": "<map Gmail Date field>",
  "body_plain": "<map Gmail Body Plain field>",
  "body_html": "<map Gmail Body HTML field>",
  "snippet": "<map Gmail Snippet field>",
  "message_id": "<map Gmail Message ID field>",
  "output_folder": "data/gmail_json"
}
```

Use Zapier's field picker for the angle-bracket fields.

### Step 6: Test the Zap

When Zapier posts the email:

1. FastAPI receives it.
2. The app saves one JSON file to `data/gmail_json`.
3. The app ingests `data/gmail_json` into Qdrant.
4. The response includes estimated API cost.

### Step 7: Turn On the Zap

After testing, turn on the Zap.

Use this only for new emails. For historical/backfill emails, use the direct Gmail CLI script.

## 9. Which Gmail Option Should You Use?

Use this decision table:

```text
Need older emails from a teacher?
Use direct Gmail API CLI.

Need local demo?
Use direct Gmail API CLI or Streamlit Gmail button.

Need automatic ingestion of future teacher emails?
Use Zapier.

Do not want to configure Google Cloud OAuth?
Zapier may be easier, but it needs a public FastAPI URL.

Need full control and GitHub/Learning demo value?
Use direct Gmail API.
```

## 10. Troubleshooting

### Missing Gmail credentials

Error:

```text
Gmail OAuth credentials file was not found
```

Fix:

```text
Put data/secrets/gmail_credentials.json in place.
```

### Browser login does not open

Run Gmail extraction locally first instead of from a hosted server:

```powershell
python .\scripts\gmail_to_qdrant.py --sender "teacher@school.edu"
```

Then upload the generated `gmail_token.json` privately if you need a cloud demo.

### Zapier cannot reach localhost

Zapier cannot POST to:

```text
http://localhost:8000
```

Use Lightning AI public URL or a tunnel.

### Emails exported but answers do not mention them

Try:

```powershell
python .\scripts\ingest_folder.py --folder "data\gmail_json"
```

Then ask a more specific question with the teacher name, subject, or date.

## 11. Official References

- Gmail on Zapier supports triggers including **New Email Matching Search**: https://help.zapier.com/hc/en-us/articles/8495933589645-How-to-get-started-with-Gmail-on-Zapier
- Zapier Webhooks can send JSON payloads: https://help.zapier.com/hc/en-us/articles/8496083355661-How-to-Get-Started-with-Webhooks-by-Zapier
- Google Workspace API OAuth pattern: https://codelabs.developers.google.com/codelabs/gsuite-apis-intro/
