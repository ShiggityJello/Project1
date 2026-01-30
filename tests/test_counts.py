import pytest
from logkit.parser import iter_events, count_by_level
import json
import subprocess


def test_count_by_level_sample_log():
    counts = count_by_level(iter_events("data/sample.log"))
    assert counts["INFO"] == 2
    assert counts["WARN"] == 2
    assert counts["ERROR"] == 1


def test_contains_filter():
    counts = count_by_level(iter_events(
        "data/sample.log"), contains="login failed")
    assert counts == {"WARN": 2}


def test_src_ip_and_contains():
    counts = count_by_level(iter_events("data/sample.log"),
                            src_ip="10.0.0.5", contains="heart")
    assert counts == {"INFO": 1}


def test_iter_events_strict_raises():
    with pytest.raises(ValueError):
        list(iter_events("data/bad.log", strict=True))


def test_until_filter_counts():
    counts = count_by_level(iter_events(
        "data/sample.log", until="2026-01-30T05:00:02Z"))
    assert counts == {"INFO": 1, "WARN": 1}


def test_combined_filters():
    counts = count_by_level(
        iter_events(
            "data/sample.log",
            since="2026-01-30T05:00:02Z",
            until="2026-01-30T05:00:03Z",
        ),
        src_ip="10.0.0.8",
        contains="login failed",
    )
    assert counts == {"WARN": 2}


def test_json_output_runs():
    out = subprocess.check_output(
        ["python", "main.py", "data/sample.log", "--json"],
        text=True,
    )
    obj = json.loads(out)
    assert obj["counts_by_level"]["INFO"] == 2
