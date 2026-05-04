import os

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def render_usage(usage: dict) -> None:
    st.metric("Estimated API cost", f"${usage['estimated_total_cost_usd']:.6f}")
    cols = st.columns(3)
    cols[0].metric("LLM input tokens", f"{usage['llm_input_tokens']:,}")
    cols[1].metric("LLM output tokens", f"{usage['llm_output_tokens']:,}")
    cols[2].metric("Embedding tokens", f"{usage['embedding_tokens']:,}")
    st.caption(usage["pricing_note"])


st.set_page_config(page_title="RAG Demo", layout="wide")

st.title("RAG Demo")


with st.sidebar:
    st.header("Ingest")
    st.caption("Upload school files from your computer.")
    uploaded_files = st.file_uploader(
        "Files",
        type=["pdf", "md", "markdown", "txt", "json"],
        accept_multiple_files=True,
    )
    upload_clicked = st.button("Upload and ingest", type="primary", use_container_width=True)

    with st.expander("Server folder ingest"):
        folder_path = st.text_input(
            "Folder path on the server",
            value="data/documents",
            placeholder=r"data/documents",
        )
        ingest_clicked = st.button("Ingest server folder", use_container_width=True)

    st.divider()
    st.subheader("Gmail sender")
    gmail_sender = st.text_input("Sender email", placeholder="teacher@school.edu")
    gmail_max_results = st.number_input("Max emails", min_value=1, max_value=500, value=25, step=1)
    gmail_newer_than_days = st.number_input("Newer than days", min_value=0, max_value=3650, value=365, step=1)
    gmail_output_folder = st.text_input("Gmail JSON folder", value="data/gmail_json")
    gmail_credentials_file = st.text_input("OAuth credentials JSON", value="data/secrets/gmail_credentials.json")
    gmail_token_file = st.text_input("OAuth token cache", value="data/secrets/gmail_token.json")
    gmail_clicked = st.button("Fetch Gmail and ingest", use_container_width=True)

    st.divider()
    top_k = st.slider("Retrieved chunks", min_value=1, max_value=20, value=5)
    st.caption(f"API: {API_BASE_URL}")


if "messages" not in st.session_state:
    st.session_state.messages = []


if upload_clicked:
    if not uploaded_files:
        st.sidebar.error("Choose at least one supported file first.")
    else:
        with st.sidebar.status("Uploading and ingesting files...", expanded=True) as status:
            try:
                files = [
                    (
                        "files",
                        (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type or "application/octet-stream",
                        ),
                    )
                    for uploaded_file in uploaded_files
                ]
                response = requests.post(
                    f"{API_BASE_URL}/upload/ingest",
                    files=files,
                    timeout=900,
                )
                response.raise_for_status()
                payload = response.json()
                st.write(f"Uploaded files: {len(uploaded_files)}")
                st.write(f"Loaded documents: {payload['documents_loaded']}")
                st.write(f"Collection: {payload['collection']}")
                render_usage(payload["usage"])
                status.update(label=payload["message"], state="complete")
            except requests.RequestException as exc:
                status.update(label="Upload ingestion failed", state="error")
                detail = exc.response.text if getattr(exc, "response", None) is not None else str(exc)
                st.sidebar.error(detail)


if ingest_clicked:
    if not folder_path:
        st.sidebar.error("Enter a folder path first.")
    else:
        with st.sidebar.status("Ingesting documents...", expanded=True) as status:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/ingest",
                    json={"folder_path": folder_path},
                    timeout=600,
                )
                response.raise_for_status()
                payload = response.json()
                st.write(f"Loaded documents: {payload['documents_loaded']}")
                st.write(f"Collection: {payload['collection']}")
                render_usage(payload["usage"])
                status.update(label=payload["message"], state="complete")
            except requests.RequestException as exc:
                status.update(label="Ingestion failed", state="error")
                detail = exc.response.text if getattr(exc, "response", None) is not None else str(exc)
                st.sidebar.error(detail)


if gmail_clicked:
    if not gmail_sender:
        st.sidebar.error("Enter a sender email first.")
    else:
        with st.sidebar.status("Fetching Gmail and ingesting JSON...", expanded=True) as status:
            try:
                payload = {
                    "sender": gmail_sender,
                    "max_results": int(gmail_max_results),
                    "newer_than_days": int(gmail_newer_than_days) if gmail_newer_than_days else None,
                    "output_folder": gmail_output_folder,
                    "credentials_file": gmail_credentials_file,
                    "token_file": gmail_token_file,
                }
                response = requests.post(
                    f"{API_BASE_URL}/gmail/ingest",
                    json=payload,
                    timeout=900,
                )
                response.raise_for_status()
                result = response.json()
                st.write(f"Emails exported: {result['emails_exported']}")
                st.write(f"JSON folder: {result['output_folder']}")
                st.write(f"Documents loaded: {result['ingestion']['documents_loaded']}")
                st.write(f"Collection: {result['ingestion']['collection']}")
                render_usage(result["ingestion"]["usage"])
                status.update(label="Gmail export and ingestion complete.", state="complete")
            except requests.RequestException as exc:
                status.update(label="Gmail ingestion failed", state="error")
                detail = exc.response.text if getattr(exc, "response", None) is not None else str(exc)
                st.sidebar.error(detail)


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Sources"):
                for source in message["sources"]:
                    st.markdown(f"**{source.get('file_name') or 'Unknown file'}**")
                    if source.get("file_path"):
                        st.caption(source["file_path"])
                    if source.get("page_label"):
                        st.caption(f"Page: {source['page_label']}")
                    if source.get("score") is not None:
                        st.caption(f"Score: {source['score']:.3f}")
                    st.write(source.get("text", ""))
        if message.get("usage"):
            with st.expander("API usage estimate"):
                render_usage(message["usage"])


question = st.chat_input("Ask a question about your documents")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching your indexed documents..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/chat",
                    json={"question": question, "top_k": top_k},
                    timeout=180,
                )
                response.raise_for_status()
                payload = response.json()
                st.markdown(payload["answer"])
                if payload.get("usage"):
                    with st.expander("API usage estimate", expanded=True):
                        render_usage(payload["usage"])
                if payload.get("sources"):
                    with st.expander("Sources"):
                        for source in payload["sources"]:
                            st.markdown(f"**{source.get('file_name') or 'Unknown file'}**")
                            if source.get("file_path"):
                                st.caption(source["file_path"])
                            if source.get("page_label"):
                                st.caption(f"Page: {source['page_label']}")
                            if source.get("score") is not None:
                                st.caption(f"Score: {source['score']:.3f}")
                            st.write(source.get("text", ""))

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": payload["answer"],
                        "sources": payload.get("sources", []),
                        "usage": payload.get("usage"),
                    }
                )
            except requests.RequestException as exc:
                detail = exc.response.text if getattr(exc, "response", None) is not None else str(exc)
                st.error(detail)
