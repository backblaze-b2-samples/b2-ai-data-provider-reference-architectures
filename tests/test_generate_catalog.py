"""Catalog validation and generated-output tests."""
from __future__ import annotations

import copy
import json
import re

import pytest

import generate_catalog as gc


@pytest.fixture(scope="module")
def catalog() -> dict:
    return gc.load_catalog()


def test_generated_outputs_are_current(catalog):
    for path, content in gc.expected_outputs(catalog).items():
        assert path.read_text() == content, f"{path.relative_to(gc.ROOT)} is stale; run tools/generate_catalog.py"


def test_rejects_unknown_connection_type(catalog):
    bad = copy.deepcopy(catalog)
    bad["architectures"][0]["integrations"][0]["connection_type"] = "native"
    with pytest.raises(ValueError, match="connection_type"):
        gc.validate_catalog(bad)


def test_rejects_unknown_sample_architecture(catalog):
    bad = copy.deepcopy(catalog)
    bad["samples"][0]["architectures"] = ["no-such-architecture"]
    with pytest.raises(ValueError, match="no-such-architecture"):
        gc.validate_catalog(bad)


def test_rejects_duplicate_sample_id(catalog):
    bad = copy.deepcopy(catalog)
    bad["samples"].append(copy.deepcopy(bad["samples"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        gc.validate_catalog(bad)


def test_label_maps_match_schema_enums():
    schema = json.loads(gc.SCHEMA_PATH.read_text())
    defs = schema["$defs"]
    assert set(gc.CONNECTION_LABELS) == set(defs["integration"]["properties"]["connection_type"]["enum"])
    assert set(gc.SAMPLE_GROUPS) == set(defs["sample"]["properties"]["group"]["enum"])


def test_every_sample_is_rendered(catalog):
    related = gc.render_related_samples(catalog)
    llms = gc.render_llms(catalog)
    for sample in catalog["samples"]:
        assert sample["url"] in related
        assert sample["url"] in llms


def test_llms_full_links_are_root_relative_and_resolve(catalog):
    text = gc.render_llms_full(catalog)
    for architecture in catalog["architectures"]:
        assert f"<!-- source: {architecture['links']['architecture']} -->" in text
    targets = [match.group(1) for match in re.finditer(r"\]\(([^)\s]+)\)", text)]
    local = [t for t in targets if not t.startswith(("http://", "https://", "#", "mailto:"))]
    assert local, "expected local links in llms-full.txt"
    for target in local:
        assert not target.startswith(".."), target
        assert (gc.ROOT / target.split("#", 1)[0]).exists(), target


def test_rewrite_links_resolves_against_source_directory():
    text = "[a](../x/y.md#z) [b](https://e.com) [c](#anchor) [d](same.md)"
    out = gc.rewrite_links(text, gc.ROOT / "docs" / "page.md")
    assert out == "[a](x/y.md#z) [b](https://e.com) [c](#anchor) [d](docs/same.md)"


# Connection labels shared by every B2 category repo; each repo's enum is the subset its catalog uses.
FROZEN_CONNECTION_LABELS = {
    "s3-custom-endpoint": "S3 custom endpoint",
    "native-b2-option": "Built-in Backblaze B2 option",
    "fsspec-s3": "fsspec / s3fs",
    "presigned-url": "Presigned URLs",
    "s3-sync-cli": "S3 sync tool",
    "cdn-origin": "CDN origin",
    "b2-sample-app": "Backblaze B2 sample app",
}
CATEGORY_SLUGS = {
    "b2-ai-data-provider-reference-architectures",
    "b2-gen-video-reference-architectures",
    "b2-image-generation-reference-architectures",
    "b2-robotics-reference-architectures",
    "b2-autonomous-vehicle-reference-architectures",
    "b2-commercial-drone-reference-architectures",
}
ORG_URL = "https://github.com/backblaze-b2-samples/"
BANNED_PHRASES = (
    "documentation-reviewed", "source-reviewed", "evidence reviewed", "evidence status",
    "evidence basis", "not verified", "unverified", "not evidence",
)


def this_repo_slug() -> str:
    # The skill name is the repo slug minus its suffix, so this works under any checkout directory name.
    name = re.search(r"^name:\s*(\S+)", (gc.ROOT / "skill" / "SKILL.md").read_text(), re.MULTILINE).group(1)
    return f"{name}-reference-architectures"


def test_schema_drops_evidence_fields_and_is_version_2():
    schema = json.loads(gc.SCHEMA_PATH.read_text())
    defs = schema["$defs"]
    assert schema["properties"]["schema_version"] == {"const": "2.0.0"}
    assert schema["$id"].endswith(":2")
    assert "validation" not in defs["architecture"]["properties"]
    assert "validation" not in defs["architecture"]["required"]
    assert not {"evidence", "evidence_url"} & set(defs["integration"]["properties"])
    assert defs["integration"]["properties"]["setup_url"] == {"type": "string", "format": "uri"}
    assert "setup_url" not in defs["integration"]["required"]


def test_rejects_architecture_validation_block(catalog):
    bad = copy.deepcopy(catalog)
    bad["architectures"][0]["validation"] = {"status": "source-reviewed"}
    with pytest.raises(ValueError, match="validation"):
        gc.validate_catalog(bad)


def test_generated_outputs_contain_no_evidence_status_language(catalog):
    for path, content in gc.expected_outputs(catalog).items():
        lowered = content.lower()
        for phrase in BANNED_PHRASES:
            assert phrase not in lowered, f"{path.relative_to(gc.ROOT)} contains {phrase!r}"


def test_connection_labels_match_frozen_labels_schema_and_catalog(catalog):
    schema = json.loads(gc.SCHEMA_PATH.read_text())
    enum = set(schema["$defs"]["integration"]["properties"]["connection_type"]["enum"])
    used = {item["connection_type"] for architecture in catalog["architectures"] for item in architecture["integrations"]}
    assert set(gc.CONNECTION_LABELS) == enum == used
    assert gc.CONNECTION_LABELS == {key: FROZEN_CONNECTION_LABELS[key] for key in gc.CONNECTION_LABELS}


def test_related_categories_list_the_five_sibling_repos(catalog):
    slug = this_repo_slug()
    assert slug in CATEGORY_SLUGS
    urls = [item["url"] for item in catalog["related_categories"]]
    assert sorted(urls) == sorted(ORG_URL + other for other in CATEGORY_SLUGS - {slug})


def test_sibling_categories_are_rendered(catalog):
    llms = gc.render_llms(catalog)
    readme = gc.render_readme(catalog)
    section = llms.split("## Other B2 reference architecture categories", 1)[1].split("\n## ", 1)[0]
    entries = [line for line in section.splitlines() if line.startswith("- ")]
    assert len(entries) == 5
    for item in catalog["related_categories"]:
        assert item["url"] in section
        assert item["url"] in readme


def test_setup_url_renders_as_setup_guide_link(catalog):
    with_setup = copy.deepcopy(catalog)
    integration = with_setup["architectures"][0]["integrations"][0]
    integration["setup_url"] = "https://example.com/setup"
    gc.validate_catalog(with_setup)
    link = "[setup guide](https://example.com/setup)"
    assert link in gc.render_readme_integrations(with_setup)
    assert link in gc.render_llms(with_setup)
    assert link in gc.render_skill_index(with_setup)


def test_titles_use_the_shared_framing(catalog):
    # llms.txt H1, codemeta name and CITATION title must all read "B2 Reference Architectures for <Category>".
    title = json.loads((gc.ROOT / "codemeta.json").read_text())["name"]
    assert title.startswith("B2 Reference Architectures for ")
    assert f'title: "{title}"' in (gc.ROOT / "CITATION.cff").read_text()
    assert gc.render_llms(catalog).startswith(f"# {title}\n")
    assert gc.render_llms_full(catalog).startswith(f"# {title}: full text\n")
    assert gc.render_readme(catalog).startswith("# B2 reference architectures for ")
