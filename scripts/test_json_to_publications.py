"""Tests for json_to_publications converter."""
import json_to_publications as jp


def test_slugify_basic():
    assert jp.slugify("Beyond DAGs: modeling causal feedback with fuzzy cognitive maps") == \
        "beyond-dags-modeling-causal-feedback-with-fuzzy-cognitive-maps"


def test_slugify_strips_punct_and_collapses():
    assert jp.slugify('Technocultural Pluralism: A "Clash of Civilizations" in Technology?') == \
        "technocultural-pluralism-a-clash-of-civilizations-in-technology"


def test_normalize_title():
    assert jp.normalize_title("  Deterrence in the Age of Thinking Machines. ") == \
        jp.normalize_title("deterrence in the age of thinking machines")


def test_assign_categories_maps_index_to_key():
    research_map = {"clusters": [
        {"label": "Noise Benefits in Machine Learning", "paper_indices": [0, 2]},
        {"label": "AI for National Security & Defense", "paper_indices": [1]},
    ]}
    papers = [{}, {}, {}]
    cats = jp.assign_categories(papers, research_map)
    assert cats == {0: "noise", 2: "noise", 1: "defense"}


def test_dedupe_keeps_higher_citation():
    papers = [
        {"title": "Deterrence in the Age of Thinking Machines", "citation_count": 91, "year": 2020},
        {"title": "deterrence in the age of thinking machines", "citation_count": 0, "year": 2020},
        {"title": "Unique Paper", "citation_count": 5, "year": 2019},
    ]
    kept = jp.dedupe(papers)
    titles = sorted(p["title"] for _, p in kept)
    assert titles == ["Deterrence in the Age of Thinking Machines", "Unique Paper"]
    # original index preserved for the kept duplicate
    kept_idx = {p["title"]: i for i, p in kept}
    assert kept_idx["Deterrence in the Age of Thinking Machines"] == 0


def test_to_frontmatter_has_required_fields():
    paper = {
        "title": 'Technocultural Pluralism: A "Clash" in Technology?',
        "authors": "Osonde A Osoba and Someone Else",
        "year": 2020,
        "venue": "AIES",
        "citation_count": 6,
        "pub_url": "https://example.org/paper",
        "doi": "10.1/x",
        "scholar_id": "abc:def",
    }
    fm = jp.to_frontmatter(paper, "fairness")
    assert fm.startswith("---\n")
    assert fm.rstrip().endswith("---")
    assert "collection: publications" in fm
    assert "category: fairness" in fm
    assert "date: 2020-01-01" in fm
    assert 'venue: "AIES"' in fm
    assert "paperurl:" in fm
    # internal double-quotes in the title must be escaped, not raw
    assert '\\"Clash\\"' in fm


def test_osoba_rank_and_lead_author():
    assert jp.osoba_rank({"authors": "Osonde A Osoba and Bart Kosko"}) == 0
    assert jp.osoba_rank({"authors": "S Navabi and O Osoba"}) == 1
    assert jp.osoba_rank({"authors": "A and B and C and Osonde Osoba"}) == 3
    assert jp.osoba_rank({"authors": "Someone Else"}) is None
    assert jp.is_lead_author({"authors": "Osonde A Osoba and X"}) is True
    assert jp.is_lead_author({"authors": "S Navabi and O Osoba"}) is True
    assert jp.is_lead_author({"authors": "A and B and Osonde Osoba"}) is False


def test_apply_overrides_fills_missing_venue():
    paper = {
        "title": "The Resilience Assessment Framework: Assessing Commercial "
                 "Contributions to US Space Force Mission Resilience",
        "venue": "",
        "year": 2023,
    }
    out = jp.apply_overrides(paper)
    assert out["venue"] == "RAND Corporation"
    # does not clobber an existing venue
    paper2 = {"title": paper["title"], "venue": "Somewhere", "year": 2023}
    assert jp.apply_overrides(paper2)["venue"] == "Somewhere"


def test_paperurl_falls_back_to_doi_then_scholar():
    assert jp.paper_url({"pub_url": "https://p", "doi": "10.1/x"}) == "https://p"
    assert jp.paper_url({"pub_url": "", "doi": "10.1/x"}) == "https://doi.org/10.1/x"
    assert jp.paper_url({"pub_url": "", "doi": "", "scholar_id": "u:v"}).startswith(
        "https://scholar.google.com/citations?view_op=view_citation")
