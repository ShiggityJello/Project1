from logkit.parser import iter_events, count_by_level


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
