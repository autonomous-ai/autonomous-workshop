"""Write a self-contained copy of a concepts page: every relative image becomes an inline WebP.

usage: embed_page.py <CONCEPTS.html> <out.html> [--max-side 900] [--quality 80]
"""

import argparse
import base64
import io
import re
from pathlib import Path

from PIL import Image


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("page", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--max-side", type=int, default=900)
    ap.add_argument("--quality", type=int, default=80)
    args = ap.parse_args()

    base = args.page.parent
    html = args.page.read_text()

    def inline(match: re.Match) -> str:
        image = Image.open(base / match.group(1)).convert("RGB")
        image.thumbnail((args.max_side, args.max_side))
        buf = io.BytesIO()
        image.save(buf, "WEBP", quality=args.quality)
        return 'src="data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode() + '"'

    html, count = re.subn(r'src="(?!data:|https?:|/)([^"]+\.(?:png|jpe?g|webp))"', inline, html)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html)
    print(f"{args.out}: {count} images, {args.out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
