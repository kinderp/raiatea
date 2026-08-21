#!/usr/bin/env python3
"""Run the B-02 direct EPUB and local Pandoc baseline routes.

Results are benchmark evidence only. They do not select a production Provider
and do not define the future P0 Processing Run or Normalized Representation
schemas.
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
sys.path.insert(0, str(BENCH_DIR))
sys.path.insert(0, str(HERE))

import generate_fixtures  # noqa: E402
from epub_routes import pandoc_version, parse_direct_epub, run_pandoc_epub  # noqa: E402
from score_b02 import measure_negative_fixture, measure_normal_fixture  # noqa: E402


RESULT_CONTRACT_VERSION = "0.1.0"
E02_SURVEYED_PANDOC_VERSION = "3.10.2"


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
        "epub_routes": HERE / "epub_routes.py",
        "score_b02": HERE / "score_b02.py",
        "measure_b02": Path(__file__).resolve(),
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
    results = report["results"]
    by_key = {(r["fixture_id"], r["route"]): r for r in results}
    direct_1 = by_key.get(("B02-EPUB-001", "direct-epub-stdlib"), {})
    pandoc_1 = by_key.get(("B02-EPUB-001", "pandoc-epub"), {})
    direct_2 = by_key.get(("B02-EPUB-002", "direct-epub-stdlib"), {})
    pandoc_2 = by_key.get(("B02-EPUB-002", "pandoc-epub"), {})
    pandoc_route = report["routes"]["pandoc-epub"]

    def dim(result: dict[str, Any], name: str) -> dict[str, Any]:
        return result.get("dimensions", {}).get(name, {})

    lines = [
        "# B-02 EPUB reference-environment baseline",
        "",
        "> Benchmark evidence only. No Provider is selected and no first slice is promoted.",
        "> The fixture/gold redistribution gate remains open in issue #131.",
        "",
        "## Environment",
        "",
        f"- OS: `{report['environment']['platform_system']} {report['environment']['platform_release']}` `{report['environment']['machine']}`",
        f"- Python: `{report['environment']['python_version']}`",
        f"- Pandoc measured: `{pandoc_route.get('version')}`",
        f"- Pandoc E-02 surveyed: `{pandoc_route.get('surveyed_version')}`",
        f"- Version match: `{pandoc_route.get('surveyed_version_match')}`",
        "- Timing: single-run observations only; not performance claims.",
        "",
        "## B02-EPUB-001 — spine/text/anchors",
        "",
    ]
    if direct_1:
        coords = dim(direct_1, "source_coordinates")
        lines.append(
            f"- direct stdlib: text `{dim(direct_1, 'content_text').get('matched_units')}/{dim(direct_1, 'content_text').get('expected_units')}`, "
            f"coordinate full-exact `{coords.get('full_exact_count')}/{coords.get('expected_count')}`, "
            f"reading-order edges `{dim(direct_1, 'reading_order').get('satisfied_edges')}/{dim(direct_1, 'reading_order').get('expected_edges')}`."
        )
    if pandoc_1:
        coords = dim(pandoc_1, "source_coordinates")
        lines.append(
            f"- Pandoc: text `{dim(pandoc_1, 'content_text').get('matched_units')}/{dim(pandoc_1, 'content_text').get('expected_units')}`, "
            f"coordinate full-exact `{coords.get('full_exact_count')}/{coords.get('expected_count')}`, "
            f"traceable `{coords.get('traceable_count')}/{coords.get('expected_count')}`; paragraph authored fragments are not preserved in this measured mapping."
        )
    lines.extend(["", "## B02-EPUB-002 — navigation/links", ""])
    if direct_2:
        lines.append(
            f"- direct stdlib: navigation exact `{dim(direct_2, 'navigation').get('matched_exact')}/{dim(direct_2, 'navigation').get('expected')}`, "
            f"link semantic `{dim(direct_2, 'links').get('semantic_matches')}/{dim(direct_2, 'links').get('expected')}`, "
            f"authored target exact `{dim(direct_2, 'links').get('authored_exact_matches')}/{dim(direct_2, 'links').get('expected')}`."
        )
    if pandoc_2:
        lines.append(
            f"- Pandoc: navigation exact `{dim(pandoc_2, 'navigation').get('matched_exact')}/{dim(pandoc_2, 'navigation').get('expected')}`, "
            f"link semantic `{dim(pandoc_2, 'links').get('semantic_matches')}/{dim(pandoc_2, 'links').get('expected')}`, "
            f"authored target exact `{dim(pandoc_2, 'links').get('authored_exact_matches')}/{dim(pandoc_2, 'links').get('expected')}`; nav tree is not exposed by the measured Pandoc AST mapping."
        )
    lines.extend(["", "## Negative fixtures", ""])
    for fixture_id in ["B02-EPUB-NEG-001", "B02-EPUB-NEG-002"]:
        for route in ["direct-epub-stdlib", "pandoc-epub"]:
            result = by_key.get((fixture_id, route))
            if not result:
                continue
            assessment = result.get("expected_state_assessment", {})
            satisfied = (
                assessment.get("satisfied")
                if assessment.get("status") == "measured"
                else "not-measured"
            )
            lines.append(
                f"- `{fixture_id}` / `{route}`: route status `{result.get('route_status')}`, "
                f"expected-state satisfied `{satisfied}`; security checks retain partial/not-measured states where the harness cannot prove a property."
            )
    lines.extend(["", "## Decision boundary", "", "- No weighted/universal score is produced."])
    if pandoc_route.get("selection_blocker"):
        lines.append(f"- Pandoc route selection blocker: {pandoc_route['selection_blocker']}")
    elif pandoc_route.get("availability") == "available":
        lines.append(
            f"- Pandoc measured version `{pandoc_route.get('version')}` matches the E-02 surveyed baseline; this removes only the version-mismatch blocker and does not select the route."
        )
    else:
        lines.append("- Pandoc was not measured in this environment and cannot be selected from this evidence.")
    lines.extend(
        [
            "- B-02 coverage is incomplete; images/captions, notes, tables/code/MathML and malformed-resource coverage remain open.",
            "- G-04 and G-05 remain open; this baseline only advances evidence.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_observation(
    observations_dir: Path,
    fixture_id: str,
    route: str,
    observation: dict[str, Any],
) -> None:
    safe_route = route.replace("/", "-")
    path = observations_dir / f"{fixture_id}__{safe_route}.json"
    path.write_text(json.dumps(observation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_baseline(
    output_dir: Path,
    pandoc_executable: str = "pandoc",
    evidence_source_commit: str | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    fixture_dir = output_dir / "fixtures"
    generated = generate_fixtures.generate_all(fixture_dir)

    gold = json.loads((MANIFEST_DIR / "gold.json").read_text(encoding="utf-8"))
    fixture_manifest = json.loads((MANIFEST_DIR / "fixtures.json").read_text(encoding="utf-8"))
    fixture_by_id = {fixture["id"]: fixture for fixture in fixture_manifest["fixtures"]}
    generated_by_id = {fixture["id"]: fixture for fixture in generated["generated"]}

    version_info = pandoc_version(pandoc_executable)
    pandoc_available = version_info["returncode"] == 0 and bool(version_info["version"])
    routes: dict[str, Any] = {
        "direct-epub-stdlib": {
            "route": "direct-epub-stdlib",
            "availability": "available",
            "implementation": "Python standard library zipfile + ElementTree",
            "route_contract_version": "0.1.0",
        },
        "pandoc-epub": {
            "route": "pandoc-epub",
            "availability": "available" if pandoc_available else "unavailable",
            **version_info,
            "surveyed_version": E02_SURVEYED_PANDOC_VERSION,
            "surveyed_version_match": version_info["version"] == E02_SURVEYED_PANDOC_VERSION,
            "command_options": ["--sandbox", "--from=epub", "--to=json"],
            "network_instrumentation": "not-measured",
            "selection_blocker": (
                None
                if version_info["version"] == E02_SURVEYED_PANDOC_VERSION
                else "Measured Pandoc version differs from the E-02 surveyed baseline; rerun on an accepted current version before route selection."
            ),
        },
    }

    results: list[dict[str, Any]] = []
    observations_dir = output_dir / "observations"
    observations_dir.mkdir(exist_ok=True)
    for fixture_id in [
        "B02-EPUB-001",
        "B02-EPUB-002",
        "B02-EPUB-NEG-001",
        "B02-EPUB-NEG-002",
    ]:
        fixture_path = fixture_dir / fixture_by_id[fixture_id]["output"]
        gold_fixture = gold["fixtures"][fixture_id]
        is_negative = "-NEG-" in fixture_id

        direct = parse_direct_epub(fixture_path)
        _write_observation(observations_dir, fixture_id, "direct-epub-stdlib", direct)
        direct_result = (
            measure_negative_fixture(fixture_id, direct, gold_fixture)
            if is_negative
            else measure_normal_fixture(fixture_id, direct, gold_fixture)
        )
        direct_result["fixture_sha256"] = generated_by_id[fixture_id]["sha256"]
        results.append(direct_result)

        if pandoc_available:
            pandoc = run_pandoc_epub(fixture_path, pandoc_executable)
            _write_observation(observations_dir, fixture_id, "pandoc-epub", pandoc)
            pandoc_result = (
                measure_negative_fixture(fixture_id, pandoc, gold_fixture)
                if is_negative
                else measure_normal_fixture(fixture_id, pandoc, gold_fixture)
            )
            pandoc_result["fixture_sha256"] = generated_by_id[fixture_id]["sha256"]
            results.append(pandoc_result)
        else:
            results.append(
                {
                    "fixture_id": fixture_id,
                    "route": "pandoc-epub",
                    "route_status": "not-measured",
                    "reason": "Pandoc executable unavailable in this environment.",
                    "fixture_sha256": generated_by_id[fixture_id]["sha256"],
                }
            )

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
        "results": results,
        "coverage": {
            "benchmark_class": "B-02",
            "normal_fixtures": ["B02-EPUB-001", "B02-EPUB-002"],
            "negative_fixtures": ["B02-EPUB-NEG-001", "B02-EPUB-NEG-002"],
            "full_b02_coverage": False,
            "remaining_gaps": [
                "images/captions/alt",
                "footnotes/endnotes",
                "tables/code/MathML",
                "realistic integrated multi-chapter fixture beyond current navigation case",
                "malformed/missing resource negative fixture",
            ],
        },
        "measurement_limits": [
            "Timing values are single-run observations and are not performance claims.",
            "Provider network traffic is not instrumented in this child.",
            "Pandoc process isolation uses its --sandbox plus a controlled temporary input/work parent; OS-level write/network isolation is not claimed.",
            "Results apply only to the recorded route/version/environment and minimal fixture subset.",
        ],
        "decision_boundary": {
            "provider_selected": False,
            "first_slice_promoted": False,
            "g04_satisfied": False,
            "g05_satisfied": False,
        },
    }
    (output_dir / "b02-results.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    _write_summary(report, output_dir / "b02-summary.md")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pandoc", default="pandoc")
    parser.add_argument("--evidence-source-commit")
    args = parser.parse_args()
    report = run_baseline(
        args.output.resolve(), args.pandoc, evidence_source_commit=args.evidence_source_commit
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
