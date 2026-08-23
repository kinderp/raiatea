#!/usr/bin/env python3
"""Synthetic process that floods stderr before entering the normal protocol loop."""
from __future__ import annotations

import sys

import synthetic_plugin


def main() -> int:
    block = b"synthetic-stderr-flood:" + b"x" * 8170 + b"\n"
    for _ in range(64):
        sys.stderr.buffer.write(block)
    sys.stderr.buffer.flush()
    return synthetic_plugin.run("normal")


if __name__ == "__main__":
    raise SystemExit(main())
