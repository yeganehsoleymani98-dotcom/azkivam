#!/usr/bin/env python3
import argparse
import asyncio
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse, JSONResponse

# ---- Notes on correctness ----
# - Replies are sent via Send API: POST /{version}/me/messages with recipient.id = IGSID. :contentReference[oaicite:4]{index=4}
# - Webhook verification uses hub.challenge/hub.verify_token. :contentReference[oaicite:5]{index=5}
# - Payload validation uses X-Hub-Signature-256 (HMAC SHA256, "sha256=<hex>"). :contentReference[oaicite:6]{index=6}

@dataclass(frozen=True)
class Settings:
    verify_token: str
    access_token: str
    app_secret: Optional[str]
    graph_version: str
    reply_text: str

# simple in-memory dedupe (good enough for low volume)
_DEDUPE: Dict[str, float] = {}
_DEDUPE_TTL_S = 60 * 10  # 10 minutes


def _dedupe_seen(key: str) -> bool:
    now = time.time()
    # prune occasionally
    if len(_DEDUPE) > 5000:
        for k, ts in list(_DEDUPE.items()):
            if now - ts > _DEDUPE_TTL_S:
                _DEDUPE.pop(k, None)

    ts = _DEDUPE.get(key)
    if ts and (now - ts) <= _DEDUPE_TTL_S:
        return True
    _DEDUPE[key] = now
    return False


def _verify_signature(app_secret: str, raw_body: bytes, x_hub_signature_256: Optional[str]) -> None:
    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="Missing X-Hub-Signature-256")

    # header format: "sha256=<hex>"
    if not x_hub_signature_256.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Invalid X-Hub-Signature-256 format")

    expected = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    got = x_hub_signature_256.split("=", 1)[1].strip()

    if not hmac.compare_digest(expected, got):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")


async def _send_text_message(settings: Settings, recipient_igsid: str, text: str) -> Dict[str, Any]:
    url = f"https://graph.facebook.com/{settings.graph_version}/me/messages"
    payload = {
        "messaging_type": "RESPONSE",
        "recipient": {"id": recipient_igsid},
        "message": {"text": text},
    }

    # retry on transient errors / 429
    backoff = 1.0
    async with httpx.AsyncClient(timeout=15) as client:
        for attempt in range(5):
            r = await client.post(url, params={"access_token": settings.access_token}, json=payload)
            if r.status_code == 429 or 500 <= r.status_code < 600:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 20)
                continue

            # raise for other non-2xx
            r.raise_for_status()
            return r.json()

    raise RuntimeError("Send API failed after retries")


def _extract_incoming_text_events(body: Dict[str, Any]) -> list[dict]:
    """
    Returns list of {sender_id, mid, text} for inbound messages.
    Payload shape is typically entry[] -> messaging[] -> message{text, mid} for IG Messaging webhooks.
    """
    out = []
    for entry in body.get("entry", []) or []:
        for evt in entry.get("messaging", []) or []:
            msg = evt.get("message") or {}
            sender = (evt.get("sender") or {}).get("id")
            if not sender:
                continue

            # ignore echoes (messages your page/app sent)
            if msg.get("is_echo"):
                continue

            text = msg.get("text")
            mid = msg.get("mid") or f"no-mid:{sender}:{hash(json.dumps(msg, sort_keys=True))}"

            if text:
                out.append({"sender_id": str(sender), "mid": str(mid), "text": str(text)})
    return out


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(title="Instagram DM Auto-Reply (Messenger API for Instagram)")

    @app.get("/webhook", response_class=PlainTextResponse)
    async def webhook_verify(request: Request):
        qp = request.query_params
        mode = qp.get("hub.mode")
        token = qp.get("hub.verify_token")
        challenge = qp.get("hub.challenge")

        if mode == "subscribe" and token == settings.verify_token and challenge:
            return PlainTextResponse(challenge)

        raise HTTPException(status_code=403, detail="Webhook verification failed")

    @app.post("/webhook")
    async def webhook_receive(
        request: Request,
        background: BackgroundTasks,
        x_hub_signature_256: Optional[str] = Header(default=None, convert_underscores=False),
    ):
        raw = await request.body()

        # Optional signature verification (recommended if you have the App Secret)
        if settings.app_secret:
            _verify_signature(settings.app_secret, raw, x_hub_signature_256)

        try:
            body = json.loads(raw.decode("utf-8"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON")

        events = _extract_incoming_text_events(body)

        # enqueue replies
        for ev in events:
            # dedupe by message id
            if _dedupe_seen(ev["mid"]):
                continue

            sender_id = ev["sender_id"]

            # keep it simple: always reply with the same text
            background.add_task(_send_text_message, settings, sender_id, settings.reply_text)

        return JSONResponse({"ok": True, "received": len(events)})

    @app.get("/health")
    async def health():
        return {"ok": True}

    return app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-token", required=True, help="Webhook verify token (hub.verify_token)")
    parser.add_argument("--access-token", required=True, help="Page/IG access token with messaging permissions")
    parser.add_argument("--app-secret", default=None, help="Meta App Secret (enables X-Hub-Signature-256 verification)")
    parser.add_argument("--graph-version", default="v24.0", help="Graph API version (default: v24.0)")
    parser.add_argument("--reply-text", default="Got it ✅", help="Auto-reply text")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    settings = Settings(
        verify_token=args.verify_token,
        access_token=args.access_token,
        app_secret=args.app_secret,
        graph_version=args.graph_version,
        reply_text=args.reply_text,
    )

    app = create_app(settings)

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
