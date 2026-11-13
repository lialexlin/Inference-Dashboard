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


class RefreshKeepsPriorData(unittest.TestCase):
    """A failed source must not wipe what the last good run stored. A bad
    Capital IQ login did exactly that on 2026-07-14, and every run after kept
    the financials empty."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="refresh-test-")
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        for name in ("layers.json", "players.json", "signals.json"):
            shutil.copy(REPO_DATA / name, self.tmp / name)
        players = json.loads((self.tmp / "players.json").read_text())
        self.a, self.b = [p["ticker"] for p in players][:2]
        mapping = {self.a: {"company_id": 1}, self.b: {"company_id": 2}}
        (self.tmp / "ciq_mapping.json").write_text(json.dumps(mapping))
        prior = {t: {"long_name": t, "ciq": {"revenue_yoy": 0.5}} for t in (self.a, self.b)}
        prior["GONE"] = {"long_name": "dropped from PLAYERS", "ciq": {"revenue_yoy": 9.9}}
        (self.tmp / "fundamentals.json").write_text(json.dumps(prior))
        (self.tmp / "prices.json").write_text(json.dumps({self.a: {"close": 7.0}, self.b: {"close": 8.0}}))

    def _run(self, ciq_result, price_result=None, mapping=None):
        if mapping is not None:
            (self.tmp / "ciq_mapping.json").write_text(json.dumps(mapping))
        if price_result is None:
            price_result = prices.PriceResult(
                prices={t: {"close": 1.0} for t in (self.a, self.b)},
                fundamentals={t: {"long_name": t + " Inc"} for t in (self.a, self.b)},
            )
        argv = ["refresh", "--tickers", f"{self.a},{self.b}", *SKIP_ALL_BUT_CIQ_AND_PRICES]
        with mock.patch.object(refresh, "DATA", self.tmp), \
             mock.patch.object(capital_iq, "fetch", return_value=ciq_result), \
             mock.patch.object(prices, "fetch", return_value=price_result), \
             mock.patch.object(sys, "argv", argv):
            self.assertEqual(refresh.main(), 0)
        load = lambda n: json.loads((self.tmp / n).read_text())
        return load("fundamentals.json"), load("prices.json"), load("meta.json")

    def test_failed_login_keeps_every_prior_block(self):
        failed = capital_iq.CIQResult(errors={"__connection__": "Incorrect username or password"})
        fund, _, meta = self._run(failed)
        for t in (self.a, self.b):
            self.assertEqual(fund[t]["ciq"]["revenue_yoy"], 0.5, t)
            self.assertEqual(fund[t]["long_name"], t + " Inc", "yfinance part must still refresh")
        self.assertIn("ciq", meta["broken_stages"])

    def test_partial_fetch_refreshes_some_and_keeps_the_rest(self):
        partial = capital_iq.CIQResult(snapshot={self.a: {"revenue_yoy": 0.9}}, errors={self.b: "timeout"})
        fund, _, meta = self._run(partial)
        self.assertEqual(fund[self.a]["ciq"], {"revenue_yoy": 0.9})
        self.assertEqual(fund[self.b]["ciq"]["revenue_yoy"], 0.5)
        self.assertNotIn("broken_stages", meta)

    def test_untracked_or_unmapped_ticker_loses_its_block(self):
        failed = capital_iq.CIQResult(errors={"__connection__": "x"})
        fund, _, _ = self._run(failed, mapping={self.a: {"company_id": 1}, self.b: {"company_id": None}})
        self.assertNotIn("ciq", fund.get("GONE", {}))
        self.assertNotIn("ciq", fund[self.b])
        self.assertEqual(fund[self.a]["ciq"]["revenue_yoy"], 0.5)

    def test_blocked_yahoo_keeps_prior_prices_and_names(self):
        blocked = prices.PriceResult(errors={self.a: "no history", self.b: "no history"})
        fund, px, meta = self._run(capital_iq.CIQResult(snapshot={}), price_result=blocked)
        self.assertEqual(px[self.a], {"close": 7.0})
        self.assertEqual(fund[self.b]["long_name"], self.b)
        self.assertIn("prices", meta["broken_stages"])


class BrokenStages(unittest.TestCase):
    STARTED = "2026-11-13T00:00:00+00:00"
    NOW = "2026-11-13T00:05:00+00:00"
    EARLIER = "2026-11-12T00:05:00+00:00"

    def test_rules(self):
        down = {"ok": 0, "errors": {"__stage__": "403"}, "ts": self.NOW}
        sources = {
            "ciq": {"ok": 0, "errors": {"__connection__": "bad login"}, "ts": self.NOW},
            "prices": {"ok": 61, "errors": {"6967.T": "delisted"}, "ts": self.NOW},
            "transcripts": {"ok": 0, "errors": {"MU": "301", "AMD": "301"}, "ts": self.NOW},
            "scoring": {"ok": 0, "errors": {"__stage__": "old"}, "ts": self.EARLIER},
            "tw_universe": down,
            "us_universe": down,
        }
        prev = {"us_universe": {"ok": 0, "errors": {"__stage__": "403"}}}
        broken = refresh.broken_stages(sources, prev, self.STARTED)
        self.assertEqual(set(broken), {"ciq", "transcripts", "us_universe"},
                         "per-item noise, carried-forward blocks and a first flaky failure stay green")


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
        self.assertTrue(scores)


if __name__ == "__main__":
    unittest.main()
