"""Object-key layout shared by every stage (see architectures/.../object-layout.md)."""
from __future__ import annotations

MANIFEST_NAME = "manifest.json"  # release commit marker, written last


def raw_prefix(batch: str) -> str:
    """CVAT source-storage prefix for one ingest batch."""
    return f"raw/{batch}/"


def export_prefix(batch: str) -> str:
    """CVAT target-storage prefix for annotation exports of one batch."""
    return f"exports/{batch}/"


def release_prefix(dataset: str, version: str) -> str:
    return f"releases/{dataset}/{version}/"


def release_manifest_key(dataset: str, version: str) -> str:
    return release_prefix(dataset, version) + MANIFEST_NAME
