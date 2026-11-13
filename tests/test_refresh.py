"""Contracts the twice-daily refresh must keep.

Run: uv run python -m unittest discover tests
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from jobs import refresh, scoring
from jobs.sources import capital_iq, prices

REPO_DATA = Path(__file__).resolve().parent.parent / "data"
SKIP_ALL_BUT_CIQ_AND_PRICES = [
    "--skip-rss", "--skip-edgar", "--skip-scoring", "--skip-bottleneck",
    "--skip-openrouter", "--skip-exit-triggers", "--skip-transcripts",
    "--skip-narrative", "--skip-tw-universe", "--skip-us-universe",
]


class CiqFailureKeepsPriorFinancials(unittest.TestCase):
    """A bad Capital IQ login must not wipe the financials the last good run
    stored (it did on 2026-07-14, and every run after kept them empty)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="refresh-test-"))
        for name in ("layers.json", "players.json", "ciq_mapping.json", "signals.json"):
            shutil.copy(REPO_DATA / name, self.tmp / name)
        players = json.loads((self.tmp / "players.json").read_text())
        self.tickers = [p["ticker"] for p in players][:2]
        prior = {t: {"long_name": t, "ciq": {"revenue_yoy": 0.5, "pe_trailing": 30.0}}
                 for t in self.tickers}
        (self.tmp / "fundamentals.json").write_text(json.dumps(prior))

    def _run(self, ciq_result):
        fresh_yf = prices.PriceResult(
            prices={t: {"close": 1.0} for t in self.tickers},
            fundamentals={t: {"long_name": t + " Inc"} for t in self.tickers},
        )
        argv = ["refresh", "--tickers", ",".join(self.tickers), *SKIP_ALL_BUT_CIQ_AND_PRICES]
        with mock.patch.object(refresh, "DATA", self.tmp), \
             mock.patch.object(capital_iq, "fetch", return_value=ciq_result), \
             mock.patch.object(prices, "fetch", return_value=fresh_yf), \
             mock.patch.object(sys, "argv", argv):
            self.assertEqual(refresh.main(), 0)
        return json.loads((self.tmp / "fundamentals.json").read_text())

    def test_failed_login_keeps_every_prior_block(self):
        failed = capital_iq.CIQResult(errors={"__connection__": "Incorrect username or password"})
        fund = self._run(failed)
        for t in self.tickers:
            self.assertEqual(fund[t]["ciq"]["revenue_yoy"], 0.5, t)
            self.assertEqual(fund[t]["long_name"], t + " Inc", "yfinance part must still refresh")

    def test_partial_fetch_refreshes_some_and_keeps_the_rest(self):
        a, b = self.tickers
        partial = capital_iq.CIQResult(snapshot={a: {"revenue_yoy": 0.9}}, errors={b: "timeout"})
        fund = self._run(partial)
        self.assertEqual(fund[a]["ciq"], {"revenue_yoy": 0.9})
        self.assertEqual(fund[b]["ciq"]["revenue_yoy"], 0.5)


class ScoringWithoutCiq(unittest.TestCase):
    """With no Capital IQ data at all, scoring must still run on prices and
    signals, not crash (it raised KeyError 'revenue_yoy' from July to November)."""

    def test_compute_on_prices_only(self):
        load = lambda n: json.loads((REPO_DATA / n).read_text())
        fund = {t: {k: v for k, v in f.items() if k != "ciq"}
                for t, f in load("fundamentals.json").items()}
        scores, _status = scoring.compute(
            layers=load("layers.json"), players=load("players.json"),
            fundamentals=fund, prices=load("prices.json"), history={},
            signals=load("signals.json"), manual={},
        )
        self.assertEqual(len(scores), len(load("players.json")))


if __name__ == "__main__":
    unittest.main()
