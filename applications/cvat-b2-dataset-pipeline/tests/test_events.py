import hashlib
import hmac

from cvat_b2_pipeline import events


def _sig(secret, body):
    return "v1=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_signature_roundtrip():
    body = b'{"events":[]}'
    assert events.verify_signature("s" * 32, body, _sig("s" * 32, body))
    assert not events.verify_signature("s" * 32, body, _sig("x" * 32, body))
    assert not events.verify_signature("s" * 32, body, "")


def test_created_keys_filters_type_and_prefix():
    payload = {"events": [
        {"eventType": "b2:ObjectCreated:Upload", "objectName": "exports/b1/a.json"},
        {"eventType": "b2:ObjectDeleted:Delete", "objectName": "exports/b1/b.json"},
        {"eventType": "b2:ObjectCreated:Copy", "objectName": "raw/x"},
    ]}
    assert events.created_keys(payload, "exports/") == ["exports/b1/a.json"]
