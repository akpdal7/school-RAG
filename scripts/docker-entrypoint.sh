#!/bin/sh
set -eu

mkdir -p data/secrets data/gmail_json data/documents

if [ -n "${GMAIL_CREDENTIALS_JSON:-}" ]; then
  printf '%s' "$GMAIL_CREDENTIALS_JSON" > "${GMAIL_CREDENTIALS_FILE:-data/secrets/gmail_credentials.json}"
fi

if [ -n "${GMAIL_TOKEN_JSON:-}" ]; then
  printf '%s' "$GMAIL_TOKEN_JSON" > "${GMAIL_TOKEN_FILE:-data/secrets/gmail_token.json}"
fi

uvicorn rag_app.api:app --host 127.0.0.1 --port 8000 &

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}" \
streamlit run streamlit_app.py \
  --server.address=0.0.0.0 \
  --server.port=8501 \
  --server.enableCORS=false \
  --server.enableXsrfProtection=true
