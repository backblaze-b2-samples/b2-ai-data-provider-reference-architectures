#!/usr/bin/env python3
"""Fail when a local Markdown link points to a missing repository path."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def main() -> int:
    files = sorted(ROOT.rglob("*.md")) + [ROOT / "llms.txt"]
    failures: list[str] = []
    checked = 0
    for path in files:
        if any(part in {".venv", ".pytest_cache"} for part in path.parts):
            continue
        for match in LINK.finditer(path.read_text()):
            raw = match.group(1).strip()
            if raw.startswith("<") and raw.endswith(">"):
                raw = raw[1:-1]
            target = raw.split(maxsplit=1)[0]
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
    if failures:
        print("\n".join(failures))
        return 1
    print(f"{checked} local Markdown links resolve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
