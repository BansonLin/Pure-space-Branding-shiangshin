#!/usr/bin/env python3
"""Flatten every TEXT / MTEXT / ATTRIB / ATTDEF from the DWG JSON dump.

usage: python3 scripts/extract_texts.py db.json texts.json
Output rows: owner (block name or *MODEL), type, layer, x, y, h (text height), text, tag.
ATTRIB values arrive nested as {"text": {...}} in the dump and are unwrapped here.
"""
import json
import sys


def main(src: str, dst: str) -> None:
    db = json.load(open(src, encoding="utf-8"))
    out = []

    def walk(ents, owner):
        for e in ents:
            if e["type"] not in ("TEXT", "MTEXT", "ATTRIB", "ATTDEF"):
                continue
            txt = e.get("text") or e.get("contents") or e.get("defaultValue") or ""
            p = e.get("startPoint") or e.get("insertionPoint") or {}
            h = e.get("textHeight") or e.get("height")
            if isinstance(txt, dict):
                p = txt.get("startPoint") or {}
                h = txt.get("textHeight")
                txt = txt.get("text", "")
            out.append(dict(owner=owner, type=e["type"], layer=e.get("layer"), x=p.get("x"), y=p.get("y"),
                            h=h, text=txt, tag=e.get("tag")))

    walk(db["entities"], "*MODEL")
    for b in db["tables"]["BLOCK_RECORD"]["entries"]:
        if b["name"] != "*Model_Space":
            walk(b.get("entities") or [], b["name"])
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False)
    print(len(out), "texts")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
