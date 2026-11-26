"""No launcher may serve the dashboard beyond this machine: `http.server`
listens on every interface unless it is told otherwise.

Run: uv run python -m unittest discover tests
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Everything that starts a server or tells a person how to, one command a line.
PATTERNS = ("*.command", "*.cmd", "*.sh", "*.bat", "*.ps1", ".claude/launch.json",
            ".claude/skills/*/SKILL.md", "*.html")


class ServersStayOnThisMachine(unittest.TestCase):
    def test_every_http_server_command_binds_loopback(self):
        files = {p for pattern in PATTERNS for p in ROOT.glob(pattern)}
        self.assertLessEqual({ROOT / "launch.command", ROOT / "launch.cmd"}, files)
        for path in sorted(files):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                # flatten JSON argument arrays into the command they spell
                command = re.sub(r'[",\s]+', " ", line)
                with self.subTest(file=str(path.relative_to(ROOT)), line=number):
                    self.assertNotIn("0.0.0.0", command)
                    if "-m http.server" in command:
                        self.assertRegex(command, r"--bind 127\.0\.0\.1(?![\d.])")


if __name__ == "__main__":
    unittest.main()
