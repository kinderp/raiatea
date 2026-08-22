from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES = BENCH_DIR / "routes"
sys.path.insert(0, str(ROUTES))
SPEC = importlib.util.spec_from_file_location(
    "p0_poppler_figure_evidence", ROUTES / "poppler_figure_evidence.py"
)
POPPLER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(POPPLER)


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(kind)
    crc = zlib.crc32(payload, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


def _rgb_png(width: int, height: int, pixels: bytes) -> bytes:
    stride = width * 3
    raw = b"".join(
        b"\x00" + pixels[row * stride : (row + 1) * stride]
        for row in range(height)
    )
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        POPPLER.PNG_SIGNATURE
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(raw))
        + _png_chunk(b"IEND", b"")
    )


class PopplerFigureEvidenceTests(unittest.TestCase):
    def test_rgb8_decoder_recovers_authored_pixel_payload(self):
        pixels = bytes(
            [
                255, 0, 0, 0, 255, 0, 0, 0, 255, 255, 255, 0,
                0, 255, 255, 255, 0, 255, 64, 64, 64, 192, 192, 192,
                255, 128, 0, 128, 0, 255, 0, 128, 255, 128, 255, 0,
            ]
        )
        png = _rgb_png(4, 3, pixels)
        width, height, decoded = POPPLER.decode_png_rgb8(png)
        self.assertEqual((width, height), (4, 3))
        self.assertEqual(decoded, pixels)
        self.assertEqual(
            hashlib.sha256(decoded).hexdigest(),
            "2e9756a2943938c833aa0b9d72189577b64146bfdc7ce30957624a762cf5abee",
        )

    def test_decoder_rejects_non_png(self):
        with self.assertRaisesRegex(ValueError, "not-png"):
            POPPLER.decode_png_rgb8(b"not a png")

    def test_controlled_asset_path_accepts_absolute_path_inside_work_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "work"
            work.mkdir()
            asset = work / "out-1_1.png"
            asset.write_bytes(b"png")
            self.assertEqual(
                POPPLER.controlled_asset_path(work, str(asset)), asset.resolve()
            )

    def test_controlled_asset_path_accepts_relative_basename(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "work"
            work.mkdir()
            expected = work / "out-1_1.png"
            self.assertEqual(
                POPPLER.controlled_asset_path(work, "out-1_1.png"), expected.resolve()
            )

    def test_controlled_asset_path_rejects_escape_and_external_absolute_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = root / "work"
            work.mkdir()
            with self.assertRaisesRegex(ValueError, "non-basename-relative-reference"):
                POPPLER.controlled_asset_path(work, "../outside.png")
            with self.assertRaisesRegex(ValueError, "outside-work-root"):
                POPPLER.controlled_asset_path(work, str(root / "outside.png"))


if __name__ == "__main__":
    unittest.main()
