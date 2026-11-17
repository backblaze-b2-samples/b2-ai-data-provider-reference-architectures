#!/usr/bin/env python3
"""Fail when a local Markdown link points to a missing repository path.

With --external, also probe http(s) links. Vendor docs sites often rate-limit or block
bots, so only definitive breakage (404, 410, DNS failure) fails; everything else warns.
Known reference repositories warn on 404 only while their repository root is also unavailable.
"""
from __future__ import annotations

import argparse
import re
import socket
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SKIP_PARTS = {".venv", ".pytest_cache"}
BROKEN_STATUSES = {404, 410}
TIMEOUT_SECONDS = 10
USER_AGENT = "b2-category-link-check/1.0"
# Only these repositories may be awaiting publication. A missing file in a public
# repository still fails, and similarly named repositories get no exception.
REFERENCE_REPOSITORIES = {
    "b2-ai-data-provider-reference-architectures",
    "b2-autonomous-vehicle-reference-architectures",
    "b2-commercial-drone-reference-architectures",
    "b2-gen-video-reference-architectures",
    "b2-image-generation-reference-architectures",
    "b2-robotics-reference-architectures",
}


def reference_repository_url(url: str) -> str | None:
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if (parsed.hostname == "github.com" and len(parts) >= 2
            and parts[0] == "backblaze-b2-samples" and parts[1] in REFERENCE_REPOSITORIES):
        return f"https://github.com/{parts[0]}/{parts[1]}"
    return None


def markdown_files() -> list[Path]:
    files = sorted(ROOT.rglob("*.md")) + [ROOT / "llms.txt", ROOT / "llms-full.txt"]
    return [path for path in files if path.exists() and not SKIP_PARTS.intersection(path.parts)]


def link_targets(path: Path) -> Iterable[str]:
    for match in LINK.finditer(path.read_text()):
        raw = match.group(1).strip()
        if raw.startswith("<") and raw.endswith(">"):
            raw = raw[1:-1]
        yield raw.split(maxsplit=1)[0]


def check_local(files: list[Path]) -> tuple[int, list[str]]:
    failures: list[str] = []
    checked = 0
    for path in files:
        for target in link_targets(path):
            parsed = urlparse(target)
            if parsed.scheme or parsed.netloc or target.startswith("#"):
                continue
            local = (path.parent / unquote(parsed.path)).resolve()
            checked += 1
            try:
                local.relative_to(ROOT)
            except ValueError:
                failures.append(f"{path.relative_to(ROOT)}: link escapes repository: {target}")
                continue
            if not local.exists():
                failures.append(f"{path.relative_to(ROOT)}: missing {target}")
    return checked, failures


def external_urls(files: Iterable[Path]) -> list[str]:
    return sorted({target for path in files for target in link_targets(path) if urlparse(target).scheme in {"http", "https"}})


def fetch_status(url: str) -> int:
    """Return the final HTTP status, retrying with GET when a server rejects HEAD."""
    status = 0
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                return response.status
        except urllib.error.HTTPError as error:
            status = error.code
    return status


def check_url(url: str, fetch: Callable[[str], int] = fetch_status) -> tuple[str, str]:
    """Classify a URL as ok, warn, or fail."""
    try:
        status = fetch(url)
    except urllib.error.URLError as error:
        if isinstance(error.reason, socket.gaierror):
            return "fail", f"DNS lookup failed: {error.reason}"
        return "warn", f"unreachable: {error.reason}"
    except (TimeoutError, OSError) as error:
        return "warn", f"unreachable: {error!r}"
    if status in BROKEN_STATUSES:
        repository = reference_repository_url(url)
        if status == 404 and repository:
            try:
                root_status = fetch(repository)
            except (urllib.error.URLError, TimeoutError, OSError):
                return "fail", "HTTP 404 (repository visibility could not be confirmed)"
            if root_status == 404:
                return "warn", "HTTP 404 (unpublished or private reference repository)"
        return "fail", f"HTTP {status}"
    if status >= 400:
        return "warn", f"HTTP {status}"
    return "ok", f"HTTP {status}"


def check_external(files: list[Path]) -> list[str]:
    urls = external_urls(files)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(check_url, urls))
    failures: list[str] = []
    for url, (outcome, detail) in zip(urls, results):
        if outcome == "fail":
            failures.append(f"broken: {url} ({detail})")
        elif outcome == "warn":
            print(f"warning: {url} ({detail})")
    print(f"{len(urls)} external links checked")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--external", action="store_true", help="also probe http(s) links over the network")
    args = parser.parse_args()
    files = markdown_files()
    checked, failures = check_local(files)
    print(f"{checked} local Markdown links checked")
    if args.external:
        failures += check_external(files)
    if failures:
        print("\n".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
