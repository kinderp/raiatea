from __future__ import annotations

import hashlib
import io
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD = ROOT / "build"
sys.path.insert(0, str(BUILD))

import build_evaluator_archive as archive_builder  # noqa: E402


class EvaluatorArchiveTests(unittest.TestCase):
    def test_repeated_builds_are_byte_identical_and_verify(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first_parent = root / "first"
            second_parent = root / "second"
            first = archive_builder.build_evaluator_archive(first_parent, "pilot-1")
            second = archive_builder.build_evaluator_archive(second_parent, "pilot-1")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            extracted = archive_builder.verify_evaluator_archive(first, root / "verified")
            self.assertTrue((extracted / "release-manifest.json").is_file())
            self.assertTrue((extracted / "pilot" / "index.html").is_file())
            self.assertTrue((extracted / "SHA256SUMS").is_file())

    def test_archive_members_and_metadata_are_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive = archive_builder.build_evaluator_archive(Path(temporary), "metadata-1")
            with tarfile.open(archive, "r:") as source:
                members = source.getmembers()
            names = [member.name.rstrip("/") for member in members]
            self.assertEqual(names, sorted(names))
            self.assertEqual(len(names), len(set(names)))
            self.assertTrue(all(name.startswith("raiatea-evaluator-metadata-1") for name in names))
            for member in members:
                self.assertIn(member.type, (tarfile.DIRTYPE, tarfile.REGTYPE))
                self.assertEqual(0, member.mtime)
                self.assertEqual(0, member.uid)
                self.assertEqual(0, member.gid)
                self.assertEqual("", member.uname)
                self.assertEqual("", member.gname)
                self.assertEqual(0o755 if member.isdir() else 0o644, member.mode)

    def test_checksum_inventory_is_sorted_complete_and_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = archive_builder.build_evaluator_archive(root, "checksums-1")
            extracted = archive_builder.verify_evaluator_archive(archive, root / "verify")
            entries = archive_builder._parse_checksums((extracted / "SHA256SUMS").read_text(encoding="ascii"))
            paths = [path for _, path in entries]
            self.assertEqual(paths, sorted(paths))
            self.assertIn("release-manifest.json", paths)
            self.assertIn("pilot/index.html", paths)
            self.assertNotIn("SHA256SUMS", paths)
            for digest, relative in entries:
                self.assertEqual(digest, hashlib.sha256((extracted / relative).read_bytes()).hexdigest())

    def test_tampered_archive_is_rejected_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = archive_builder.build_evaluator_archive(root / "build", "tamper-1")
            tampered = root / "tampered.tar"
            with tarfile.open(archive, "r:") as source, tarfile.open(tampered, "w", format=tarfile.USTAR_FORMAT) as target:
                for member in source.getmembers():
                    data = source.extractfile(member).read() if member.isfile() else None
                    if member.name.endswith("pilot/index.html"):
                        data = (data or b"") + b"tampered"
                        member.size = len(data)
                    target.addfile(member, io.BytesIO(data) if data is not None else None)
            output = root / "verify"
            with self.assertRaisesRegex(ValueError, "checksum|inventory"):
                archive_builder.verify_evaluator_archive(tampered, output)
            self.assertFalse((output / "raiatea-evaluator-tamper-1").exists())

    def test_unsafe_and_link_members_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, member in (
                ("unsafe.tar", tarfile.TarInfo("../escape")),
                ("link.tar", tarfile.TarInfo("raiatea-evaluator-x/link")),
            ):
                archive = root / name
                if name == "unsafe.tar":
                    member.type = tarfile.REGTYPE
                    member.size = 0
                else:
                    member.type = tarfile.SYMTYPE
                    member.linkname = "target"
                with tarfile.open(archive, "w", format=tarfile.USTAR_FORMAT) as target:
                    target.addfile(member, io.BytesIO(b"") if member.isfile() else None)
                with self.assertRaises(ValueError):
                    archive_builder.verify_evaluator_archive(archive, root / f"out-{name}")

    def test_existing_archive_and_verification_destination_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "raiatea-evaluator-existing-1.tar"
            archive.write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already exists"):
                archive_builder.build_evaluator_archive(root, "existing-1")
            self.assertEqual("keep", archive.read_text(encoding="utf-8"))

            good = archive_builder.build_evaluator_archive(root / "good", "verify-1")
            destination_parent = root / "destination"
            destination = destination_parent / "raiatea-evaluator-verify-1"
            destination.mkdir(parents=True)
            marker = destination / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already exists"):
                archive_builder.verify_evaluator_archive(good, destination_parent)
            self.assertEqual("keep", marker.read_text(encoding="utf-8"))

    def test_checksum_parser_fails_closed(self) -> None:
        invalid = (
            "",
            "0" * 64 + "  ../escape\n",
            "g" * 64 + "  pilot/index.html\n",
            "0" * 64 + "  b\n" + "1" * 64 + "  a\n",
            "0" * 64 + "  a\n" + "1" * 64 + "  a\n",
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    archive_builder._parse_checksums(value)


if __name__ == "__main__":
    unittest.main()
