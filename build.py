#!/usr/bin/env python3
"""Build site/index.html from site/index.template.html + publications data.

Reuses the tested helpers in scripts/json_to_publications.py for dedupe,
first/second-author filtering, category assignment, and URL selection.

Usage:  python3 build.py
"""
import html
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime

import markdown

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import json_to_publications as jp  # noqa: E402

POSTS_DIR = os.path.join(ROOT, "posts")
WRITING_DIR = os.path.join(ROOT, "writing")
POST_TEMPLATE = os.path.join(ROOT, "post.template.html")
SITE_URL = "https://ope-osoba.me"

SOURCE = jp.DEFAULT_SOURCE
TEMPLATE = os.path.join(ROOT, "index.template.html")
OUTPUT = os.path.join(ROOT, "index.html")

# Merge several source clusters into one display cluster.
MERGE = {
    "abm-rl": "policy-modeling",
    "econ": "policy-modeling",
    "complex": "policy-modeling",
}

# Display order + titles for the research clusters (post-merge keys).
ORDER = ["fairness", "defense", "health", "policy-modeling", "fuzzy", "noise"]
TITLES = {
    "fairness": "Algorithmic Fairness, AI Ethics & Privacy",
    "defense": "AI for National Security & Defense",
    "health": "Health, Epidemiology & Public Health AI",
    "policy-modeling": "Computational Social Science & Policy Modeling",
    "fuzzy": "Fuzzy Systems & Causal Modeling",
    "noise": "Noise Benefits in Machine Learning",
}

# Short labels for the filter chips (full titles used for section headings).
SHORT = {
    "fairness": "Fairness",
    "defense": "Defense",
    "health": "Health",
    "policy-modeling": "Policy Modeling",
    "fuzzy": "Fuzzy Systems",
    "noise": "Noise Benefits",
}


def is_erratum(title):
    """Corrigenda / errata are correction notices, not standalone papers."""
    t = (title or "").strip().lower()
    return t.startswith(("corrigendum", "corrigenda", "erratum", "errata"))


def featured_publications():
    with open(os.path.join(SOURCE, "papers.json")) as f:
        papers = json.load(f)
    with open(os.path.join(SOURCE, "research_map.json")) as f:
        research_map = json.load(f)

    cats = jp.assign_categories(papers, research_map)
    kept = jp.dedupe(papers)
    kept = [(i, jp.apply_overrides(p)) for i, p in kept if jp.is_lead_author(p)]
    kept = [(i, p) for i, p in kept if p.get("year")]
    kept = [(i, p) for i, p in kept if not is_erratum(p.get("title", ""))]

    groups = {k: [] for k in ORDER}
    for i, p in kept:
        key = cats.get(i, "fairness")
        key = MERGE.get(key, key)
        groups.setdefault(key, []).append(p)
    for k in groups:
        groups[k].sort(key=lambda p: (p.get("year", 0), p.get("citation_count", 0) or 0),
                       reverse=True)
    return groups


SMALL_WORDS = {
    "a", "an", "and", "as", "at", "but", "by", "for", "from", "if", "in", "into",
    "nor", "of", "on", "onto", "or", "over", "per", "so", "the", "to", "up", "via",
    "vs", "with", "yet",
}


def _cap_token(tok):
    parts = re.split(r"([-–/])", tok)  # keep hyphen / en-dash / slash delimiters
    out = []
    for part in parts:
        if part in ("-", "–", "/") or not part:
            out.append(part)
            continue
        core = re.sub(r"[^A-Za-z0-9]", "", part)
        if core and (core.isupper() or any(c.isupper() for c in core[1:])):
            out.append(part)  # preserve acronym / mixed-case token
        else:
            out.append(part[0].upper() + part[1:])
    return "".join(out)


def titlecase(title):
    """Title-case a paper title, preserving acronyms and lowercasing small words."""
    if not title:
        return title
    words = title.split(" ")
    res = []
    new_sentence = True  # first word, or first word after a colon
    last = len(words) - 1
    for i, w in enumerate(words):
        if not w:
            res.append(w)
            continue
        core = re.sub(r"[^A-Za-z0-9]", "", w)
        if core and (core.isupper() or any(c.isupper() for c in core[1:])):
            res.append(w)  # preserve acronym / mixed-case
        elif (not new_sentence) and i != last and core.lower() in SMALL_WORDS:
            res.append(w.lower())
        else:
            res.append(_cap_token(w))
        new_sentence = w.endswith(":")
    return " ".join(res)


def render_meta(p):
    parts = []
    venue = (p.get("venue") or "").strip()
    if "bound method" in venue.lower() or "<" in venue:  # guard against scraper repr leaks
        venue = ""
    year = p.get("year")
    if venue and year:  # the year is shown separately; drop a trailing duplicate
        venue = re.sub(rf",?\s*{re.escape(str(year))}\s*$", "", venue).rstrip(", ")
    if venue:
        parts.append(html.escape(venue))
    if year:
        parts.append(str(year))
    cc = p.get("citation_count", 0) or 0
    line = " · ".join(parts)
    if cc > 0:
        sep = " · " if line else ""
        line += f'{sep}<span class="cite">Cited by {cc}</span>'
    return line


def render_publications(groups):
    nonempty = [k for k in ORDER if groups.get(k)]
    total = sum(len(groups[k]) for k in nonempty)
    out = []

    # Filter chips (always visible): All + one per cluster.
    out.append('<div class="chips" id="cluster-chips" role="group" aria-label="Filter by research area">')
    out.append('  <button type="button" class="chip active" data-cluster="all" aria-pressed="true">'
               f'All <span class="chip-count">{total}</span></button>')
    for k in nonempty:
        out.append(f'  <button type="button" class="chip" data-cluster="{k}" aria-pressed="false">'
                   f'{html.escape(SHORT.get(k, TITLES[k]))} '
                   f'<span class="chip-count">{len(groups[k])}</span></button>')
    out.append('</div>')

    # Grouped sections (filtered by the chips).
    out.append('<div class="pub-groups">')
    for k in nonempty:
        out.append(f'<section class="pub-group" data-cluster="{k}">')
        out.append(f'  <h3 class="pub-group-title">{html.escape(TITLES[k])}</h3>')
        for p in groups[k]:
            url = jp.paper_url(p)
            title = html.escape(titlecase(p.get("title", "").strip()))
            title_html = (f'<a class="pub-title" href="{html.escape(url)}">{title}</a>'
                          if url else f'<span class="pub-title">{title}</span>')
            out.append('  <div class="pub">')
            out.append(f'    {title_html}')
            out.append(f'    <p class="pub-meta">{render_meta(p)}</p>')
            out.append('  </div>')
        out.append('</section>')
    out.append('</div>')
    return "\n".join(out)


# --------------------------------------------------------------------------
# Blog posts: posts/*.md -> writing/<slug>.html + Writing-tab index
# --------------------------------------------------------------------------

def make_markdown():
    return markdown.Markdown(
        extensions=[
            "pymdownx.superfences",   # fenced code blocks
            "pymdownx.highlight",     # Pygments highlighting at build time
            "pymdownx.arithmatex",    # math -> KaTeX-ready \( \) / \[ \]
            "pymdownx.tilde",         # ~~strikethrough~~
            "tables", "footnotes", "attr_list", "md_in_html", "sane_lists", "toc",
        ],
        extension_configs={
            "pymdownx.highlight": {"css_class": "highlight", "guess_lang": False},
            "pymdownx.arithmatex": {"generic": True},
        },
    )


def parse_front_matter(text):
    """Minimal YAML-ish front matter: key: value, plus tags: [a, b] and draft."""
    if not text.startswith("---"):
        return {}, text
    lines = text.split("\n")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, text
    meta = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if k == "tags":
            v = v.strip("[]")
            meta["tags"] = [t.strip().strip("\"'") for t in v.split(",") if t.strip()]
        elif k == "draft":
            meta["draft"] = v.lower() in ("true", "yes", "1")
        else:
            meta[k] = v.strip("\"'")
    return meta, "\n".join(lines[end + 1:])


def format_date(d):
    try:
        dt = datetime.strptime(d.strip(), "%Y-%m-%d")
        return f"{dt.strftime('%B')} {dt.day}, {dt.year}"  # %-d is glibc-only; use dt.day
    except (ValueError, AttributeError):
        return d


def format_post_meta(datestr, tags):
    s = html.escape(format_date(datestr)) if datestr else ""
    if tags:
        chips = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in tags)
        s += (" &middot; " if s else "") + f'<span class="tags">{chips}</span>'
    return s


def render_posts():
    """Render each posts/*.md to writing/<slug>.html; return metadata, newest first."""
    if not os.path.isdir(POSTS_DIR):
        return []
    os.makedirs(WRITING_DIR, exist_ok=True)
    for old in os.listdir(WRITING_DIR):  # clear stale generated post pages
        if old.endswith(".html"):
            os.remove(os.path.join(WRITING_DIR, old))
    with open(POST_TEMPLATE) as f:
        tmpl = f.read()
    md = make_markdown()
    posts = []
    used = set()
    for fn in sorted(os.listdir(POSTS_DIR)):
        if not fn.endswith(".md"):
            continue
        with open(os.path.join(POSTS_DIR, fn)) as f:
            meta, body = parse_front_matter(f.read())
        if meta.get("draft"):
            continue
        md.reset()
        content = md.convert(body)
        base = meta.get("slug") or re.sub(r"^\d{4}-\d{2}-\d{2}-", "", fn[:-3])
        slug, n = base, 2
        while slug in used:           # de-collide like the publications converter
            slug, n = f"{base}-{n}", n + 1
        used.add(slug)
        title = meta.get("title", slug)
        summary = meta.get("summary", "")
        tags = meta.get("tags", [])
        # Single-pass substitution: a value containing "{{X}}" is never re-expanded.
        repl = {
            "TITLE": html.escape(title),
            "SUMMARY": html.escape(summary),
            "META": format_post_meta(meta.get("date", ""), tags),
            "CONTENT": content,
            "CANONICAL": f"{SITE_URL}/writing/{slug}.html",
        }
        page = re.sub(r"\{\{(\w+)\}\}", lambda m: repl.get(m.group(1), m.group(0)), tmpl)
        with open(os.path.join(WRITING_DIR, slug + ".html"), "w") as f:
            f.write(page)
        posts.append({"slug": slug, "title": title, "summary": summary,
                      "tags": tags, "date": meta.get("date", "")})
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def render_post_index(posts):
    if not posts:
        return '<p class="posts-empty">Posts are in progress and will appear here.</p>'
    out = []
    tagcount = Counter(t for p in posts for t in p["tags"])
    if tagcount:
        out.append('<div class="chips" id="tag-chips" role="group" aria-label="Filter posts by tag">')
        out.append('  <button type="button" class="chip active" data-tag="all" aria-pressed="true">'
                   f'All <span class="chip-count">{len(posts)}</span></button>')
        for tag, c in sorted(tagcount.items()):
            out.append(f'  <button type="button" class="chip" data-tag="{html.escape(tag)}" aria-pressed="false">'
                       f'{html.escape(tag)} <span class="chip-count">{c}</span></button>')
        out.append('</div>')
    out.append('<div class="post-list">')
    for p in posts:
        datatags = " ".join(html.escape(t) for t in p["tags"])
        out.append(f'<div class="post-item" data-tags="{datatags}">')
        out.append(f'  <a class="post-item-title" href="writing/{html.escape(p["slug"])}.html">'
                   f'{html.escape(p["title"])}</a>')
        if p["summary"]:
            out.append(f'  <p class="post-item-summary">{html.escape(p["summary"])}</p>')
        out.append(f'  <div class="post-item-meta">{format_post_meta(p["date"], p["tags"])}</div>')
        out.append('</div>')
    out.append('</div>')
    return "\n".join(out)


def write_sitemap(posts):
    today = datetime.now().strftime("%Y-%m-%d")
    urls = [(f"{SITE_URL}/", today)]
    for p in posts:
        urls.append((f"{SITE_URL}/writing/{p['slug']}.html", p.get("date") or today))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in urls:
        lines.append(f"  <url><loc>{html.escape(loc)}</loc><lastmod>{lastmod}</lastmod></url>")
    lines.append("</urlset>")
    with open(os.path.join(ROOT, "sitemap.xml"), "w") as f:
        f.write("\n".join(lines) + "\n")
    return len(urls)


def main():
    groups = featured_publications()
    total = sum(len(v) for v in groups.values())
    pubs_html = render_publications(groups)

    posts = render_posts()
    posts_html = render_post_index(posts)

    with open(TEMPLATE) as f:
        template = f.read()
    if "<!--PUBLICATIONS-->" not in template:
        print("ERROR: marker <!--PUBLICATIONS--> not found in template", file=sys.stderr)
        return 1
    page = template.replace("<!--PUBLICATIONS-->", pubs_html)
    page = page.replace("<!--POSTS-->", posts_html)
    with open(OUTPUT, "w") as f:
        f.write(page)

    print(f"built {OUTPUT}")
    print(f"  {total} featured publications across "
          f"{sum(1 for k in ORDER if groups.get(k))} clusters")
    for k in ORDER:
        if groups.get(k):
            print(f"    {len(groups[k]):2d}  {TITLES[k]}")
    print(f"  {len(posts)} blog post(s) -> writing/")
    n = write_sitemap(posts)
    print(f"  sitemap.xml: {n} URL(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
