"""Guards for the repo-wide rules a refactor must not undo.

Run: uv run python -m unittest discover tests
"""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOBS = ROOT / "jobs"


def _calls(attr: str, dirs=(JOBS,)):
    """(path:line, call) for every `.attr(...)` call under `dirs`."""
    for p in sorted(f for d in dirs for f in d.rglob("*.py")):
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == attr:
                yield f"{p.relative_to(ROOT).as_posix()}:{node.lineno}", node


class OneJsonWriter(unittest.TestCase):
    def test_only_jobs_io_writes_json_files(self):
        """A second writer drifts from the first (the four copies did) and
        loses the UTF-8 and temp-file guarantees. Use jobs.io.write_json."""
        offenders = [
            where for where, call in _calls("write_text")
            if not where.startswith("jobs/io.py")
            and any(isinstance(a, ast.Call) and getattr(a.func, "attr", "") == "dumps" for a in ast.walk(call))
        ]
        self.assertEqual(offenders, [])

    def test_written_json_is_utf8_under_an_ascii_locale(self):
        """refresh.cmd runs on Windows, whose default code page cannot hold a
        Taiwan company name; an ASCII locale reproduces that on any OS."""
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "x.json"
            env = {**os.environ, "LC_ALL": "C", "LANG": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"}
            subprocess.run(
                [sys.executable, "-c", "import sys; from pathlib import Path; from jobs.io import write_json; "
                 "write_json(Path(sys.argv[1]), {'name': '台積電'})", str(out)],
                cwd=ROOT, env=env, check=True, capture_output=True,
            )
            self.assertEqual(json.loads(out.read_bytes().decode("utf-8")), {"name": "台積電"})
            self.assertEqual([p.name for p in Path(d).iterdir()], ["x.json"])


class TextIoIsUtf8(unittest.TestCase):
    def test_every_read_text_and_write_text_names_utf8(self):
        offenders = [
            where for attr in ("read_text", "write_text") for where, call in _calls(attr, (JOBS, ROOT / "tests"))
            if not any(k.arg == "encoding" for k in call.keywords)
        ]
        self.assertEqual(offenders, [])


class PinnedVersions(unittest.TestCase):
    def test_every_cdn_script_names_an_exact_version(self):
        """An unversioned CDN URL silently swaps the library under the pages."""
        offenders = []
        for p in sorted(ROOT.glob("*.html")):
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                for url in re.findall(r'<script[^>]*\bsrc="(https?://[^"]+)"', line):
                    if not re.search(r"[@/]\d+\.\d+\.\d+(/|$)", url):
                        offenders.append(f"{p.name}:{n} {url}")
        self.assertEqual(offenders, [])

    def test_uv_lock_is_committed(self):
        git = lambda *a: subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True)
        self.assertEqual(git("check-ignore", "-q", "--no-index", "uv.lock").returncode, 1, "uv.lock is gitignored")
        self.assertEqual(git("ls-files", "--error-unmatch", "uv.lock").returncode, 0, "uv.lock is not tracked")


if __name__ == "__main__":
    unittest.main()
