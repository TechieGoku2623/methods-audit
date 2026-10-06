"""Write asciinema v2 casts from real CLI stdout. No credentials."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"


def _run(args: list[str]) -> str:
    proc = subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout


def _cast(path: Path, commands: list[list[str]]) -> None:
    header = {
        "version": 2,
        "width": 140,
        "height": 48,
        "timestamp": int(time.time()),
        "env": {"SHELL": "/bin/bash", "TERM": "xterm-256color"},
    }
    events: list[list[object]] = []
    t = 0.05
    for args in commands:
        prompt = "$ " + " ".join(args) + "\r\n"
        events.append([round(t, 3), "o", prompt])
        t += 0.15
        out = _run(args)
        chunk = out.replace("\n", "\r\n")
        events.append([round(t, 3), "o", chunk])
        t += 0.40
        events.append([round(t, 3), "o", "\r\n"])
        t += 0.10
    DEMO.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(header, separators=(",", ":"))]
    lines.extend(json.dumps(ev, separators=(",", ":")) for ev in events)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {path}")


def main() -> None:
    exe = "methods-audit"
    try:
        subprocess.run([exe, "version"], cwd=ROOT, check=True, capture_output=True)
        py = [exe]
    except (subprocess.CalledProcessError, FileNotFoundError):
        py = [sys.executable, "-m", "methods_audit.cli"]
    _cast(
        DEMO / "01-extract-with-spans.cast",
        [py + ["extract", "--paper", "data/sample/complete.xml"]],
    )
    _cast(
        DEMO / "02-consistency-checks.cast",
        [
            py + ["check", "--paper", "data/sample/guide-mismatch.xml"],
            py + ["check", "--paper", "data/sample/bad-cell-line.xml"],
        ],
    )
    _cast(
        DEMO / "03-per-field-eval.cast",
        [[sys.executable, "research/phase0/field_f1/run.py"]],
    )


if __name__ == "__main__":
    main()
