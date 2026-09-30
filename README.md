# WIG20 point-in-time constituents (2020–2025)

**Which companies were actually in the WIG20 index on any given date, in a machine-readable file.**

31 membership spans covering 28 distinct companies across 23 quarterly revisions,
from 2020-03-20 to 2025-09-19. CSV and JSON, public-domain, no dependencies, no API key.

```python
from datetime import date
from wig20 import members_asof

members_asof(date(2022, 6, 15))
# {'acp.pl', 'ale.pl', 'ccc.pl', 'cdr.pl', 'cps.pl', 'dnp.pl', 'jsw.pl', ...}  # 20 names
```

## Why this exists

If you backtest a strategy on **today's** WIG20, you are testing a portfolio of
companies chosen, with hindsight, for still being in the index. That portfolio was
not available to anyone in 2020. The effect is not small: **6 of the 20 names in the
index at the last covered revision were not in it in March 2020**
(`ale.pl`, `bdx.pl`, `kru.pl`, `kty.pl`, `pco.pl`, `zab.pl`), and 6 that were in it
then have since dropped out (`cps.pl`, `jsw.pl`, `lts.pl`, `pgn.pl`, `ply.pl`,
`tpe.pl`). Nearly a third of the index turned over in five and a half years.

This is survivorship bias, and for the WIG20 it is unusually awkward to remove,
because the constituent history is published by GPW Benchmark only as a series of
per-revision PDFs. There is no free, machine-readable membership history for the
Warsaw Stock Exchange's main index. This repository is that file.

## What is in here

| File | What it is |
|---|---|
| `data/wig20.csv` | The dataset. One row per membership span: `symbol,start,end` |
| `data/wig20.json` | The same data as JSON, for non-Python users |
| `wig20.py` | A ~100-line stdlib loader. `members_asof(d)`, `current_members()`, `coverage()` |
| `test_wig20.py` | 11 tests, most of which check the **data**, not the code (see below) |

Dates are ISO `YYYY-MM-DD`. `end` is the **last day of membership**, inclusive — the
replacing company's span starts on `end + 1`. A blank `end` means "still a member at
the last covered revision". Symbols follow the Stooq convention (lowercase, `.pl`
suffix): `pkn.pl`, `cdr.pl`, `ale.pl`.

## What the tests check

The tests exist because a wrong membership file produces a *plausible* backtest,
which is worse than one that crashes. The strongest check walks **every single day**
in the covered range and asserts the index resolves to exactly 20 names:

```
test_the_index_has_twenty_members_on_every_covered_day
```

That one test catches overlapping spans, one-day holes on revision days, off-by-one
errors in date handling, and any row where a company was added without another being
removed. It found a real bug in this repository's own loader on the first run (an
exclusive-end reading opened a 19-name hole on all eight revision eves).

The rest check that no company overlaps itself (several left and later returned),
that symbols follow the documented convention, and that a date **before** the data
horizon returns an empty set rather than today's index — an empty universe fails
loudly in a backtest, while today's index would silently reintroduce exactly the
bias this dataset exists to remove.

## Provenance

Extracted from **GPW Benchmark's official historical index portfolios**
(*Historyczne portfele indeksów*, per-revision PDFs at
`gpwbenchmark.pl/historyczne-portfele-indeksow`), matched to tickers by ISIN. The
provenance header is kept inside `data/wig20.csv` itself, so a number computed from
this file can be traced back to its source without this README.

## Known limitations — read before trusting a result

- **Quarterly granularity.** Revisions are taken at the regular quarterly dates (the
  third Friday of March, June, September and December). Intra-quarter *special*
  revisions — a company delisted after a takeover, for example — are snapped to the
  next quarterly boundary, so an entry or exit can lag its real date by up to one
  quarter.
- **Coverage starts 2020-03-20.** Earlier dates return an empty set. This is a data
  horizon, not an assertion that the index did not exist before.
- **Membership is not the whole survivorship story.** Knowing a company was a member
  is only useful if you can also *price* it after it left or was delisted. Free price
  feeds commonly drop delisted tickers, which quietly reintroduces survivorship bias
  through the back door and flatters drawdowns. If your price source cannot serve
  delisted names, say so in your results.
- **This is not an official GPW product** and is not endorsed by GPW Benchmark. It is
  a derived dataset, offered as-is. If your work is commercial or regulatory, license
  the data from the index provider.

## Licence

Code (`wig20.py`, `test_wig20.py`): **MIT**.

Data (`data/*`): released under **CC0 1.0** to the extent we are able to do so. The
underlying facts — which company was a member of a public index on a public date —
are not themselves ours, and in the EU a compiled database may additionally attract
the *sui generis* database right of the compiler. We believe a 31-row quarterly
extract of a single index is not a substantial part of GPW Benchmark's database, but
we are not lawyers. Use accordingly.

## Where this came from

This file is extracted from the backtesting engine behind
[hedgeyourown.com](https://hedgeyourown.com), which publishes systematic model
portfolios with simulated track records on point-in-time universes. The
[methodology page](https://hedgeyourown.com/methodology) documents how the same data
is used there — universes, total-return prices, per-market costs, and the
limitations that remain.

Related, and deliberately not duplicated here: point-in-time **Nasdaq-100**
membership is already well served by
[jmccarrell/n100tickers](https://github.com/jmccarrell/n100tickers) (MIT).

## Contributing

Corrections to the data are the most valuable contribution. If you have a revision
this file gets wrong, open an issue with the revision date and the GPW Benchmark PDF
it came from. Pull requests that extend coverage before 2020 or add special-revision
precision are very welcome — please keep the provenance header accurate.
