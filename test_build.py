"""Tests for build.py helpers (titlecase, erratum filter, front matter, dates)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402


def test_titlecase_small_words_and_first():
    assert build.titlecase("an intelligence in our image: the risks of bias") == \
        "An Intelligence in Our Image: The Risks of Bias"


def test_titlecase_preserves_acronyms_and_slash():
    assert build.titlecase("beyond DAGs: an AI/ML view") == "Beyond DAGs: An AI/ML View"


def test_titlecase_hyphen_parts_capitalized():
    assert build.titlecase("noise-enhanced convolutional neural networks") == \
        "Noise-Enhanced Convolutional Neural Networks"


def test_is_erratum():
    assert build.is_erratum("Corrigendum to 'Noise enhanced clustering'")
    assert build.is_erratum("Erratum: something")
    assert not build.is_erratum("A Normal Paper Title")
    assert not build.is_erratum("")


def test_parse_front_matter_basic_with_colon_value():
    text = "---\ntitle: Hello: World\ndate: 2026-01-02\ntags: [a, b]\ndraft: false\n---\nBody"
    meta, body = build.parse_front_matter(text)
    assert meta["title"] == "Hello: World"
    assert meta["date"] == "2026-01-02"
    assert meta["tags"] == ["a", "b"]
    assert meta["draft"] is False
    assert body.strip() == "Body"


def test_parse_front_matter_none_and_unterminated():
    assert build.parse_front_matter("plain body") == ({}, "plain body")
    meta, _ = build.parse_front_matter("---\ntitle: X\nno closing marker")
    assert meta == {}


def test_format_date_portable_and_fallback():
    assert build.format_date("2026-07-01") == "July 1, 2026"
    assert build.format_date("not a date") == "not a date"
