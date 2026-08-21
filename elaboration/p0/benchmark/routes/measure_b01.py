#!/usr/bin/env python3
"""Run the B-01 Poppler control baselines.

Results are benchmark evidence only. Poppler routes in this child are controls,
not production Provider selections, and result records do not define E-05.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
BENCH_DIR = HERE.parent
MANIFEST_DIR = BENCH_DIR / "manifests"
sys.path.insert(0, str(BENCH_DIR))
sys.path.insert(0, str(HERE))

import generate_fixtures  # noqa: E402
from pdf_routes import (  # noqa: E402
    executable_version,
    run_pdftohtml_xml,
    run_pdftotext_bbox_layout,
)
from score_b01 import measure_b01_fixture  # noqa: E402


RESULT_CONTRACT_VERSION = "0.1.0"
TIKA_SURVEYED_VERSION = "3.3.2"
TIKA_APP_SHA512 = (
    "88c2032cba0d45feea361e6eebd2918bd04707614cdda5d89a1b167da5503c98"
    "e7b4cd368336f0402d559abcaf5006fcc7c825c32c749ae0417ea2f3b8423aba"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_fingerprints() -> dict[str, str]:
    paths = {
        "generator": BENCH_DIR / "generate_fixtures.py",
        "fixture_manifest": MANIFEST_DIR / "fixtures.json",
        "gold": MANIFEST_DIR / "gold.json",
        "pdf_routes": HERE / "pdf_routes.py",
        "score_b01": HERE / "score_b01.py",
        "measure_b01": Path(__file__).resolve(),
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


def _structured_provider_setup() -> dict[str, Any]:
    return {
        "policy": (
            "availability/setup evidence only; never convert unavailable/not-installed "
            "into extraction-quality evidence"
        ),
        "apache-tika": {
            "surveyed_version": TIKA_SURVEYED_VERSION,
            "official_release_page": "https://tika.apache.org/3.3.2/",
            "official_download_page": "https://tika.apache.org/download",
            "tika_app_sha512": TIKA_APP_SHA512,
            "execution_status": "not-measured",
            "setup_status": "artifact-not-materialized-in-current-reference-environment",
            "quality_assessment": None,
            "note": (
                "The current environment could not materialize the official Tika app jar "
                "through its available download path. This is setup evidence, not a quality result."
            ),
        },
        "docling": {
            "surveyed_version": "2.117.0",
            "python_module_available": importlib.util.find_spec("docling") is not None,
            "execution_status": "not-measured",
            "quality_assessment": None,
        },
    }


def _write_summary(report: dict[str, Any], path: Path) -> None:
    by_key = {(item["fixture_id"], item["route"]): item for item in report["results"]}

    def dim(result: dict[str, Any], name: str) -> dict[str, Any]:
        return result.get("dimensions", {}).get(name, {})

    lines = [
        "# B-01 PDF Poppler control baseline",
        "",
        "> Benchmark control evidence only. Poppler is not selected as the production Provider.",
        "> The fixture/gold redistribution gate remains open in issue #131.",
        "",
        "## Environment",
        "",
        f"- OS: `{report['environment']['platform_system']} {report['environment']['platform_release']}` `{report['environment']['machine']}`",
        f"- Python: `{report['environment']['python_version']}`",
        f"- pdftotext: `{report['routes']['pdftotext-bbox-layout'].get('version')}`",
        f"- pdftohtml: `{report['routes']['pdftohtml-xml'].get('version')}`",
        f"- pdfinfo: `{report['routes']['pdftohtml-xml'].get('pdfinfo_version')}`",
        "- Timing values are single-run observations only; not performance claims.",
        "",
    ]
    for fixture_id in ["B01-PDF-001", "B01-PDF-002"]:
        lines.extend([f"## {fixture_id}", ""])
        for route in ["pdftotext-bbox-layout", "pdftohtml-xml"]:
            result = by_key.get((fixture_id, route), {})
            if not result:
                continue
            text = dim(result, "content_text")
            coords = dim(result, "source_coordinates")
            order = dim(result, "reading_order")
            lines.append(
                f"- `{route}`: text `{text.get('matched_units')}/{text.get('expected_units')}`, "
                f"coordinates contained `{coords.get('contained_count')}/{coords.get('expected_count')}`, "
                f"reading-order edges `{order.get('satisfied_edges')}/{order.get('expected_edges')}`, "
                f"hierarchy `{dim(result, 'hierarchy').get('status')}`."
            )
        lines.append("")

    lines.extend(
        [
            "## Structured Provider setup status",
            "",
            "- Apache Tika 3.3.2: `not-measured`; official artifact setup was not materialized in this reference environment. This is not a quality failure.",
            f"- Docling 2.117.0 Python module available in this environment: `{report['structured_provider_setup']['docling']['python_module_available']}`; execution remains `not-measured`.",
            "",
            "## Decision boundary",
            "",
            "- Poppler routes are controls for born-digital PDF, not Provider-selection outcomes.",
            "- No weighted/universal score is produced.",
            "- B-01 coverage is incomplete: headings/lists/links, figures/captions, tables, formula/code, defective native text and negative malformed/access-controlled PDF fixtures remain open.",
            "- #131 remains open; G-02 is not complete.",
            "- G-04 and G-05 remain open; no Provider or first slice is selected/promoted.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run_baseline(
    output_dir: Path,
    evidence_source_commit: str | None = None,
    pdftotext_executable: str = "pdftotext",
    pdftohtml_executable: str = "pdftohtml",
    pdfinfo_executable: str = "pdfinfo",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    fixture_dir = output_dir / "fixtures"
    generated = generate_fixtures.generate_all(fixture_dir)
    gold = json.loads((MANIFEST_DIR / "gold.json").read_text(encoding="utf-8"))
    fixture_manifest = json.loads((MANIFEST_DIR / "fixtures.json").read_text(encoding="utf-8"))
    fixtures = {item["id"]: item for item in fixture_manifest["fixtures"]}
    generated_by_id = {item["id"]: item for item in generated["generated"]}

    pdftotext_info = executable_version(pdftotext_executable)
    pdftohtml_info = executable_version(pdftohtml_executable)
    pdfinfo_info = executable_version(pdfinfo_executable)
    routes = {
        "pdftotext-bbox-layout": {
            "route": "pdftotext-bbox-layout",
            "control_route": True,
            "availability": "available" if pdftotext_info.get("version") else "unavailable",
            **pdftotext_info,
            "command_options": ["-bbox-layout"],
            "native_coordinate_system": "top-left-points",
        },
        "pdftohtml-xml": {
            "route": "pdftohtml-xml",
            "control_route": True,
            "availability": (
                "available"
                if pdftohtml_info.get("version") and pdfinfo_info.get("version")
                else "unavailable"
            ),
            **pdftohtml_info,
            "pdfinfo_executable": pdfinfo_info.get("resolved_executable"),
            "pdfinfo_version": pdfinfo_info.get("version"),
            "pdfinfo_executable_sha256": pdfinfo_info.get("executable_sha256"),
            "command_options": ["-xml", "-hidden", "-nodrm", "-q"],
            "native_coordinate_system": "top-left-scaled-canvas",
        },
    }

    results: list[dict[str, Any]] = []
    observations_dir = output_dir / "observations"
    observations_dir.mkdir(exist_ok=True)
    for fixture_id in ["B01-PDF-001", "B01-PDF-002"]:
        fixture_path = fixture_dir / fixtures[fixture_id]["output"]
        gold_fixture = gold["fixtures"][fixture_id]

        if routes["pdftotext-bbox-layout"]["availability"] == "available":
            observation = run_pdftotext_bbox_layout(fixture_path, pdftotext_executable)
            (observations_dir / f"{fixture_id}__pdftotext-bbox-layout.json").write_text(
                json.dumps(observation, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            result = measure_b01_fixture(fixture_id, observation, gold_fixture)
        else:
            result = {
                "fixture_id": fixture_id,
                "route": "pdftotext-bbox-layout",
                "route_status": "not-measured",
                "reason": "pdftotext unavailable in this environment",
            }
        result["fixture_sha256"] = generated_by_id[fixture_id]["sha256"]
        results.append(result)

        if routes["pdftohtml-xml"]["availability"] == "available":
            observation = run_pdftohtml_xml(
                fixture_path,
                pdftohtml_executable,
                pdfinfo_executable,
            )
            (observations_dir / f"{fixture_id}__pdftohtml-xml.json").write_text(
                json.dumps(observation, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            result = measure_b01_fixture(fixture_id, observation, gold_fixture)
        else:
            result = {
                "fixture_id": fixture_id,
                "route": "pdftohtml-xml",
                "route_status": "not-measured",
                "reason": "pdftohtml/pdfinfo unavailable in this environment",
            }
        result["fixture_sha256"] = generated_by_id[fixture_id]["sha256"]
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
        "harness_fingerprints": _file_fingerprints(),
        "rights_state": {
            "redistribution": fixture_manifest["rights_gate"]["redistribution"],
            "decision_issue": fixture_manifest["rights_gate"]["decision_issue"],
            "public_rights_safe": False,
            "remote_provider": "denied",
        },
        "routes": routes,
        "structured_provider_setup": _structured_provider_setup(),
        "results": results,
        "coverage": {
            "benchmark_class": "B-01",
            "normal_fixtures": ["B01-PDF-001", "B01-PDF-002"],
            "full_b01_coverage": False,
            "remaining_gaps": [
                "headings/lists/links",
                "figures/captions",
                "tables",
                "formula/code",
                "defective native text subprofile",
                "malformed/access-controlled negative fixtures",
                "structured generalist Provider measurements such as Docling/Tika",
            ],
        },
        "measurement_limits": [
            "Poppler routes in this child are controls, not production Provider-selection candidates.",
            "Gold coordinate comparison uses page-exact strict containment inside broad reference regions; no universal IoU threshold is introduced.",
            "Hierarchy is not measured because visual/font cues are not promoted to Provider-neutral semantics.",
            "Timing values are single-run observations and are not performance claims.",
            "Provider network traffic is not instrumented; the measured local Poppler tools do not require remote Provider transmission for these fixtures.",
            "Results apply only to the recorded route/version/environment and current minimal fixtures.",
        ],
        "decision_boundary": {
            "provider_selected": False,
            "first_slice_promoted": False,
            "g02_satisfied": False,
            "g04_satisfied": False,
            "g05_satisfied": False,
        },
    }
    (output_dir / "b01-results.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    _write_summary(report, output_dir / "b01-summary.md")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence-source-commit")
    parser.add_argument("--pdftotext", default="pdftotext")
    parser.add_argument("--pdftohtml", default="pdftohtml")
    parser.add_argument("--pdfinfo", default="pdfinfo")
    args = parser.parse_args()
    report = run_baseline(
        args.output.resolve(),
        evidence_source_commit=args.evidence_source_commit,
        pdftotext_executable=args.pdftotext,
        pdftohtml_executable=args.pdftohtml,
        pdfinfo_executable=args.pdfinfo,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
