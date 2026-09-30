"""Env-driven B2 config. Secrets never appear in repr or error messages."""
from __future__ import annotations

import os
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

REQUIRED = ("B2_APPLICATION_KEY_ID", "B2_APPLICATION_KEY", "B2_BUCKET_NAME", "B2_REGION")


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    key_id: str = field(repr=False)
    key: str = field(repr=False)
    bucket: str
    region: str
    endpoint: str


def load(env_file: str = ".env") -> Config:
    """Load .env (if present) then read config from the environment."""
    path = Path(env_file)
    if path.exists():
        if path.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
            print(f"warning: {env_file} is group/world accessible; chmod 600", file=sys.stderr)
        load_dotenv(path, override=False)
    missing = [name for name in REQUIRED if not os.environ.get(name)]
    if missing:
        raise ConfigError(f"missing required env vars: {', '.join(missing)}")
    region = os.environ["B2_REGION"]
    return Config(
        key_id=os.environ["B2_APPLICATION_KEY_ID"],
        key=os.environ["B2_APPLICATION_KEY"],
        bucket=os.environ["B2_BUCKET_NAME"],
        region=region,
        endpoint=os.environ.get("B2_ENDPOINT") or f"https://s3.{region}.backblazeb2.com",
    )
