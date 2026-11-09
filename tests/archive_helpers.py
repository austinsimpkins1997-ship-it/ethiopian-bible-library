"""Memory-light access to the metadata-only archive embedded in the site."""

import json
import re
from pathlib import Path


def read_embedded_archive(root: Path) -> dict:
    html = (Path(root) / "index.html").read_text(encoding="utf-8")
    match = re.search(
        r'<script id="archive-data" type="application/json">(.*?)</script>',
        html,
        flags=re.DOTALL,
    )
    if not match:
        raise ValueError("index.html does not contain its embedded archive metadata")
    return json.loads(match.group(1))
