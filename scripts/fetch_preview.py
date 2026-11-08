#!/usr/bin/env python3
"""
Fill the end card's pointer from an article URL (SKILL.md, "End card").

  python3 scripts/fetch_preview.py <article url> [--photo-out FILE]

Reads the page's own metadata (Open Graph and Twitter tags, JSON-LD, the
<title>), downloads its share image, and prints the "pointer" block to paste
into the manifest: {"outlet", "title", "url", "date", "photo"}. Notes go to
stderr: every field it couldn't find, and a reminder to check the title
against the page's headline word for word.

No live browser is needed, only a page fetch. A site that blocks the fetch
(paywall, bot wall) exits 1: fill the pointer by hand from the page text.
Exit 0 when a title was found. Standard library only (plus Pillow, which
the build already needs, to check the downloaded image).
"""

import argparse
import datetime
import html as htmllib
import json
import os
import re
import sys
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

USER_AGENT = "Mozilla/5.0 (compatible; reel-preview-fetch)"
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
IMAGE_EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


class _PageMeta(HTMLParser):
    """Collects <meta property|name content>, the <title> text, JSON-LD
    script bodies and the first <time datetime>."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta, self.title, self.jsonld, self.time = {}, None, [], None
        self._buf, self._in = [], None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "meta":
            key = (a.get("property") or a.get("name") or "").lower()
            if key and a.get("content") and key not in self.meta:
                self.meta[key] = a["content"].strip()
        elif tag == "title" and self.title is None:
            self._in, self._buf = "title", []
        elif tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self._in, self._buf = "jsonld", []
        elif tag == "time" and self.time is None and a.get("datetime"):
            self.time = a["datetime"].strip()

    def handle_endtag(self, tag):
        if self._in == "title" and tag == "title":
            self.title = " ".join("".join(self._buf).split())
            self._in = None
        elif self._in == "jsonld" and tag == "script":
            self.jsonld.append("".join(self._buf))
            self._in = None

    def handle_data(self, data):
        if self._in:
            self._buf.append(data)


def _ld_article(blobs):
    """The first JSON-LD item whose @type names an article or a posting."""
    for raw in blobs:
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        items = []
        for d in (data if isinstance(data, list) else [data]):
            if isinstance(d, dict) and isinstance(d.get("@graph"), list):
                items += d["@graph"]
            else:
                items.append(d)
        for it in items:
            if not isinstance(it, dict):
                continue
            t = it.get("@type")
            if any(isinstance(x, str) and ("Article" in x or "Posting" in x)
                   for x in (t if isinstance(t, list) else [t])):
                return it
    return {}


def _ld_text(v):
    return htmllib.unescape(v).strip() if isinstance(v, str) and v.strip() else None


def _ld_image(v):
    if isinstance(v, list):
        v = v[0] if v else None
    if isinstance(v, dict):
        v = v.get("url")
    return v if isinstance(v, str) and v.strip() else None


def _ld_publisher(v):
    if isinstance(v, list):
        v = v[0] if v else None
    return _ld_text(v.get("name")) if isinstance(v, dict) else None


def strip_site_suffix(title, site):
    """title without one trailing " | Site", " - Site" or " — Site" segment,
    and only when that segment is the site's name (any case)."""
    if not site:
        return title
    for sep in (" | ", " - ", " — ", " – "):
        head, found, tail = title.rpartition(sep)
        if found and head and tail.strip().lower() == site.strip().lower():
            return head.strip()
    return title


def parse_preview(html, url):
    """The preview fields a page states about itself: {"outlet", "title",
    "date_iso", "photo_url"}, each a string or None."""
    p = _PageMeta()
    p.feed(html)
    p.close()
    m, ld = p.meta, _ld_article(p.jsonld)
    outlet = m.get("og:site_name") or _ld_publisher(ld.get("publisher"))
    title = (m.get("og:title") or m.get("twitter:title") or _ld_text(ld.get("headline"))
             or p.title or None)
    if title:
        host = (urlparse(url).hostname or "").removeprefix("www.")
        title = strip_site_suffix(strip_site_suffix(title, outlet), host.split(".")[0])
    date_iso = m.get("article:published_time") or _ld_text(ld.get("datePublished")) or p.time
    photo = (m.get("og:image:secure_url") or m.get("og:image") or m.get("twitter:image")
             or _ld_image(ld.get("image")))
    return {"outlet": outlet or None, "title": title or None, "date_iso": date_iso or None,
            "photo_url": urljoin(url, photo) if photo else None}


def _card_date(d):
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def iso_to_card_date(value):
    """"29 Oct 2026" from an ISO date or date-time, using the date as written
    (the publisher's own day; no time-zone conversion). None if not ISO."""
    mt = re.match(r"^\s*(\d{4})-(\d{2})-(\d{2})", value or "")
    if not mt:
        return None
    try:
        return _card_date(datetime.date(*map(int, mt.groups())))
    except ValueError:
        return None


def pointer_block(found, url, today, photo_path):
    """(the manifest's pointer block, notes) from parse_preview's fields.
    No publish date gives "Accessed <today>"; "photo" only when downloaded."""
    notes = []
    date = iso_to_card_date(found.get("date_iso") or "")
    if not date:
        date = f"Accessed {_card_date(today)}"
        notes.append(f"no publish date on the page: 'date' set to {date!r}; use the page's "
                     "own date if it shows one.")
    if not found.get("outlet"):
        notes.append("no outlet name found: fill 'outlet' with the outlet's usual short name.")
    if not found.get("title"):
        notes.append("no title found: fill 'title' with the page's headline, word for word.")
    else:
        notes.append("check 'title' against the page's headline: it must match word for word.")
    block = {"outlet": found.get("outlet") or "", "title": found.get("title") or "",
             "url": url, "date": date}
    if photo_path:
        block["photo"] = photo_path
    else:
        notes.append("no photo: the card draws the outlet tile. Add 'photo' only with the "
                     "article's own image, never the false material the reel debunks.")
    return block, notes


def _get(url, accept):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read(), r.headers.get_content_type(), r.headers.get_content_charset()


def _download_photo(photo_url, out):
    """The saved photo's path, or (None, why)."""
    try:
        data, ctype, _ = _get(photo_url, "image/jpeg,image/png;q=0.9,*/*;q=0.5")
    except Exception as e:
        return None, f"could not download the share image {photo_url} ({e})"
    path = out or f"pointer_photo{IMAGE_EXT.get(ctype, '.jpg')}"
    with open(path, "wb") as f:
        f.write(data)
    from reel_manifest import POINTER_PHOTO_MIN, image_problem
    problem = image_problem(path)
    if not problem:
        from PIL import Image
        with Image.open(path) as im:
            if min(im.size) < POINTER_PHOTO_MIN:
                problem = f"is only {im.size[0]}x{im.size[1]}px, too small to be the article's photo"
    if problem:
        os.remove(path)
        return None, f"share image {photo_url} {problem}"
    return path, None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Print the end card's pointer block for an article URL.")
    ap.add_argument("url", help="the article's full http(s) address")
    ap.add_argument("--photo-out", help="where to save the share image "
                    "(default: pointer_photo.<ext> in the current folder)")
    args = ap.parse_args(argv)
    try:
        body, _, charset = _get(args.url, "text/html,application/xhtml+xml")
    except Exception as e:
        print(f"could not fetch {args.url} ({e}); fill the pointer by hand from the page text: "
              "outlet, title (word for word), url, date", file=sys.stderr)
        return 1
    found = parse_preview(body.decode(charset or "utf-8", errors="replace"), args.url)
    photo_path, why = (_download_photo(found["photo_url"], args.photo_out)
                       if found["photo_url"] else (None, None))
    block, notes = pointer_block(found, args.url, datetime.date.today(), photo_path)
    if why:
        notes.insert(0, why)
    print(json.dumps(block, ensure_ascii=False, indent=2))
    for n in notes:
        print(f"note: {n}", file=sys.stderr)
    return 0 if found["title"] else 1


if __name__ == "__main__":
    sys.exit(main())
