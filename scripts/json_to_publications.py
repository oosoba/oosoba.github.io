#!/usr/bin/env python3
"""Convert view-papers/papers.json into academicpages _publications/*.md files.

Category assignment comes from research_map.json (cluster paper_indices ->
publication_category key). No title-based fuzzy matching is used for categories.

Exact normalized-title duplicates are collapsed (highest citation_count wins).
Near-duplicate titles are *reported* for manual review, never auto-deleted.

Usage:
    python3 json_to_publications.py [--source DIR] [--out DIR] [--write]
Without --write it does a dry run (counts + near-dup report only).
"""
import argparse
import json
import os
import re
import sys

# Cluster label (from research_map.json) -> publication_category key (in _config.yml)
LABEL_TO_KEY = {
    "Noise Benefits in Machine Learning": "noise",
    "Algorithmic Fairness, AI Ethics & Privacy": "fairness",
    "Fuzzy Systems & Causal Modeling": "fuzzy",
    "AI for National Security & Defense": "defense",
    "Agent-Based Modeling & Reinforcement Learning for Policy": "abm-rl",
    "Health, Epidemiology & Public Health AI": "health",
    "Economic Networks & Racial Wealth Inequality": "econ",
    "Complex Systems & Policy Analysis Reform": "complex",
}

DEFAULT_SOURCE = "/home/alterego/Sync/worklog/z.career docs/view-papers"


def slugify(title):
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    # keep filenames sane
    return s[:80].strip("-")


def normalize_title(title):
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    s = re.sub(r"\s+", " ", s)
    return s


def assign_categories(papers, research_map):
    """Return {paper_index: category_key} from research_map cluster indices."""
    out = {}
    for cluster in research_map.get("clusters", []):
        key = LABEL_TO_KEY.get(cluster["label"])
        if key is None:
            raise ValueError(f"Unmapped cluster label: {cluster['label']!r}")
        for idx in cluster.get("paper_indices", []):
            out[idx] = key
    return out


def dedupe(papers):
    """Drop exact normalized-title duplicates, keeping the highest citation_count.

    Returns list of (original_index, paper), preserving original order of the
    kept entries.
    """
    best = {}  # norm_title -> (orig_index, citation_count)
    for i, p in enumerate(papers):
        nt = normalize_title(p.get("title", ""))
        cc = p.get("citation_count", 0) or 0
        if nt not in best or cc > best[nt][1]:
            best[nt] = (i, cc)
    keep_indices = {idx for idx, _ in best.values()}
    return [(i, papers[i]) for i in range(len(papers)) if i in keep_indices]


def _tokens(title):
    return set(normalize_title(title).split())


def near_duplicates(papers, threshold=0.85):
    """Report (title_a, title_b, jaccard) pairs above threshold. Read-only."""
    pairs = []
    items = [(p.get("title", ""), _tokens(p.get("title", ""))) for p in papers]
    for i in range(len(items)):
        ti, si = items[i]
        if not si:
            continue
        for j in range(i + 1, len(items)):
            tj, sj = items[j]
            if not sj:
                continue
            if normalize_title(ti) == normalize_title(tj):
                continue  # exact dup, handled by dedupe()
            jac = len(si & sj) / len(si | sj)
            if jac >= threshold:
                pairs.append((ti, tj, round(jac, 2)))
    return pairs


def yaml_dq(value):
    """YAML double-quoted scalar with proper escaping."""
    s = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def authors_display(authors):
    if not authors:
        return ""
    return authors.replace(" and ", ", ")


def paper_url(paper):
    if paper.get("pub_url"):
        return paper["pub_url"]
    if paper.get("doi"):
        return "https://doi.org/" + str(paper["doi"]).lstrip("/")
    if paper.get("scholar_id"):
        return (
            "https://scholar.google.com/citations?view_op=view_citation&hl=en"
            "&user=w5oYjbYAAAAJ&citation_for_view=" + paper["scholar_id"]
        )
    return ""


def build_citation(paper):
    auth = authors_display(paper.get("authors", ""))
    year = paper.get("year", "")
    title = paper.get("title", "")
    venue = paper.get("venue", "")
    cc = paper.get("citation_count", 0) or 0
    cite = f'{auth} ({year}). "{title}." <i>{venue}</i>.'
    if cc > 0:
        cite += f" (Cited by {cc}.)"
    return cite


def to_frontmatter(paper, category_key):
    year = paper.get("year", 1900)
    lines = [
        "---",
        f"title: {yaml_dq(paper.get('title', ''))}",
        "collection: publications",
        f"category: {category_key}",
        f"date: {year}-01-01",
        f"venue: {yaml_dq(paper.get('venue', ''))}",
        f"citation: {yaml_dq(build_citation(paper))}",
    ]
    url = paper_url(paper)
    if url:
        lines.append(f"paperurl: {yaml_dq(url)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def render(paper, category_key):
    fm = to_frontmatter(paper, category_key)
    abstract = (paper.get("abstract") or "").strip()
    body = ("\n" + abstract + "\n") if abstract else ""
    return fm + body


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=DEFAULT_SOURCE)
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_publications"))
    ap.add_argument("--write", action="store_true", help="actually write files")
    args = ap.parse_args(argv)

    with open(os.path.join(args.source, "papers.json")) as f:
        papers = json.load(f)
    with open(os.path.join(args.source, "research_map.json")) as f:
        research_map = json.load(f)

    cats = assign_categories(papers, research_map)
    missing = [i for i in range(len(papers)) if i not in cats]
    if missing:
        print(f"WARNING: {len(missing)} papers have no category: indices {missing}",
              file=sys.stderr)

    kept = dedupe(papers)
    print(f"papers: {len(papers)} total, {len(kept)} after exact-title dedupe")

    nd = near_duplicates(papers)
    if nd:
        print(f"\n-- {len(nd)} near-duplicate title pairs (REVIEW MANUALLY, not deleted) --")
        for a, b, jac in nd:
            print(f"  [{jac}] {a[:60]!r}  ~  {b[:60]!r}")

    if not args.write:
        print("\n(dry run; pass --write to generate files)")
        return 0

    os.makedirs(args.out, exist_ok=True)
    # clear previous generated demo files
    for fn in os.listdir(args.out):
        if fn.endswith(".md"):
            os.remove(os.path.join(args.out, fn))

    used = set()
    written = 0
    for idx, paper in kept:
        cat = cats.get(idx, "fairness")  # safe fallback; warned above if missing
        year = paper.get("year", 1900)
        base = f"{year}-{slugify(paper.get('title', 'untitled'))}"
        name = base
        n = 2
        while name in used:
            name = f"{base}-{n}"
            n += 1
        used.add(name)
        with open(os.path.join(args.out, name + ".md"), "w") as f:
            f.write(render(paper, cat))
        written += 1
    print(f"\nwrote {written} files to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
