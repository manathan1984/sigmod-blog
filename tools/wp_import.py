#!/usr/bin/env python3
"""Import posts and pages from the legacy WordPress blog (wp.sigmod.org).

Uses the public WordPress REST API, so no WordPress credentials are needed.
Re-running is safe: files are rewritten in place, keyed by WordPress ID.

Examples:
    python3 tools/wp_import.py --latest 1        # newest post only
    python3 tools/wp_import.py --post 3855       # specific post(s) by ID
    python3 tools/wp_import.py --page 2 3873     # specific page(s) by ID
    python3 tools/wp_import.py --all             # every published post

What it writes:
    _posts/YYYY-MM-DD-<slug>.html   post body (raw WordPress HTML) + front matter
    _pages/<slug>.html              imported WordPress pages
    _data/authors.yml               author name / url / avatar, keyed by slug
    _data/categories.yml            every WordPress category (for legacy ?cat= links)
    category/<slug>.html            one listing page per category in use
    author/<slug>.html              one listing page per author in use
    wp-content/uploads/...          images, mirrored at their original paths
"""

import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

SITE = "https://wp.sigmod.org"
API = SITE + "/index.php?rest_route="
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "sigmod-blog-importer/1.0 (+https://github.com/manathan1984/sigmod-blog)"

UPLOAD_RE = re.compile(r"https?://wp\.sigmod\.org(/wp-content/uploads/[^\s\"'<>)]+)")
INTERNAL_RE = re.compile(r"https?://wp\.sigmod\.org/?\?(p|page_id)=(\d+)[^\s\"'<>]*")
ATTACHMENT_RE = re.compile(r"https?://wp\.sigmod\.org/?\?attachment_id=(\d+)")
CAT_RE = re.compile(r"https?://wp\.sigmod\.org/?\?cat=(\d+)")
# Images pasted from Google Docs are served from expiring googleusercontent URLs.
EXTERNAL_IMG_RE = re.compile(r"(<img[^>]+src=\")(https://lh\d(?:-[a-z]+)?\.googleusercontent\.com/[^\"]+)\"")

# Filled in by main(): WordPress category id -> {"name", "slug"}.
CATEGORIES = {}


# --------------------------------------------------------------------------- HTTP

def fetch(route, params=None):
    """GET a REST route; returns (json, headers)."""
    url = API + route
    if params:
        url += "&" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r), r.headers
        except Exception as e:  # noqa: BLE001 - retry on any network error
            if attempt == 3:
                raise
            print(f"  retry {route}: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))


def download(path):
    """Mirror /wp-content/uploads/... into the repo at the same path."""
    path = urllib.parse.unquote(path.split("?")[0].split("#")[0])
    dest = os.path.join(ROOT, path.lstrip("/"))
    if os.path.exists(dest):
        return True
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    url = SITE + urllib.parse.quote(path)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
            f.write(r.read())
        print(f"  image {path}")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"  ! could not download {url}: {e}", file=sys.stderr)
        return False


def mirror_external(url):
    """Save an externally hosted image under /wp-content/uploads/external/; returns its path."""
    url = html.unescape(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data, ctype = r.read(), r.headers.get("Content-Type", "")
    except Exception as e:  # noqa: BLE001
        print(f"  ! could not download {url[:80]}: {e}", file=sys.stderr)
        return None
    ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif", "image/webp": ".webp"}.get(ctype.split(";")[0], ".img")
    path = f"/wp-content/uploads/external/{hashlib.sha1(url.encode()).hexdigest()[:16]}{ext}"
    dest = os.path.join(ROOT, path.lstrip("/"))
    if not os.path.exists(dest):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(data)
        print(f"  image {url[:60]}… -> {path}")
    return path


def attachment_path(media_id):
    """Resolve ?attachment_id=N to the uploaded file's path."""
    try:
        media, _ = fetch(f"/wp/v2/media/{media_id}", {"_fields": "source_url"})
    except Exception:  # noqa: BLE001
        return None
    m = UPLOAD_RE.match(media.get("source_url", ""))
    return m.group(1) if m and download(m.group(1)) else None


def unwrap_layout_tables(content):
    """Old posts wrap the whole text in a one-column <table> for layout; keep only the cell contents."""
    def unwrap(m):
        t = m.group(0)
        rows = len(re.findall(r"<tr\b", t))
        cells = re.findall(r"<td\b[^>]*>(.*?)</td>", t, re.S)
        if "<th" in t or not cells or len(cells) != rows or "<table" in t[6:]:
            return t
        return "\n".join(c.strip() for c in cells)

    return re.sub(r"<table\b.*?</table>", unwrap, content, flags=re.S)


def balance_divs(content):
    """WordPress tolerates unclosed <div>s; here they would swallow the sidebar."""
    opens, closes = len(re.findall(r"<div\b", content)), len(re.findall(r"</div>", content))
    if opens > closes:
        content += "\n" + "</div>" * (opens - closes)
    for _ in range(closes - opens):
        i = content.rfind("</div>")
        content = content[:i] + content[i + len("</div>"):]
    return content


# --------------------------------------------------------------------------- YAML

def yq(s):
    """Quote a scalar for YAML front matter."""
    return json.dumps("" if s is None else str(s), ensure_ascii=False)


def load_yaml_map(path):
    """Tiny reader for the flat `key:\n  field: "value"` files this script writes."""
    out, cur = {}, None
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        if not line.startswith(" "):
            cur = json.loads(line.rstrip()[:-1]) if line.startswith('"') else line.rstrip()[:-1]
            out[cur] = {}
        else:
            k, v = line.strip().split(":", 1)
            v = v.strip()
            out[cur][k] = json.loads(v) if v.startswith(("\"", "[")) or v.isdigit() else v
    return out


def dump_yaml_map(path, data, header):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        for key in sorted(data):
            f.write(f"{yq(key)}:\n")
            for k, v in data[key].items():
                f.write(f"  {k}: {v if isinstance(v, int) else yq(v)}\n")


# --------------------------------------------------------------------------- content

def clean_html(content, depth, id_map):
    """Make WordPress HTML portable.

    depth: how many directories deep the output page lives, so that image
    paths can be written relative (works under any baseurl).
    """
    up = "../" * depth
    # Gutenberg block comments carry no rendering information.
    content = re.sub(r"<!--\s*/?wp:.*?-->", "", content, flags=re.S)
    # srcset/sizes point at resized variants we don't mirror; src is enough.
    content = re.sub(r'\s(srcset|sizes)="[^"]*"', "", content)

    # Links pasted from Google Docs are wrapped (sometimes twice) in google.com/url?q=… redirects.
    def unwrap_google(m):
        url = html.unescape(m.group(1))
        while url.startswith("https://www.google.com/url?"):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("q")
            if not q:
                break
            url = urllib.parse.unquote(q[0]) if "%3D" in q[0] or "%253D" in q[0] else q[0]
        return 'href="' + html.escape(url, quote=True) + '"'

    content = re.sub(r'href="(https://www\.google\.com/url\?[^"]+)"', unwrap_google, content)

    def upload(m):
        download(m.group(1))
        return up + m.group(1).lstrip("/")

    content = UPLOAD_RE.sub(upload, content)

    # Links to other imported posts become links to their new home.
    def internal(m):
        target = id_map.get(int(m.group(2)))
        return up + target.strip("/") + "/" if target else m.group(0)

    content = INTERNAL_RE.sub(internal, content)

    def attachment(m):
        path = attachment_path(m.group(1))
        return up + path.lstrip("/") if path else m.group(0)

    content = ATTACHMENT_RE.sub(attachment, content)

    def category(m):
        c = CATEGORIES.get(int(m.group(1)))
        if not c:
            return m.group(0)
        write_listing("category", c["slug"], c["name"])
        return f"{up}category/{c['slug']}/"

    content = CAT_RE.sub(category, content)

    def external(m):
        path = mirror_external(m.group(2))
        return f'{m.group(1)}{up}{path.lstrip("/")}"' if path else m.group(0)

    content = EXTERNAL_IMG_RE.sub(external, content)
    # Embeds over http are blocked as mixed content on an https site.
    content = re.sub(r'(<iframe[^>]+src=")http://', r"\1https://", content)
    content = unwrap_layout_tables(content)
    content = balance_divs(content)
    content = re.sub(r"\n{3,}", "\n\n", content).strip()
    # Protect any literal {{ }} / {% %} in the body from Liquid.
    return "{% raw %}\n" + content + "\n{% endraw %}\n"


def first_image(content):
    m = re.search(r'<img[^>]+src="([^"]+)"', content)
    if not m:
        return None
    u = UPLOAD_RE.match(m.group(1))
    return u.group(1) if u else None


def text_excerpt(rendered, limit=300):
    t = html.unescape(re.sub(r"<[^>]+>", "", rendered or "")).strip()
    t = re.sub(r"\s+", " ", t).replace("[…]", "").replace("[...]", "").strip()
    return t if len(t) <= limit else t[:limit].rsplit(" ", 1)[0] + "…"


# --------------------------------------------------------------------------- main

def existing_id_map():
    """wp_id -> permalink path for everything already imported."""
    ids = {}
    for d in ("_posts", "_pages"):
        p = os.path.join(ROOT, d)
        if not os.path.isdir(p):
            continue
        for fn in os.listdir(p):
            head = open(os.path.join(p, fn), encoding="utf-8").read(4000)
            wid = re.search(r"^wp_id:\s*(\d+)", head, re.M)
            link = re.search(r"^permalink:\s*\"?([^\"\n]+)", head, re.M)
            if wid and link:
                ids[int(wid.group(1))] = link.group(1)
    return ids


def clean_slug(slug):
    """WordPress slugs can carry percent-encoded junk (e.g. %ef%bf%bc from pasted titles)."""
    slug = urllib.parse.unquote(slug).lower()
    slug = re.sub(r"[^a-z0-9-]+", "", slug)
    return re.sub(r"-{2,}", "-", slug).strip("-") or "post"


def post_permalink(p):
    d = p["date"][:10].split("-")
    return f"/{d[0]}/{d[1]}/{d[2]}/{clean_slug(p['slug'])}/"


def write_listing(kind, slug, name):
    """category/<slug>.html or author/<slug>.html"""
    path = os.path.join(ROOT, kind, slug + ".html")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"---\nlayout: {kind}\ntitle: {yq(name)}\n{kind}: {yq(slug if kind == 'author' else name)}\n"
                f"permalink: /{kind}/{slug}/\n---\n")


def import_posts(posts, authors, categories, id_map, force=False):
    for p in posts:
        id_map[p["id"]] = post_permalink(p)
    for p in posts:
        title = html.unescape(p["title"]["rendered"])
        link = post_permalink(p)
        fn = os.path.join(ROOT, "_posts", f"{p['date'][:10]}-{clean_slug(p['slug'])[:120]}.html")
        if has_local_edits(fn) and not force:
            print(f"post {p['id']}: {title}  (skipped: keep_local_edits)")
            continue
        print(f"post {p['id']}: {title}  ->  {link}")
        emb = p.get("_embedded", {})
        author = (emb.get("author") or [{}])[0]
        aslug = author.get("slug") or f"user-{p['author']}"
        if aslug not in authors:
            authors[aslug] = {}
        a = authors[aslug]
        a.update({"name": author.get("name", aslug), "wp_id": p["author"], "url": author.get("url", "")})
        avatar = (author.get("avatar_urls") or {}).get("96", "")
        m = UPLOAD_RE.match(avatar)
        if m and download(m.group(1)):
            a["avatar"] = m.group(1)
        write_listing("author", aslug, a["name"])

        cats = [categories[c]["name"] for c in p["categories"] if c in categories]
        for c in p["categories"]:
            if c in categories:
                write_listing("category", categories[c]["slug"], categories[c]["name"])

        image = None
        media = emb.get("wp:featuredmedia") or []
        if media and media[0].get("source_url"):
            m = UPLOAD_RE.match(media[0]["source_url"])
            image = m.group(1) if m else None
        image = image or first_image(p["content"]["rendered"])
        if image:
            download(image)

        body = clean_html(p["content"]["rendered"], 4, id_map)
        fm = [
            "---",
            "layout: post",
            f"title: {yq(title)}",
            f"date: {p['date'].replace('T', ' ')}",
            f"last_modified_at: {p['modified'].replace('T', ' ')}",
            f"author: {yq(aslug)}",
            "categories: [" + ", ".join(yq(c) for c in cats) + "]",
            f"excerpt: {yq(text_excerpt(p['excerpt']['rendered']))}",
            f"image: {yq(image) if image else 'null'}",
            f"wp_id: {p['id']}",
            f"permalink: {yq(link)}",
            "---",
        ]
        os.makedirs(os.path.dirname(fn), exist_ok=True)
        # Drop a stale file if the slug/date changed upstream.
        for old in os.listdir(os.path.dirname(fn)):
            oldp = os.path.join(os.path.dirname(fn), old)
            if oldp != fn and re.search(rf"^wp_id:\s*{p['id']}\s*$", open(oldp, encoding="utf-8").read(4000), re.M):
                os.remove(oldp)
        with open(fn, "w", encoding="utf-8") as f:
            f.write("\n".join(fm) + "\n" + body)


def has_local_edits(fn):
    """Files marked `keep_local_edits: true` were hand-edited after import."""
    return os.path.exists(fn) and re.search(
        r"^keep_local_edits:\s*true\s*$", open(fn, encoding="utf-8").read(4000), re.M)


def import_pages(pages, id_map, force=False):
    for p in pages:
        id_map[p["id"]] = f"/{p['slug']}/"
    for p in pages:
        title = html.unescape(p["title"]["rendered"])
        link = f"/{p['slug']}/"
        fn = os.path.join(ROOT, "_pages", p["slug"] + ".html")
        if has_local_edits(fn) and not force:
            print(f"page {p['id']}: {title}  (skipped: keep_local_edits)")
            continue
        print(f"page {p['id']}: {title}  ->  {link}")
        os.makedirs(os.path.dirname(fn), exist_ok=True)
        with open(fn, "w", encoding="utf-8") as f:
            f.write("\n".join([
                "---", "layout: page", f"title: {yq(title)}", f"wp_id: {p['id']}",
                f"permalink: {yq(link)}", "---", ""]) + clean_html(p["content"]["rendered"], 1, id_map))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--latest", type=int, metavar="N", help="import the N newest posts")
    g.add_argument("--all", action="store_true", help="import every published post")
    g.add_argument("--post", type=int, nargs="+", metavar="ID", help="import posts by WordPress ID")
    ap.add_argument("--page", type=int, nargs="+", metavar="ID", default=[], help="also import pages by ID")
    ap.add_argument("--force", action="store_true", help="overwrite files marked keep_local_edits: true")
    args = ap.parse_args()
    if not (args.latest or args.all or args.post or args.page):
        ap.error("nothing to import")

    # Category table: every category, so legacy ?cat=N links can be resolved.
    categories, page = CATEGORIES, 1
    while True:
        batch, hdr = fetch("/wp/v2/categories", {"per_page": 100, "page": page})
        for c in batch:
            categories[c["id"]] = {"name": html.unescape(c["name"]), "slug": c["slug"]}
        if page >= int(hdr.get("X-WP-TotalPages", 1)):
            break
        page += 1
    dump_yaml_map(os.path.join(ROOT, "_data", "categories.yml"),
                  {c["slug"]: {"name": c["name"], "wp_id": i} for i, c in categories.items()},
                  "# Generated by tools/wp_import.py: every category on the legacy WordPress blog.\n")

    posts = []
    common = {"_embed": "author,wp:featuredmedia"}
    if args.latest:
        posts, _ = fetch("/wp/v2/posts", {"per_page": args.latest, "orderby": "date", "order": "desc", **common})
    elif args.all:
        page = 1
        while True:
            batch, hdr = fetch("/wp/v2/posts", {"per_page": 20, "page": page, **common})
            posts += batch
            print(f"fetched page {page}/{hdr.get('X-WP-TotalPages')}")
            if page >= int(hdr.get("X-WP-TotalPages", 1)):
                break
            page += 1
    elif args.post:
        posts = [fetch(f"/wp/v2/posts/{i}", common)[0] for i in args.post]
    pages = [fetch(f"/wp/v2/pages/{i}")[0] for i in args.page]

    authors_path = os.path.join(ROOT, "_data", "authors.yml")
    authors = load_yaml_map(authors_path)
    id_map = existing_id_map()
    import_pages(pages, id_map, args.force)
    import_posts(posts, authors, categories, id_map, args.force)
    dump_yaml_map(authors_path, authors,
                  "# Generated by tools/wp_import.py; safe to hand-edit (re-imports update name/url/avatar).\n")
    print(f"done: {len(posts)} post(s), {len(pages)} page(s)")


if __name__ == "__main__":
    main()
