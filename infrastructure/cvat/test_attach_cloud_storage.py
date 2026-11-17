import io
import json
import urllib.parse

import pytest

import attach_cloud_storage as m

ENV = {"B2_REGION": "eu-central-003", "B2_BUCKET_NAME": "bkt",
       "B2_APPLICATION_KEY_ID": "id", "B2_APPLICATION_KEY": "secret"}


def test_payload_derives_endpoint_and_prefix():
    p = m.build_payload(ENV, "b2", prefix="raw/batch1/")
    attrs = dict(urllib.parse.parse_qsl(p["specific_attributes"]))
    assert attrs == {"endpoint_url": "https://s3.eu-central-003.backblazeb2.com",
                     "region": "eu-central-003", "prefix": "raw/batch1/"}
    assert p["provider_type"] == "AWS_S3_BUCKET" and p["credentials_type"] == "KEY_SECRET_KEY_PAIR"
    assert p["manifests"] == []


@pytest.mark.parametrize("manifest_args, expected", [
    ([], []),
    (["--manifest", "raw/batch1/manifest.jsonl"], ["raw/batch1/manifest.jsonl"]),
    (["--manifest", "raw/batch1/manifest.jsonl", "--manifest", "raw/batch1/extra.jsonl"],
     ["raw/batch1/manifest.jsonl", "raw/batch1/extra.jsonl"]),
])
def test_cli_sends_explicit_bucket_keys_without_rebasing(monkeypatch, manifest_args, expected):
    for name, value in {**ENV, "CVAT_URL": "https://cvat.example", "CVAT_API_TOKEN": "token"}.items():
        monkeypatch.setenv(name, value)
    requests = []

    def post(request):
        requests.append(json.loads(request.data))
        return io.BytesIO(b'{"id": 7}')

    monkeypatch.setattr(m.urllib.request, "urlopen", post)
    assert m.main(["--name", "storage", "--prefix", "raw/batch1/", *manifest_args]) == 0
    assert requests[0]["manifests"] == expected
    assert dict(urllib.parse.parse_qsl(requests[0]["specific_attributes"]))["prefix"] == "raw/batch1/"


def test_missing_env_reports_names_only(monkeypatch, capsys):
    for n in m.REQUIRED:
        monkeypatch.delenv(n, raising=False)
    monkeypatch.setenv("B2_APPLICATION_KEY", "topsecret")
    assert m.main(["--name", "x"]) == 1
    err = capsys.readouterr().err
    assert "CVAT_URL" in err and "topsecret" not in err
