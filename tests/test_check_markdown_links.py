"""External link classification tests; network access is injected, never real."""
from __future__ import annotations

import socket
import urllib.error

import pytest

import check_markdown_links as links


def fetch_returning(status: int):
    return lambda url: status


def fetch_raising(error: Exception):
    def fetch(url: str) -> int:
        raise error
    return fetch


@pytest.mark.parametrize("status, expected", [
    (200, "ok"), (301, "ok"),
    (404, "fail"), (410, "fail"),
    (403, "warn"), (429, "warn"), (503, "warn"),
])
def test_classifies_http_status(status, expected):
    assert links.check_url("https://example.com", fetch_returning(status))[0] == expected


def test_dns_failure_fails():
    error = urllib.error.URLError(socket.gaierror(8, "nodename nor servname provided"))
    assert links.check_url("https://gone.invalid", fetch_raising(error))[0] == "fail"


def test_timeout_warns():
    assert links.check_url("https://slow.example", fetch_raising(TimeoutError()))[0] == "warn"


def test_external_urls_skip_local_and_anchor_links(tmp_path):
    page = tmp_path / "page.md"
    page.write_text("[a](https://a.example/x) [b](local.md) [c](#top) [d](https://a.example/x) [e](http://b.example)")
    assert links.external_urls([page]) == ["http://b.example", "https://a.example/x"]


@pytest.mark.parametrize("url", [
    "https://github.com/backblaze-b2-samples/b2-robotics-reference-architectures",
    "https://github.com/backblaze-b2-samples/b2-ai-data-provider-reference-architectures/blob/main/README.md",
])
def test_unpublished_category_repo_404_warns(url):
    outcome, detail = links.check_url(url, fetch_returning(404))
    assert outcome == "warn"
    assert "unpublished" in detail


@pytest.mark.parametrize("url", [
    "https://github.com/backblaze-b2-samples/b2-event-broker",
    "https://github.com/backblaze-b2-samples/sam2-mask-dataset-builder",
    "https://github.com/other-org/b2-robotics-reference-architectures",
])
def test_other_404_still_fails(url):
    assert links.check_url(url, fetch_returning(404))[0] == "fail"


def test_missing_file_in_public_reference_repository_fails():
    repository = "https://github.com/backblaze-b2-samples/b2-ai-data-provider-reference-architectures"
    def fetch(url):
        return 200 if url == repository else 404
    assert links.check_url(repository + "/blob/main/missing.md", fetch)[0] == "fail"


def test_reference_repository_typo_fails():
    url = "https://github.com/backblaze-b2-samples/b2-robotic-reference-architectures"
    assert links.check_url(url, fetch_returning(404))[0] == "fail"


def test_gone_reference_repository_fails():
    url = "https://github.com/backblaze-b2-samples/b2-robotics-reference-architectures"
    assert links.check_url(url, fetch_returning(410))[0] == "fail"


def test_missing_file_with_unknown_repository_visibility_fails():
    repository = "https://github.com/backblaze-b2-samples/b2-robotics-reference-architectures"
    def fetch(url):
        if url == repository:
            raise TimeoutError()
        return 404
    assert links.check_url(repository + "/blob/main/missing.md", fetch)[0] == "fail"
