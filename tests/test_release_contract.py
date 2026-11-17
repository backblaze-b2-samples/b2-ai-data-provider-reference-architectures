"""The shared release contract accepts safe paths for every supported modality."""
import copy
import json
from pathlib import Path

import jsonschema
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas/release-manifest.schema.json").read_text())
EXAMPLE = json.loads((ROOT / "manifests/release-manifest.multimodal.example.json").read_text())


@pytest.mark.parametrize("modality, path", [
    ("audio", "data/audio/recording.wav"),
    ("video", "data/clips/scene.mp4"),
    ("text", "data/transcript.txt"),
    ("tabular", "data/measurements.parquet"),
    ("image", "images/frame.png"),
    ("multimodal", "data/episode/metadata.json"),
])
def test_modality_payload_paths(modality, path):
    release = copy.deepcopy(EXAMPLE)
    release["modalities"] = [modality]
    release["files"][0]["path"] = path
    jsonschema.Draft202012Validator(SCHEMA).validate(release)


@pytest.mark.parametrize("path", [
    "/data/file.txt", "../file.txt", "data/../file.txt", "data/nested/../../file.txt",
    "data/./file.txt", "data//file.txt", "data/", "data\\file.txt",
    "other/file.txt", "data/line\nbreak.txt", "data/\x00file.txt",
])
def test_unsafe_or_unknown_paths_are_rejected(path):
    release = copy.deepcopy(EXAMPLE)
    release["files"][0]["path"] = path
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(SCHEMA).validate(release)


def test_multimodal_example_matches_contract():
    jsonschema.Draft202012Validator(SCHEMA).validate(EXAMPLE)
    assert set(EXAMPLE["modalities"]) == {"text", "tabular"}
