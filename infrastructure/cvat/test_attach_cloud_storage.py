import urllib.parse

import attach_cloud_storage as m

ENV = {"B2_REGION": "eu-central-003", "B2_BUCKET_NAME": "bkt",
       "B2_APPLICATION_KEY_ID": "id", "B2_APPLICATION_KEY": "secret"}


def test_payload_derives_endpoint_and_prefix():
    p = m.build_payload(ENV, "b2", prefix="raw/batch1/")
    attrs = dict(urllib.parse.parse_qsl(p["specific_attributes"]))
    assert attrs == {"endpoint_url": "https://s3.eu-central-003.backblazeb2.com",
                     "region": "eu-central-003", "prefix": "raw/batch1/"}
    assert p["provider_type"] == "AWS_S3_BUCKET" and p["credentials_type"] == "KEY_SECRET_KEY_PAIR"


def test_missing_env_reports_names_only(monkeypatch, capsys):
    for n in m.REQUIRED:
        monkeypatch.delenv(n, raising=False)
    monkeypatch.setenv("B2_APPLICATION_KEY", "topsecret")
    assert m.main(["--name", "x"]) == 1
    err = capsys.readouterr().err
    assert "CVAT_URL" in err and "topsecret" not in err
