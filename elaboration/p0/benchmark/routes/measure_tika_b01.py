#!/usr/bin/env python3
"""Run the hash-verified Apache Tika 3.3.2 B-01 XHTML baseline.

This is benchmark evidence only. It neither selects Tika nor defines E-05.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
BENCH_DIR = HERE.parent
MANIFEST_DIR = BENCH_DIR / "manifests"
DEFAULT_CONFIG = BENCH_DIR / "config" / "tika-pdf-native-no-ocr.xml"
sys.path.insert(0, str(BENCH_DIR))
sys.path.insert(0, str(HERE))

import generate_fixtures  # noqa: E402
from score_b01 import measure_b01_fixture  # noqa: E402
from tika_routes import (  # noqa: E402
    TIKA_APP_SHA512,
    TIKA_VERSION,
    digest_file,
    run_tika_pdf_xhtml,
    verify_tika_jar,
)


RESULT_CONTRACT_VERSION = "0.1.0"


def _sha256(path: Path) -> str:
    return digest_file(path, "sha256")


def _file_fingerprints(config_path: Path) -> dict[str, str]:
    paths = {
        "generator": BENCH_DIR / "generate_fixtures.py",
        "fixture_manifest": MANIFEST_DIR / "fixtures.json",
        "gold": MANIFEST_DIR / "gold.json",
        "tika_config": config_path,
        "tika_routes": HERE / "tika_routes.py",
        "score_b01": HERE / "score_b01.py",
        "measure_tika_b01": Path(__file__).resolve(),
    }
    return {name: _sha256(path) for name, path in paths.items()}


def _linux_value(path: Path, prefix: str) -> str | None:
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith(prefix):
                return line.split(":", 1)[1].strip()
    except OSError:
        return None
    return None


def _environment() -> dict[str, Any]:
    cpu_model = None
    memory_total = None
    if platform.system() == "Linux":
        cpu_model = _linux_value(Path("/proc/cpuinfo"), "model name")
        memory_total = _linux_value(Path("/proc/meminfo"), "MemTotal")
    return {
        "scope": "single-reference-environment",
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor() or None,
        "cpu_model": cpu_model,
        "logical_cpu_count": os.cpu_count(),
        "memory_total_observed": memory_total,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "gpu": "not-instrumented",
        "portability_claim": False,
    }


def _write_summary(report: dict[str, Any], path: Path) -> None:
    by_fixture = {item["fixture_id"]: item for item in report["results"]}

    def dim(result: dict[str, Any], name: str) -> dict[str, Any]:
        return result.get("dimensions", {}).get(name, {})

    route = report["route"]
    lines = [
        "# B-01 Apache Tika 3.3.2 XHTML reference baseline",
        "",
        "> Benchmark evidence only. Tika is not selected as a production Provider.",
        "> The fixture/gold redistribution gate remains open in issue #131.",
        "",
        "## Environment / route",
        "",
        f"- OS: `{report['environment']['platform_system']} {report['environment']['platform_release']}` `{report['environment']['machine']}`",
        f"- Python: `{report['environment']['python_version']}`",
        f"- Tika: `{route['tika_version']}`",
        f"- Tika jar SHA-256: `{route['jar']['sha256']}`",
        f"- Tika jar SHA-512 verified: `{route['jar']['verified']}`",
        f"- Java: `{route['java'].get('version_line')}`",
        f"- OCR policy: `{route['ocr_policy']}`",
        f"- Config SHA-256: `{route['config_sha256']}`",
        "- Local file input only; no hosted/API route.",
        "- OS-level sandboxing/network isolation are not claimed.",
        "",
    ]
    for fixture_id in ["B01-PDF-001", "B01-PDF-002"]:
        result = by_fixture.get(fixture_id, {})
        text = dim(result, "content_text")
        order = dim(result, "reading_order")
        coords = dim(result, "source_coordinates")
        hierarchy = dim(result, "hierarchy")
        lines.extend(
            [
                f"## {fixture_id}",
                "",
                f"- route status: `{result.get('route_status')}`",
                f"- exact reference text units: `{text.get('matched_units')}/{text.get('expected_units')}`",
                f"- reading-order edges: `{order.get('satisfied_edges')}/{order.get('expected_edges')}`",
                f"- source coordinates: `{coords.get('status')}`",
                f"- hierarchy: `{hierarchy.get('status')}`; exact semantic types `{hierarchy.get('type_exact_count')}/{hierarchy.get('expected_count')}` when measurable",
                f"- raw XHTML SHA-256: `{result.get('raw_output_sha256')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation boundary",
            "",
            "- Missing page/bbox evidence is reported as `not-measured`/`partial`, never as successful geometry and never as an invented zero score.",
            "- Explicit XHTML tags may provide hierarchy evidence; visual/font cues are not promoted to semantic structure.",
            "- No weighted/universal score is produced.",
            "- Comparison with Poppler controls is limited to dimensions measured by both routes.",
            "- B-01 coverage remains incomplete and #131/G-02/G-04/G-05/first-slice promotion remain open.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run_baseline(
    output_dir: Path,
    jar_path: Path,
    config_path: Path = DEFAULT_CONFIG,
    java_executable: str = "java",
    evidence_source_commit: str | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    fixture_dir = output_dir / "fixtures"
    generated = generate_fixtures.generate_all(fixture_dir)
    fixture_manifest = json.loads((MANIFEST_DIR / "fixtures.json").read_text(encoding="utf-8"))
    gold = json.loads((MANIFEST_DIR / "gold.json").read_text(encoding="utf-8"))
    fixtures = {item["id"]: item for item in fixture_manifest["fixtures"]}
    generated_by_id = {item["id"]: item for item in generated["generated"]}

    jar_evidence = verify_tika_jar(jar_path)
    if not jar_evidence["verified"]:
        raise ValueError(
            "Tika artifact must match the pinned official SHA-512 before baseline execution"
        )

    results: list[dict[str, Any]] = []
    observations_dir = output_dir / "observations"
    observations_dir.mkdir(exist_ok=True)
    route_java: dict[str, Any] | None = None
    for fixture_id in ["B01-PDF-001", "B01-PDF-002"]:
        fixture_path = fixture_dir / fixtures[fixture_id]["output"]
        observation = run_tika_pdf_xhtml(
            fixture_path,
            jar_path,
            config_path,
            java_executable=java_executable,
        )
        (observations_dir / f"{fixture_id}__tika-app-3.3.2-xhtml.json").write_text(
            json.dumps(observation, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        if observation.get("java") is not None:
            route_java = observation["java"]
        result = measure_b01_fixture(fixture_id, observation, gold["fixtures"][fixture_id])
        result["fixture_sha256"] = generated_by_id[fixture_id]["sha256"]
        result["page_structure_observed"] = observation.get("page_structure_observed")
        result["bbox_structure_observed"] = observation.get("bbox_structure_observed")
        result["metadata_key_count"] = len(observation.get("metadata", {}))
        results.append(result)

    report = {
        "contract": {
            "name": "raiatea-p0-benchmark-result",
            "version": RESULT_CONTRACT_VERSION,
            "scope": "benchmark-evidence-only",
            "public_p0_schema": False,
            "no_universal_total_score": True,
        },
        "evidence_source_commit": evidence_source_commit,
        "environment": _environment(),
        "harness_fingerprints": _file_fingerprints(config_path),
        "rights_state": {
            "redistribution": fixture_manifest["rights_gate"]["redistribution"],
            "decision_issue": fixture_manifest["rights_gate"]["decision_issue"],
            "public_rights_safe": False,
            "remote_provider": "denied",
        },
        "route": {
            "route": "tika-app-3.3.2-xhtml",
            "tika_version": TIKA_VERSION,
            "jar": jar_evidence,
            "java": route_java,
            "config_path": str(config_path),
            "config_sha256": _sha256(config_path),
            "ocr_policy": "explicit-no-ocr",
            "command_semantics": [
                "java",
                "-Djava.io.tmpdir=<controlled>",
                "-jar",
                "<verified-tika-app-3.3.2.jar>",
                "--config=<pinned-no-ocr-config>",
                "-x",
                "<local-fixture.pdf>",
            ],
            "hosted_or_remote": False,
            "access_control_override": False,
            "network_instrumentation": "not-measured",
            "os_level_sandbox": False,
        },
        "results": results,
        "comparison_controls": {
            "reference_commit": "add6bbe0757848d66d17a364f8566985eef21c60",
            "note": (
                "Poppler B-01 controls are canonical in E-04c. This Tika child does not "
                "rerun/rewrite them; comparison is limited to common measured dimensions."
            ),
        },
        "coverage": {
            "benchmark_class": "B-01",
            "normal_fixtures": ["B01-PDF-001", "B01-PDF-002"],
            "full_b01_coverage": False,
            "remaining_gaps": [
                "headings/lists/links fixture",
                "figures/captions",
                "tables",
                "formula/code",
                "defective native text subprofile",
                "malformed/access-controlled negative fixtures",
                "Docling and other structured Provider measurements",
            ],
        },
        "measurement_limits": [
            "Tika XHTML is mapped conservatively; absent page/geometry semantics are not fabricated.",
            "OCR is explicitly disabled for this born-digital route through the pinned Tika config and Tesseract parser exclusion.",
            "Timing values are single-run observations and are not performance claims.",
            "Java runs in a controlled temporary input/work/tmp parent; OS-level filesystem/network isolation is not claimed.",
            "Results apply only to the recorded jar/config/runtime/environment and current minimal fixtures.",
        ],
        "decision_boundary": {
            "provider_selected": False,
            "first_slice_promoted": False,
            "g02_satisfied": False,
            "g04_satisfied": False,
            "g05_satisfied": False,
        },
    }
    (output_dir / "tika-b01-results.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    _write_summary(report, output_dir / "tika-b01-summary.md")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tika-jar", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--java", default="java")
    parser.add_argument("--evidence-source-commit")
    args = parser.parse_args()
    report = run_baseline(
        args.output.resolve(),
        args.tika_jar.resolve(),
        args.config.resolve(),
        java_executable=args.java,
        evidence_source_commit=args.evidence_source_commit,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
