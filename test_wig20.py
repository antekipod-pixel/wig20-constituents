"""Tests for the point-in-time WIG20 dataset and loader.

These check the DATA as much as the code: a membership file with overlapping
spans, a gap on a revision day, or the wrong number of members on some date is a
silently wrong backtest for everyone who uses it. Run with `pytest`.
"""
from datetime import date, timedelta

import pytest

from wig20 import FAR_FUTURE, coverage, current_members, members_asof, spans


def test_the_index_has_twenty_members_on_every_covered_day():
    """WIG20 holds exactly 20 names. If any day resolves to a different count, the
    spans are wrong — this is the single strongest check on the whole dataset."""
    first, last = coverage()
    bad = []
    d = first
    while d <= last:
        n = len(members_asof(d))
        if n != 20:
            bad.append((d.isoformat(), n))
        d += timedelta(days=1)
    assert not bad, f"days where the index did not hold 20 names: {bad[:10]}"


def test_current_members_are_twenty():
    assert len(current_members()) == 20


def test_no_symbol_overlaps_itself():
    """A company can leave and come back (several did). Its spans must not overlap,
    or it would be counted twice on the same day."""
    by_symbol: dict[str, list] = {}
    for s in spans():
        by_symbol.setdefault(s.symbol, []).append(s)
    for symbol, ss in by_symbol.items():
        ss.sort(key=lambda s: s.start)
        for earlier, later in zip(ss, ss[1:]):
            assert earlier.end < later.start, f"{symbol}: {earlier} overlaps {later}"


def test_spans_are_ordered_and_non_empty():
    for s in spans():
        assert s.start <= s.end, f"reversed span: {s}"


def test_symbols_use_the_documented_convention():
    for s in spans():
        assert s.symbol == s.symbol.lower(), s.symbol
        assert s.symbol.endswith(".pl"), s.symbol


def test_before_the_horizon_returns_empty_not_todays_members():
    """The failure mode this dataset exists to prevent: quietly answering an
    out-of-range question with today's index."""
    first, _ = coverage()
    assert members_asof(first - timedelta(days=1)) == set()
    assert members_asof(date(2015, 1, 1)) == set()


def test_end_date_is_the_last_day_of_membership_not_the_day_after():
    """`end` is INCLUSIVE. Getting this backwards is the easiest way to misuse the
    file: it opens a one-day hole on every revision eve and quietly drops a name
    from the universe on the last day it actually counted."""
    leaver = next(s for s in spans() if s.end != FAR_FUTURE)
    assert leaver.symbol in members_asof(leaver.end)
    assert leaver.symbol not in members_asof(leaver.end + timedelta(days=1))


def test_a_known_returning_company_is_modelled_as_two_spans():
    """Sanity-check against the real index: some names left and later returned."""
    returning = [sym for sym, count in
                 ((s.symbol, sum(1 for x in spans() if x.symbol == s.symbol))
                  for s in spans()) if count > 1]
    assert returning, "expected at least one company with more than one span"


@pytest.mark.parametrize("when", ["2020-03-20", "2022-06-15", "2025-01-02"])
def test_spot_dates_resolve(when):
    assert len(members_asof(date.fromisoformat(when))) == 20
