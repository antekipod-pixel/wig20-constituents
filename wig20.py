"""
Point-in-time WIG20 membership — "which companies were in the index on date D?"

Standard library only. No pandas, no network, no install step: copy this file and
`data/wig20.csv` into your project, or `pip install -e .` if you prefer.

    >>> from wig20 import members_asof
    >>> sorted(members_asof(date(2021, 6, 1)))[:3]
    ['acp.pl', 'ale.pl', 'ccc.pl']

The point of this module is one line of defence against survivorship bias. If you
backtest on *today's* WIG20 you are testing a portfolio of companies selected,
with hindsight, for having survived in the index — which is not a portfolio anyone
could have held in 2020. `members_asof` gives you the index as it actually was.

Read the README before trusting a result: the data is QUARTERLY, so a company that
entered or left on a special revision appears to move up to one quarter late.
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from datetime import date
from functools import lru_cache

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "wig20.csv")

# A blank `end` in the CSV means "still a member at the last covered revision".
# Represented as a real date rather than None so comparisons stay simple and total.
# Matches engine/universe.py in the hedgeyourown backtester, which this is extracted from.
FAR_FUTURE = date(9999, 12, 31)


@dataclass(frozen=True)
class Span:
    """One continuous stretch of index membership, [start, end] — both inclusive."""
    symbol: str
    start: date
    end: date          # INCLUSIVE last day of membership; FAR_FUTURE while a member

    def covers(self, d: date) -> bool:
        # Both ends inclusive. `end` is the LAST day the company was in the index,
        # not the day it left: the replacement's span starts on end + 1, so there is
        # no overlap and no one-day hole. (Reading `end` as exclusive puts the index
        # at 19 names on the eight revision eves in this file — the test suite checks
        # every covered day resolves to exactly 20.)
        return self.start <= d <= self.end


def _parse(value: str) -> date:
    return date.fromisoformat(value)


@lru_cache(maxsize=1)
def spans(path: str | None = None) -> tuple[Span, ...]:
    """Every membership span, sorted by (symbol, start). Cached after first read."""
    out: list[Span] = []
    with open(path or DATA_FILE, encoding="utf-8") as fh:
        # '#' lines carry provenance (source, revisions covered, caveats) — skip them
        # here, but do not delete them from the file: they are what makes a number
        # computed from this data auditable.
        rows = csv.DictReader(line for line in fh if not line.startswith("#"))
        for row in rows:
            symbol = (row.get("symbol") or "").strip()
            if not symbol:
                continue
            end = (row.get("end") or "").strip()
            out.append(Span(symbol, _parse(row["start"].strip()),
                            _parse(end) if end else FAR_FUTURE))
    return tuple(sorted(out, key=lambda s: (s.symbol, s.start)))


def members_asof(d: date, path: str | None = None) -> set[str]:
    """The set of WIG20 tickers that were index members on `d`.

    Returns an EMPTY set for dates before the data horizon (2020-03-20) rather
    than raising or silently returning today's members — an empty universe is a
    loud, obvious failure in a backtest, whereas today's members would quietly
    reintroduce exactly the survivorship bias this dataset exists to remove.
    """
    return {s.symbol for s in spans(path) if s.covers(d)}


def current_members(path: str | None = None) -> set[str]:
    """Members at the last covered revision (2025-09-19)."""
    return {s.symbol for s in spans(path) if s.end == FAR_FUTURE}


def coverage(path: str | None = None) -> tuple[date, date]:
    """(first date covered, last revision with a recorded change)."""
    all_spans = spans(path)
    firsts = min(s.start for s in all_spans)
    lasts = max((s.end for s in all_spans if s.end != FAR_FUTURE), default=firsts)
    return firsts, lasts


if __name__ == "__main__":  # tiny CLI: python wig20.py 2022-06-15
    import sys

    when = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    names = sorted(members_asof(when))
    print(f"WIG20 on {when}: {len(names)} members")
    for n in names:
        print(" ", n)
