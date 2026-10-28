import pytest

from parser import parse_reply


def ok(reply, value, flags=()):
    r = parse_reply(reply)
    assert r["decision"] == value and r["flags"] == list(flags), r
    return r


def failed(reply, error):
    r = parse_reply(reply)
    assert r["decision"] is None and "parse_failed" in r["flags"] and r["parse_error"] == error, r
    return r


def test_standard_format():
    r = ok("I will share some.\n[DECISION]\n4", 4)
    assert r["reason"] == "I will share some."


@pytest.mark.parametrize("reply", ["x\n[DECISION]: 6", "x\n[DECISION]:\n6", "x\n[DECISION]\n: 6", "x\n[DECISION] - 6", "x\n[DECISION]\n- 6", "x\n[DECISION] 6"])
def test_separators_accepted(reply):
    ok(reply, 6)


@pytest.mark.parametrize("n", [0, 10])
def test_boundaries(n):
    ok(f"r\n[DECISION]\n{n}", n)


def test_trailing_full_stop():
    ok("r\n[DECISION]\n5.", 5)


def test_last_tag_wins():
    r = ok("First [DECISION]\n2\nthen I changed my mind.\n[DECISION]\n8", 8)
    assert "changed my mind" in r["reason"]


def test_out_of_range_not_clamped():
    failed("r\n[DECISION]\n11", "out_of_range")
    failed("r\n[DECISION]\n100", "out_of_range")


def test_negative_not_turned_positive():
    failed("r\n[DECISION]\n-3", "out_of_range")
    failed("r\n[DECISION]: -3", "out_of_range")


def test_non_integer_and_absent():
    failed("r\n[DECISION]\n7.5", "non_integer")
    failed("r\n[DECISION]\n5 units", "non_integer")
    failed("r\n[DECISION]\nsome", "no_integer")
    failed("r\n[DECISION]\n", "no_integer")
    failed("r\n[DECISION]", "no_integer")


def test_tags_missing_fallback():
    ok("I give 3.", 3, ["tags_missing"])
    ok("Maybe 2, but finally 5", 5, ["tags_missing"])


def test_tags_missing_failures():
    r = failed("I keep everything.", "no_integer")
    assert "tags_missing" in r["flags"]
    r = parse_reply("I give 12.")
    assert r["decision"] is None and r["flags"] == ["tags_missing", "parse_failed"] and r["parse_error"] == "out_of_range"
    failed("", "no_integer")


def test_fallback_known_weakness_is_flagged():
    # last standalone integer is taken, so "3 of my 10" yields 10; tags_missing flag lets analysis exclude these
    ok("I give 3 of my 10", 10, ["tags_missing"])