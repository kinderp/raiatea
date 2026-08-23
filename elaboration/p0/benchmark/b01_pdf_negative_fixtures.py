#!/usr/bin/env python3
"""Build bounded B01 PDF negative/security fixtures.

This module creates test data only. It never opens, decrypts, guesses passwords
for, or bypasses access control on an input document.

`B01-PDF-NEG-001` is a deliberately truncated project-created PDF.
`B01-PDF-NEG-002` is generated from a project-created valid source using qpdf
with a fixed fixture-only password and qpdf's test-only static ID/AES-IV options
so byte reproducibility can be verified before Provider measurement.

The fixture password is not a secret; the security assertion is that measured
Provider routes receive no password and no access-control override/circumvention
option. The static qpdf options are generator-only and must never be copied into
production processing policy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any

NEG_MALFORMED_ID = "B01-PDF-NEG-001"
NEG_ACCESS_CONTROLLED_ID = "B01-PDF-NEG-002"
GENERATOR_VERSION = "0.2.0"

# Fixture-only values. They are intentionally public test inputs, not credentials
# that any measured Provider route is allowed to receive.
FIXTURE_USER_PASSWORD = "raiatea-fixture-user"
FIXTURE_OWNER_PASSWORD = "raiatea-fixture-owner"

QPDF_GENERATOR_OPTIONS = ("--static-id", "--static-aes-iv")
QPDF_ENCRYPT_BITS = "128"
QPDF_ENCRYPT_OPTIONS = ("--use-aes=y",)


def _pdf_object(number: int, payload: bytes) -> bytes:
    return f"{number} 0 obj\n".encode("ascii") + payload + b"\nendobj\n"


def build_valid_source_pdf() -> bytes:
    """Return a small deterministic valid PDF used only as fixture source."""
    stream = b"BT /F1 18 Tf 72 710 Td (Raiatea negative fixture control) Tj ET\n"
    objects = [
        _pdf_object(1, b"<< /Type /Catalog /Pages 2 0 R >>"),
        _pdf_object(2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"),
        _pdf_object(
            3,
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        ),
        _pdf_object(
            4,
            f"<< /Length {len(stream)} >>\nstream\n".encode("ascii")
            + stream
            + b"endstream",
        ),
        _pdf_object(5, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"),
    ]

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    body = bytearray(header)
    offsets = [0]
    for obj in objects:
        offsets.append(len(body))
        body.extend(obj)

    xref_offset = len(body)
    body.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    body.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        body.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    body.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(body)


def build_malformed_pdf() -> bytes:
    """Return a deterministic, inert, visibly truncated PDF container."""
    source = build_valid_source_pdf()
    marker = b"endstream"
    index = source.find(marker)
    if index < 0:
        raise RuntimeError("valid-source-stream-marker-missing")
    return source[: index - 7] + b"\n% deterministic intentional truncation\n"


def access_controlled_qpdf_command(
    qpdf_executable: str, source: Path, output: Path
) -> list[str]:
    """Return generator-only qpdf invocation for the encrypted test fixture."""
    return [
        qpdf_executable,
        *QPDF_GENERATOR_OPTIONS,
        "--encrypt",
        FIXTURE_USER_PASSWORD,
        FIXTURE_OWNER_PASSWORD,
        QPDF_ENCRYPT_BITS,
        *QPDF_ENCRYPT_OPTIONS,
        "--",
        str(source),
        str(output),
    ]


def generate_access_controlled_pdf(
    qpdf_executable: str = "qpdf",
) -> tuple[bytes, dict[str, Any]]:
    """Generate NEG-002 twice and require byte-for-byte reproducibility.

    AES-128 is used explicitly for this fixture because, with the qpdf test-only
    static document ID and static AES IV, the small test file can be reproduced
    byte-for-byte. This is *not* production cryptographic guidance. The measured
    benchmark routes receive neither the fixture password nor these generator
    options.
    """
    plain = build_valid_source_pdf()
    with tempfile.TemporaryDirectory(prefix="raiatea-b01-neg-access-") as tmp:
        root = Path(tmp)
        source = root / "source.pdf"
        first = root / "first.pdf"
        second = root / "second.pdf"
        source.write_bytes(plain)

        commands = []
        for output in (first, second):
            command = access_controlled_qpdf_command(qpdf_executable, source, output)
            commands.append(command)
            completed = subprocess.run(
                command,
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    "qpdf-fixture-generation-failed:"
                    f"exit={completed.returncode}:stderr={completed.stderr.strip()}"
                )
            if not output.is_file():
                raise RuntimeError("qpdf-fixture-output-missing")

        first_bytes = first.read_bytes()
        second_bytes = second.read_bytes()
        if first_bytes != second_bytes:
            raise RuntimeError(
                "qpdf-access-controlled-output-not-byte-reproducible; "
                "do not measure Providers until the generator is hardened"
            )
        return first_bytes, {
            "generator": "qpdf",
            "generator_options": list(QPDF_GENERATOR_OPTIONS),
            "encryption_bits": int(QPDF_ENCRYPT_BITS),
            "encryption_options": list(QPDF_ENCRYPT_OPTIONS),
            "fixture_password_supplied_to_generator_only": True,
            "provider_password_policy": "must-not-be-supplied",
            "provider_bypass_policy": "must-not-be-used",
            "reproducibility_check": "two-independent-generation-bytes-identical",
            "commands_redacted": [
                [
                    item
                    if item not in {FIXTURE_USER_PASSWORD, FIXTURE_OWNER_PASSWORD}
                    else "<fixture-generator-password>"
                    for item in command
                ]
                for command in commands
            ],
        }


def fixture_record(fixture_id: str, payload: bytes, **extra: Any) -> dict[str, Any]:
    return {
        "id": fixture_id,
        "generator_version": GENERATOR_VERSION,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        **extra,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--qpdf", default="qpdf")
    parser.add_argument("--include-access-controlled", action="store_true")
    args = parser.parse_args()

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    malformed = build_malformed_pdf()
    (output / f"{NEG_MALFORMED_ID}.pdf").write_bytes(malformed)
    records = [
        fixture_record(
            NEG_MALFORMED_ID,
            malformed,
            source_family="B-01",
            expected_class="rejected-or-visible-degraded-failure",
            excluded_from_quality_average=True,
            corruption="truncated-content-stream-no-xref-no-trailer-no-eof",
        )
    ]

    if args.include_access_controlled:
        protected, generator = generate_access_controlled_pdf(args.qpdf)
        (output / f"{NEG_ACCESS_CONTROLLED_ID}.pdf").write_bytes(protected)
        records.append(
            fixture_record(
                NEG_ACCESS_CONTROLLED_ID,
                protected,
                source_family="B-01",
                expected_class="restricted-unsupported-or-visible-failure",
                excluded_from_quality_average=True,
                access_control="password-encrypted",
                provider_password_supplied=False,
                provider_bypass_allowed=False,
                generator_evidence=generator,
            )
        )

    manifest = {
        "contract": {
            "name": "raiatea-p0-b01-negative-fixture-generation",
            "version": GENERATOR_VERSION,
            "scope": "benchmark-evidence-only",
            "public_p0_schema": False,
        },
        "fixtures": records,
    }
    (output / "generated-negative-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
