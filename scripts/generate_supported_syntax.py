#!/usr/bin/env python3
"""Refresh the generated block in docs/supported_syntax.md.

Run after changing a feature rule or a profile. A test compares the checked-in
document against this output, so forgetting is a build failure rather than a
document that quietly stops being true.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from multigen.frontend.syntax_reference import render_document  # noqa: E402

DOC_PATH = REPO_ROOT / "docs" / "supported_syntax.md"


def main() -> int:
    """Rewrite the document, reporting whether anything changed."""
    existing = DOC_PATH.read_text(encoding="utf-8")
    updated = render_document(existing)
    if existing == updated:
        sys.stdout.write(f"{DOC_PATH.relative_to(REPO_ROOT)} is up to date\n")
        return 0
    DOC_PATH.write_text(updated, encoding="utf-8")
    sys.stdout.write(f"{DOC_PATH.relative_to(REPO_ROOT)} regenerated\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
