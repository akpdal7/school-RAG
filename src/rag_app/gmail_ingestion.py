import base64
import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from rag_app.config import Settings
from rag_app.ingestion import ingest_folder


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def _safe_file_part(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_")
    return cleaned[:80] or "gmail_message"


def _decode_body(data: str | None) -> str:
    if not data:
        return ""
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", errors="replace")


def _strip_html(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    value = re.sub(r"(?s)<br\s*/?>", "\n", value)
    value = re.sub(r"(?s)</p\s*>", "\n", value)
    value = re.sub(r"(?s)<.*?>", " ", value)
    value = unescape(value)
    return re.sub(r"\s+\n", "\n", re.sub(r"[ \t]+", " ", value)).strip()


def _headers_to_dict(payload: dict) -> dict:
    headers = payload.get("headers", [])
    return {item.get("name", "").lower(): item.get("value", "") for item in headers}


def _extract_message_text(payload: dict) -> str:
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")

    if mime_type == "text/plain" and body_data:
        return _decode_body(body_data).strip()
    if mime_type == "text/html" and body_data:
        return _strip_html(_decode_body(body_data))

    plain_parts = []
    html_parts = []
    for part in payload.get("parts", []) or []:
        text = _extract_message_text(part)
        if not text:
            continue
        if part.get("mimeType") == "text/html":
            html_parts.append(text)
        else:
            plain_parts.append(text)

    return "\n\n".join(plain_parts or html_parts).strip()


def _parse_email_date(value: str) -> str | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.isoformat()
    except (TypeError, ValueError):
        return value


def _get_gmail_service(credentials_file: str, token_file: str):
    credentials_path = Path(credentials_file).expanduser().resolve()
    token_path = Path(token_file).expanduser().resolve()
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                raise FileNotFoundError(
                    "Gmail OAuth credentials file was not found. "
                    f"Expected: {credentials_path}"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)


def _list_message_ids(service, query: str, max_results: int) -> list[str]:
    message_ids = []
    request = service.users().messages().list(userId="me", q=query, maxResults=min(max_results, 500))

    while request is not None and len(message_ids) < max_results:
        response = request.execute()
        message_ids.extend(item["id"] for item in response.get("messages", []))
        if len(message_ids) >= max_results:
            break
        request = service.users().messages().list_next(request, response)

    return message_ids[:max_results]


def export_gmail_sender_to_json(
    sender: str,
    output_folder: str,
    credentials_file: str,
    token_file: str,
    max_results: int = 25,
    newer_than_days: int | None = None,
) -> dict:
    output_path = Path(output_folder).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    query_parts = [f"from:{sender}"]
    if newer_than_days:
        query_parts.append(f"newer_than:{newer_than_days}d")
    query = " ".join(query_parts)

    service = _get_gmail_service(credentials_file, token_file)
    message_ids = _list_message_ids(service, query, max_results)

    exported_files = []
    for message_id in message_ids:
        message = service.users().messages().get(userId="me", id=message_id, format="full").execute()
        payload = message.get("payload", {})
        headers = _headers_to_dict(payload)
        subject = headers.get("subject", "(no subject)")
        sent_at = _parse_email_date(headers.get("date", ""))
        body = _extract_message_text(payload) or message.get("snippet", "")

        document = {
            "source_type": "gmail",
            "gmail_message_id": message_id,
            "thread_id": message.get("threadId"),
            "sender_filter": sender,
            "from": headers.get("from"),
            "to": headers.get("to"),
            "cc": headers.get("cc"),
            "subject": subject,
            "sent_at": sent_at,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "snippet": message.get("snippet", ""),
            "text": f"Subject: {subject}\nFrom: {headers.get('from', '')}\nDate: {sent_at or ''}\n\n{body}",
        }

        filename = f"{_safe_file_part(sent_at or 'unknown_date')}_{message_id}_{_safe_file_part(subject)}.json"
        file_path = output_path / filename
        file_path.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")
        exported_files.append(str(file_path))

    return {
        "sender": sender,
        "query": query,
        "output_folder": str(output_path),
        "emails_exported": len(exported_files),
        "exported_files": exported_files,
    }


def export_and_ingest_gmail_sender(
    sender: str,
    settings: Settings,
    output_folder: str,
    credentials_file: str,
    token_file: str,
    max_results: int = 25,
    newer_than_days: int | None = None,
) -> dict:
    export_result = export_gmail_sender_to_json(
        sender=sender,
        output_folder=output_folder,
        credentials_file=credentials_file,
        token_file=token_file,
        max_results=max_results,
        newer_than_days=newer_than_days,
    )
    ingest_result = ingest_folder(export_result["output_folder"], settings)
    return {
        **export_result,
        "ingestion": ingest_result,
    }


def save_zapier_email_and_ingest(payload: dict, settings: Settings, output_folder: str) -> dict:
    output_path = Path(output_folder).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    subject = payload.get("subject") or "(no subject)"
    sender = payload.get("from_email") or payload.get("sender") or ""
    message_id = payload.get("message_id") or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    sent_at = payload.get("date")
    body = payload.get("body_plain") or _strip_html(payload.get("body_html") or "") or payload.get("snippet") or ""

    document = {
        "source_type": "gmail_zapier",
        "gmail_message_id": message_id,
        "from": sender,
        "to": payload.get("to"),
        "cc": payload.get("cc"),
        "subject": subject,
        "sent_at": sent_at,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "snippet": payload.get("snippet", ""),
        "text": f"Subject: {subject}\nFrom: {sender}\nDate: {sent_at or ''}\n\n{body}",
    }

    filename = f"zapier_{_safe_file_part(str(message_id))}_{_safe_file_part(subject)}.json"
    file_path = output_path / filename
    file_path.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")

    ingest_result = ingest_folder(str(output_path), settings)
    return {
        "output_folder": str(output_path),
        "exported_file": str(file_path),
        "ingestion": ingest_result,
    }
