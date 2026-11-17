import boto3
import pytest
from botocore.config import Config as BotoConfig
from moto import mock_aws

from cvat_b2_pipeline import cli, storage
from cvat_b2_pipeline.config import Config

BUCKET = "test-cvat-b2-bucket"
SECRET = "SUPERSECRETKEYVALUE123"


@pytest.fixture(autouse=True)
def isolated_writer_locks(tmp_path, monkeypatch):
    monkeypatch.setenv("CVAT_B2_LOCK_DIR", str(tmp_path / "publisher-locks"))


@pytest.fixture
def cfg():
    return Config(key_id="keyid123", key=SECRET, bucket=BUCKET, region="us-east-1",
                  endpoint="https://s3.us-east-1.backblazeb2.com")


@pytest.fixture
def s3(cfg, monkeypatch):
    """moto covers S3 data operations only; key scoping, Object Lock and lifecycle need live B2."""
    with mock_aws():
        # Pin SigV4 like make_client; the SDK default varies by environment (CI signs with SigV2).
        client = boto3.client("s3", region_name="us-east-1",
                              config=BotoConfig(signature_version="s3v4"))
        client.create_bucket(Bucket=BUCKET)
        monkeypatch.setattr(storage, "make_client", lambda _cfg: client)
        # moto's retention writes update its object state; model the missing GET API from that state.
        def get_retention(**params):
            head = client.head_object(**params)
            if "ObjectLockMode" not in head:
                return {"Retention": {}}
            return {"Retention": {"Mode": head["ObjectLockMode"],
                                  "RetainUntilDate": head["ObjectLockRetainUntilDate"]}}
        monkeypatch.setattr(client, "get_object_retention", get_retention)
        yield client


@pytest.fixture
def dataset(tmp_path):
    from cvat_b2_pipeline import synth
    synth.generate(tmp_path / "out", 4, seed=1)
    return tmp_path / "out"


@pytest.fixture
def run(cfg, monkeypatch):
    monkeypatch.setattr(cli, "load", lambda: cfg)
    return cli.main
