#!/usr/bin/env python3
"""Measure B01 negative PDF fixtures without normalizing Provider outcomes yet.

This is the evidence-first raw stage for B01-PDF-NEG-001/002. qpdf is used
only to materialize the deterministic access-controlled fixture. The measured
Provider receives the resulting PDF path only: no fixture password, decrypt
option, access-control override, password guess/recovery, or remote Provider is
used by this runner.

Raw rejection/failure/degradation is expected benchmark evidence and must not be
converted into synthetic success merely to keep CI green.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

HERE = Path(__file__).resolve().parent
BENCH_DIR = HERE.parent
sys.path.insert(0, str(BENCH_DIR))
sys.path.insert(0, str(HERE))

import b01_pdf_negative_fixtures as fixtures  # noqa: E402

GOLD_PATH = BENCH_DIR / "manifests" / "b01-pdf-negative-gold.json"
FIXTURE_IDS = (fixtures.NEG_MALFORMED_ID, fixtures.NEG_ACCESS_CONTROLLED_ID)

# Provider processing options only. Generator-only qpdf options/passwords are
# deliberately audited in a separate namespace and never passed to Providers.
FORBIDDEN_PROVIDER_OPTION_PREFIXES = (
    "-nodrm",
    "--password",
    "--decrypt",
    "--remove-restrictions",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _flatten_provider_options(observation: dict[str, Any]) -> list[str]:
    values: list[str] = []
    command_options = observation.get("command_options")
    if isinstance(command_options, list):
        values.extend(str(item) for item in command_options)
    route_options = observation.get("route_options")
    if isinstance(route_options, dict):
        for key, value in sorted(route_options.items()):
            values.append(f"{key}={value}")
    return values


def audit_provider_invocation(observation: dict[str, Any]) -> dict[str, Any]:
    options = _flatten_provider_options(observation)
    forbidden_hits: list[str] = []
    for option in options:
        normalized = option.strip().lower()
        for prefix in FORBIDDEN_PROVIDER_OPTION_PREFIXES:
            if normalized == prefix or normalized.startswith(prefix + "="):
                forbidden_hits.append(option)
    return {
        "provider_options": options,
        "fixture_password_supplied_to_provider": False,
        "access_control_bypass_requested": bool(forbidden_hits),
        "forbidden_option_hits": forbidden_hits,
        "audit_passed": not forbidden_hits,
        "policy": (
            "Provider receives only local fixture path plus its already-pinned normal route options; "
            "generator-only qpdf passwords/static options are outside this audit namespace."
        ),
    }


def materialize_negative_fixtures(root: Path, qpdf_executable: str) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    malformed = fixtures.build_malformed_pdf()
    (root / f"{fixtures.NEG_MALFORMED_ID}.pdf").write_bytes(malformed)
    protected, generator = fixtures.generate_access_controlled_pdf(qpdf_executable)
    (root / f"{fixtures.NEG_ACCESS_CONTROLLED_ID}.pdf").write_bytes(protected)

    gold = _load_json(GOLD_PATH)["fixtures"]
    records = []
    for fixture_id, payload in (
        (fixtures.NEG_MALFORMED_ID, malformed),
        (fixtures.NEG_ACCESS_CONTROLLED_ID, protected),
    ):
        record = fixtures.fixture_record(fixture_id, payload)
        expected = gold[fixture_id]
        if record["sha256"] != expected["sha256"] or record["bytes"] != expected["bytes"]:
            raise RuntimeError(
                f"negative-fixture-identity-drift:{fixture_id}:"
                f"{record['sha256']}/{record['bytes']} != {expected['sha256']}/{expected['bytes']}"
            )
        records.append(record)
    return {
        "fixtures": records,
        "access_controlled_generator": generator,
        "provider_password_supplied": False,
        "provider_bypass_allowed": False,
    }


def _result_row(fixture_id: str, observation: dict[str, Any]) -> dict[str, Any]:
    audit = audit_provider_invocation(observation)
    if not audit["audit_passed"]:
        raise RuntimeError(
            f"provider-invocation-policy-violation:{fixture_id}:{audit['forbidden_option_hits']}"
        )
    return {
        "fixture_id": fixture_id,
        "observation": observation,
        "provider_invocation_audit": audit,
    }


def run_poppler(source_root: Path) -> list[dict[str, Any]]:
    from pdf_routes import run_pdftohtml_xml, run_pdftotext_bbox_layout

    rows = []
    for fixture_id in FIXTURE_IDS:
        source = source_root / f"{fixture_id}.pdf"
        rows.append(_result_row(fixture_id, run_pdftotext_bbox_layout(source)))
        rows.append(_result_row(fixture_id, run_pdftohtml_xml(source)))
    return rows


def run_tika(
    source_root: Path,
    tika_jar: Path,
    config: Path,
    java_executable: str,
) -> list[dict[str, Any]]:
    from tika_routes import run_tika_pdf_xhtml

    rows = []
    for fixture_id in FIXTURE_IDS:
        source = source_root / f"{fixture_id}.pdf"
        observation = run_tika_pdf_xhtml(
            source,
            jar_path=tika_jar,
            config_path=config,
            java_executable=java_executable,
        )
        rows.append(_result_row(fixture_id, observation))
    return rows


def run_docling(
    source_root: Path,
    artifacts_path: Path,
    cache_root: Path,
) -> list[dict[str, Any]]:
    from docling_routes import run_docling_pdf_json

    rows = []
    for fixture_id in FIXTURE_IDS:
        source = source_root / f"{fixture_id}.pdf"
        fixture_cache = cache_root / fixture_id
        observation = run_docling_pdf_json(source, artifacts_path, fixture_cache)
        # Raw exported Provider data is useful evidence but duplicated inside the
        # observation. Keep it in this raw report; the later compact durable
        # baseline will fingerprint rather than reproduce large payloads.
        rows.append(_result_row(fixture_id, observation))
    return rows


def run(
    provider: str,
    output: Path,
    qpdf_executable: str,
    evidence_source_commit: str | None,
    tika_jar: Path | None = None,
    config: Path | None = None,
    java_executable: str = "java",
    artifacts_path: Path | None = None,
    cache_root: Path | None = None,
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="raiatea-b01-negative-fixtures-") as tmp:
        source_root = Path(tmp)
        generation = materialize_negative_fixtures(source_root, qpdf_executable)
        if provider == "poppler":
            rows = run_poppler(source_root)
        elif provider == "tika":
            if tika_jar is None or config is None:
                raise ValueError("tika requires --tika-jar and --config")
            rows = run_tika(source_root, tika_jar, config, java_executable)
        elif provider == "docling":
            if artifacts_path is None or cache_root is None:
                raise ValueError("docling requires --artifacts-path and --cache-root")
            rows = run_docling(source_root, artifacts_path, cache_root)
        else:
            raise ValueError(f"unsupported provider family: {provider}")

    payload = {
        "contract": {
            "name": "raiatea-p0-b01-negative-raw-evidence",
            "version": "0.1.0",
            "scope": "benchmark-evidence-only",
            "public_p0_schema": False,
            "negative_security_fixtures": True,
            "excluded_from_normal_quality_averages": True,
            "raw_before_normalization": True,
        },
        "evidence_source_commit": evidence_source_commit,
        "provider_family": provider,
        "fixture_generation": generation,
        "provider_password_supplied": False,
        "access_control_bypass_allowed": False,
        "results": rows,
    }
    _write_json(output / f"b01-negative-{provider}-raw.json", payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="provider", required=True)
    for name in ("poppler", "tika", "docling"):
        child = sub.add_parser(name)
        child.add_argument("--output", type=Path, required=True)
        child.add_argument("--qpdf", default="qpdf")
        child.add_argument("--evidence-source-commit")
        if name == "tika":
            child.add_argument("--tika-jar", type=Path, required=True)
            child.add_argument("--config", type=Path, required=True)
            child.add_argument("--java", default="java")
        if name == "docling":
            child.add_argument("--artifacts-path", type=Path, required=True)
            child.add_argument("--cache-root", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    kwargs: dict[str, Any] = {
        "provider": args.provider,
        "output": args.output.resolve(),
        "qpdf_executable": args.qpdf,
        "evidence_source_commit": args.evidence_source_commit,
    }
    if args.provider == "tika":
        kwargs.update(
            tika_jar=args.tika_jar.resolve(),
            config=args.config.resolve(),
            java_executable=args.java,
        )
    elif args.provider == "docling":
        kwargs.update(
            artifacts_path=args.artifacts_path.resolve(),
            cache_root=args.cache_root.resolve(),
        )
    run(**kwargs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
