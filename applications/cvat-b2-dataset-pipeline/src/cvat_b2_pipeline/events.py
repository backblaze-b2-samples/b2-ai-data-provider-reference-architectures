"""Helpers for a B2 event-notification webhook receiver (validation/refresh trigger)."""
from __future__ import annotations

import hashlib
import hmac

SIGNATURE_HEADER = "X-Bz-Event-Notification-Signature"  # value: "v1=<hex hmac-sha256 of body>"


def verify_signature(secret: str, body: bytes, header: str) -> bool:
    expected = "v1=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header or "")


def created_keys(payload: dict, prefix: str = "") -> list[str]:
    """Object names from ObjectCreated events under a prefix."""
    return [e["objectName"] for e in payload.get("events", [])
            if e["eventType"].startswith("b2:ObjectCreated:") and e["objectName"].startswith(prefix)]
