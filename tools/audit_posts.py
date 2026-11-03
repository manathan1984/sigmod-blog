#!/usr/bin/env python3
"""Flag imported posts that should be checked by eye against the old blog.

Reads _posts/*.html (and the built _site/ if present) and writes
IMPORT_REVIEW.md: one row per post with the reasons it was flagged and links
to both the new page and the original on wp.sigmod.org.

    python3 tools/audit_posts.py [--site-url https://sigmod-org.github.io/blog.sigmod.org]
"""

import argparse
import html
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEGACY = "https://wp.sigmod.org"

# (reason, regex over the post body, severity) — severity 2 = likely broken, 1 = worth a look
CHECKS = [
    ("embedded iframe/video (YouTube, slides, maps…)", r"<(iframe|object|embed|video|audio)\b", 2),
    ("unrendered shortcode", r"\[(/?)(caption|embed|gallery|latex|video|audio|youtube|slideshare|tweet|code|sourcecode)[\] ]", 2),
    ("LaTeX / math markup", r"\$\$|\\\(|\\\[|\$latex|class=\"[^\"]*(MathJax|katex|ql-img-inline-formula)", 2),
    ("script or style block in content", r"<(script|style)\b", 2),
    ("image hosted outside wp.sigmod.org (may disappear)", r"<img[^>]+src=\"https?://(?!wp\.sigmod\.org)[^\"]+\"", 1),
    ("remaining link to an old wp.sigmod.org page", r"https?://wp\.sigmod\.org/?(\?|index\.php|[0-9]{4}/)", 1),
    ("link to another old SIGMOD host", r"https?://(www\.)?sigmod\.org/(blog|wp-content)", 1),
    ("table", r"<table\b", 1),
    ("code / preformatted block", r"<(pre|code)\b", 1),
    ("fixed inline width/height styles", r"style=\"[^\"]*(width|height):\s*\d{3,}px", 1),
    ("possible mojibake (bad character encoding)", r"Ã.|â€|Â\s", 2),
]


# Results of looking at flagged posts by eye, keyed by WordPress ID.
# "ok": renders correctly, flag can be ignored. "human": still needs a decision.
REVIEWED = {
    978: ("ok", "YouTube embed (now https) plays; inline code renders."),
    2012: ("ok", "Fixed-width pull-quote box floats right as intended."),
    2897: ("ok", "Data tables render."),
    3403: ("ok", "Inline code and table image render."),
    3624: ("ok", "Data tables render."),
    3726: ("ok", "Reference table renders."),
    3833: ("ok", "Fixed width is the resized author photo."),
    3855: ("ok", "Fixed width is the resized author photo."),
    3379: ("ok", "Jim Gray photo fixed: importer now requests a supported Wikimedia thumbnail size (250px)."),
    2454: ("human", "One image (edtosavetheworld…/paradigms.png) is dead on the old blog too; five others are hotlinked "
                    "from blogspot/wordpress.com and could disappear. Decide whether to remove the dead one."),
    3760: ("human", "Wide results table now scrolls sideways; check it reads well. Three footnote links (#_ftn1, "
                    "#_msocom_1, #_bookmark6) have no target, as on the old blog."),
}


def front_matter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    fm = {}
    for line in (m.group(1) if m else "").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm, text[m.end():] if m else text


def div_balance(body):
    return len(re.findall(r"<div\b", body)) - len(re.findall(r"</div>", body))


def url_ok(url):
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:  # noqa: BLE001
        return False


def audit(site_url, check_external=True):
    rows = []
    posts_dir = os.path.join(ROOT, "_posts")
    for fn in sorted(os.listdir(posts_dir), reverse=True):
        text = open(os.path.join(posts_dir, fn), encoding="utf-8").read()
        fm, body = front_matter(text)
        body = body.replace("{% raw %}", "").replace("{% endraw %}", "")
        reasons, score = [], 0

        for reason, rx, sev in CHECKS:
            n = len(re.findall(rx, body, re.I))
            if n:
                reasons.append(f"{reason} ({n})")
                score += sev

        targets = set(re.findall(r"\b(?:id|name)=\"([^\"]+)\"", body))
        missing = [a for a in re.findall(r"href=\"#([^\"]+)\"", body) if a not in targets]
        if missing:
            reasons.append(f"footnote/anchor links without a target ({len(missing)})")
            score += 1

        if check_external:
            for src in re.findall(r"<img[^>]+src=\"(https?://[^\"]+)\"", body):
                if not url_ok(html.unescape(src)):
                    reasons.append(f"external image no longer loads: {src[:60]}…")
                    score += 2

        if re.match(r"user-\d+$", fm.get("author", "")):
            reasons.append("author unknown (placeholder user-N)")
            score += 2

        bal = div_balance(body)
        if bal:
            reasons.append(f"unbalanced &lt;div&gt; tags ({bal:+d}); may break the page layout")
            score += 2

        plain = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body))).strip()
        if len(plain) < 600:
            reasons.append(f"very short body ({len(plain)} chars)")
            score += 2

        for src in re.findall(r"<img[^>]+src=\"((?:\.\./)+wp-content/[^\"]+)\"", body):
            path = os.path.join(ROOT, re.sub(r"^(\.\./)+", "", src))
            if not os.path.exists(path):
                reasons.append(f"missing local image {src}")
                score += 2

        built = os.path.join(ROOT, "_site", fm.get("permalink", "").strip("/"), "index.html")
        if os.path.exists(built):
            page = open(built, encoding="utf-8").read()
            # Content must not close the layout's containers: sidebar has to stay inside #content-area.
            main = page.split('<aside id="sidebar">')[0]
            if main.count("<div") - main.count("</div>") != 4:
                reasons.append("layout broken in built page (sidebar pushed out)")
                score += 2

        if reasons:
            rows.append((score, fm, reasons))

    def wid(fm):
        return int(fm.get("wp_id", 0))

    rows.sort(key=lambda r: (-r[0], r[1].get("date", "")))
    human = [r for r in rows if REVIEWED.get(wid(r[1]), ("",))[0] != "ok"]
    ok = [r for r in rows if REVIEWED.get(wid(r[1]), ("",))[0] == "ok"]
    out = [
        "# Import review",
        "",
        "Generated by `tools/audit_posts.py` after importing from wp.sigmod.org.",
        "Every post was checked automatically for content that may not survive the move (embeds, math,",
        "external images, broken layout, unresolved old links, missing images…). Flagged posts were then",
        "looked at by eye; the verdicts live in `REVIEWED` in the script.",
        "",
        f"{len(rows)} of {len(os.listdir(posts_dir))} posts flagged: **{len(human)} need a human decision**, "
        f"{len(ok)} were checked and render correctly.",
        "",
        "## Needs a human look",
        "",
        "| Post | What to check | Links |",
        "| --- | --- | --- |",
    ]

    def links(fm):
        new = site_url.rstrip("/") + fm.get("permalink", "")
        return f"[new]({new}) · [old]({LEGACY}/?p={fm.get('wp_id')})"

    def title(fm):
        return f"{fm.get('title', '').replace('|', chr(92) + '|')} ({fm.get('date', '')[:10]})"

    for score, fm, reasons in human:
        note = REVIEWED.get(wid(fm), (None, "Not reviewed yet: " + "; ".join(reasons)))[1]
        out.append(f"| {title(fm)} | {note} | {links(fm)} |")
    out += ["", "## Flagged, checked, fine", "", "| Post | Flags | Verdict | Links |", "| --- | --- | --- | --- |"]
    for score, fm, reasons in ok:
        out.append(f"| {title(fm)} | {'; '.join(reasons)} | {REVIEWED[wid(fm)][1]} | {links(fm)} |")
    path = os.path.join(ROOT, "IMPORT_REVIEW.md")
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print(f"{len(rows)} posts flagged ({len(human)} need a human) -> {os.path.relpath(path, ROOT)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site-url", default="https://sigmod-org.github.io/blog.sigmod.org")
    ap.add_argument("--offline", action="store_true", help="skip checking that external images still load")
    a = ap.parse_args()
    audit(a.site_url, not a.offline)
