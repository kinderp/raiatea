#!/usr/bin/env python3
"""Post-process raw B01 negative Provider evidence conservatively."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from score_b01_negative import score_raw_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads(args.input.read_text(encoding="utf-8"))
    scored = score_raw_report(raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(scored, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(scored, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
