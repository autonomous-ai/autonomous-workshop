#!/usr/bin/env python3
"""Loop D CLI — drive and inspect the great-books study by hand.

The meta-loop normally drives Loop D via books.study_tick; this tool is the
human/ops face for the same state. Deterministic; the *reading* is still done
by the book-reading agent and recorded through `add-learning`/`add-principle`.

Examples:
  python3 tools/books.py list
  python3 tools/books.py tick                # start the next unread book
  python3 tools/books.py status              # what is being read now
  python3 tools/books.py add-learning "..." --book TITLE --target-area rules
  python3 tools/books.py add-principle "The printed game is the product."
  python3 tools/books.py done "Title..."     # finish a book (after learnings)
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from eve import books, config  # noqa: E402


def _cfg():
    return config.Config.load()


def cmd_list(cfg):
    prog = books.progress(cfg)
    print(f"books: {prog['books']}  (total {prog['total']})")
    print(f"learnings: {prog['learnings']}  principles: {prog['principles']}")
    for b in books.reading_list(cfg):
        mark = {"unread": " ", "in_progress": ">", "done": "x"}[b.get("status", "unread")]
        print(f"[{mark}] {b['title']}  — {b['author']} ({b['category']})")


def cmd_status(cfg):
    prog = books.progress(cfg)
    cur = next((b for b in books.reading_list(cfg)
                if b.get("status") == "in_progress"), None)
    nxt = books.next_up(cfg)
    print("currently reading:", cur["title"] if cur else "(none)")
    print("next up:", nxt["title"] if nxt else "(shelf exhausted)")
    print(f"progress: {prog['books']}")
    rep = books.graduation_repeats(cfg)
    if rep:
        print(f"repeated learnings to graduate: {len(rep)}")


def cmd_tick(cfg):
    book = books.study_tick(cfg)
    if book is None:
        print("no book left to study; replenish the shelf")
        return
    print(f"studying: {book['title']}")


def cmd_add_learning(cfg, text, book, target_area, mechanic, theme):
    lid = books.record_learning(
        cfg, book=book, learning=text, target_area=target_area or "design",
        mechanic=mechanic, theme=theme)
    print(f"recorded learning {lid}")


def cmd_add_principle(cfg, text):
    books.add_principle(cfg, text=text, source="cli")
    print("recorded principle")


def cmd_done(cfg, title):
    if books.mark_done(cfg, title):
        print(f"finished: {title}")
    else:
        print(f"no such book: {title}")
        sys.exit(1)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    cmd = argv[0] if argv else "list"
    cfg = _cfg()
    if cmd == "list":
        cmd_list(cfg)
    elif cmd == "status":
        cmd_status(cfg)
    elif cmd == "tick":
        cmd_tick(cfg)
    elif cmd == "add-learning":
        rest = argv[1:]
        text = rest[0] if rest else None
        if not text:
            print("usage: add-learning TEXT [--book T] [--target-area A] "
                  "[--mechanic M] [--theme T]")
            sys.exit(2)
        kw = dict(zip(rest[1::2], rest[2::2])) if len(rest) > 1 else {}
        cmd_add_learning(cfg, text, kw.get("--book", "unknown"),
                         kw.get("--target-area"), kw.get("--mechanic"),
                         kw.get("--theme"))
    elif cmd == "add-principle":
        text = argv[1] if len(argv) > 1 else None
        if not text:
            print("usage: add-principle TEXT")
            sys.exit(2)
        cmd_add_principle(cfg, text)
    elif cmd == "done":
        title = " ".join(argv[1:]) if len(argv) > 1 else None
        if not title:
            print("usage: done TITLE")
            sys.exit(2)
        cmd_done(cfg, title)
    else:
        print(f"unknown command: {cmd}")
        sys.exit(2)


if __name__ == "__main__":
    main()
