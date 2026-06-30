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

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import json_to_publications as jp  # noqa: E402

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


def featured_publications():
    with open(os.path.join(SOURCE, "papers.json")) as f:
        papers = json.load(f)
    with open(os.path.join(SOURCE, "research_map.json")) as f:
        research_map = json.load(f)

    cats = jp.assign_categories(papers, research_map)
    kept = jp.dedupe(papers)
    kept = [(i, jp.apply_overrides(p)) for i, p in kept if jp.is_lead_author(p)]
    kept = [(i, p) for i, p in kept if p.get("year")]

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
    if venue:
        parts.append(html.escape(venue))
    if p.get("year"):
        parts.append(str(p["year"]))
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
    out.append('<div class="chips" id="cluster-chips" role="tablist" aria-label="Filter by research area">')
    out.append('  <button type="button" class="chip active" data-cluster="all">'
               f'All <span class="chip-count">{total}</span></button>')
    for k in nonempty:
        out.append(f'  <button type="button" class="chip" data-cluster="{k}">'
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


def main():
    groups = featured_publications()
    total = sum(len(v) for v in groups.values())
    pubs_html = render_publications(groups)

    with open(TEMPLATE) as f:
        template = f.read()
    if "<!--PUBLICATIONS-->" not in template:
        print("ERROR: marker <!--PUBLICATIONS--> not found in template", file=sys.stderr)
        return 1
    page = template.replace("<!--PUBLICATIONS-->", pubs_html)
    with open(OUTPUT, "w") as f:
        f.write(page)

    print(f"built {OUTPUT}")
    print(f"  {total} featured publications across "
          f"{sum(1 for k in ORDER if groups.get(k))} clusters")
    for k in ORDER:
        if groups.get(k):
            print(f"    {len(groups[k]):2d}  {TITLES[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
