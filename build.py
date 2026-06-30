#!/usr/bin/env python3
"""Build site/index.html from site/index.template.html + publications data.

Reuses the tested helpers in scripts/json_to_publications.py for dedupe,
first/second-author filtering, category assignment, and URL selection.

Usage:  python3 build.py
"""
import html
import json
import os
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
    out = []
    for key in ORDER:
        items = groups.get(key, [])
        if not items:
            continue
        plural = "paper" if len(items) == 1 else "papers"
        out.append('<details class="cluster">')
        out.append(
            f'  <summary class="cluster-head">'
            f'<span class="cluster-name">{html.escape(TITLES[key])}</span>'
            f'<span class="count">{len(items)} {plural}</span></summary>'
        )
        out.append('  <div class="pub-list">')
        for p in items:
            url = jp.paper_url(p)
            title = html.escape(p.get("title", "").strip())
            title_html = (f'<a class="pub-title" href="{html.escape(url)}">{title}</a>'
                          if url else f'<span class="pub-title">{title}</span>')
            out.append('    <div class="pub">')
            out.append(f'      {title_html}')
            out.append(f'      <p class="pub-meta">{render_meta(p)}</p>')
            out.append('    </div>')
        out.append('  </div>')
        out.append('</details>')
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
