#!/usr/bin/env python3
"""Run the Docling 2.118.0 B-01 structured reference route.

This is benchmark evidence only. It neither selects Docling nor defines E-05.
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
LOCK_DIR = BENCH_DIR / "locks"
CONSTRAINTS_PATH = LOCK_DIR / "docling-2.118.0-python312-linux-x86_64.txt"
MODEL_LOCK_PATH = LOCK_DIR / "docling-2.118.0-layout-model-payload.json"
sys.path.insert(0, str(BENCH_DIR))
sys.path.insert(0, str(HERE))

import generate_fixtures  # noqa: E402
from docling_routes import (  # noqa: E402
    DOCLING_SOURCE_COMMIT,
    DOCLING_VERSION,
    DOCLING_WHEEL_SHA256,
    artifact_manifest,
    installed_environment,
    run_docling_pdf_json,
)
from score_b01 import measure_b01_fixture  # noqa: E402
from verify_docling_reference import (  # noqa: E402
    freeze_sha256,
    load_constraints,
    model_payload_manifest,
)


RESULT_CONTRACT_VERSION = "0.1.0"
B01_NORMAL_FIXTURES = ["B01-PDF-001", "B01-PDF-002", "B01-PDF-003"]


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
        "docling_routes": HERE / "docling_routes.py",
        "score_b01": HERE / "score_b01.py",
        "measure_docling_b01": Path(__file__).resolve(),
        "verify_docling_reference": HERE / "verify_docling_reference.py",
        "dependency_constraints": CONSTRAINTS_PATH,
        "model_payload_lock": MODEL_LOCK_PATH,
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
        "gpu": "not-used-cpu-route",
        "portability_claim": False,
    }


def _write_summary(report: dict[str, Any], path: Path) -> None:
    by_fixture = {item["fixture_id"]: item for item in report["results"]}

    def dim(result: dict[str, Any], name: str) -> dict[str, Any]:
        return result.get("dimensions", {}).get(name, {})

    payload = report["model_payload"]
    package = report["package_environment"]
    locks = report["reference_locks"]
    lines = [
        "# B-01 Docling 2.118.0 structured reference baseline",
        "",
        "> Benchmark evidence only. Docling is not selected as a production Provider.",
        "> The fixture/gold redistribution gate remains open in issue #131.",
        "",
        "## Environment / route",
        "",
        f"- OS: `{report['environment']['platform_system']} {report['environment']['platform_release']}` `{report['environment']['machine']}`",
        f"- Python: `{report['environment']['python_version']}`",
        f"- Docling: `{package.get('docling_version')}`",
        f"- installed environment freeze SHA-256: `{package.get('freeze_sha256')}`",
        f"- locked environment freeze SHA-256: `{locks.get('expected_environment_freeze_sha256')}`",
        f"- stable model payload files: `{payload.get('file_count')}`, bytes `{payload.get('bytes')}`",
        f"- stable model payload manifest SHA-256: `{payload.get('payload_manifest_sha256')}`",
        f"- cache-inclusive download-tree files: `{report['model_artifacts'].get('file_count')}`; its hash is evidence only and is not the stable model lock",
        "- route: CPU / OCR disabled / table+enrichment models disabled / remote services disabled / external plugins disabled.",
        "- measured phase sets Hugging Face and transformers offline flags and controlled cache roots.",
        "- OS-level network isolation is not claimed.",
        "",
    ]
    for fixture_id in B01_NORMAL_FIXTURES:
        result = by_fixture.get(fixture_id, {})
        text = dim(result, "content_text")
        order = dim(result, "reading_order")
        coords = dim(result, "source_coordinates")
        hierarchy = dim(result, "hierarchy")
        levels = hierarchy.get("heading_levels", {})
        links = dim(result, "links")
        lines.extend(
            [
                f"## {fixture_id}",
                "",
                f"- route status: `{result.get('route_status')}` / provider status `{result.get('provider_conversion_status')}`",
                f"- reference text content preserved: `{text.get('matched_units')}/{text.get('expected_units')}`",
                f"- segmentation-exact Provider blocks: `{text.get('exact_block_units')}/{text.get('expected_units')}`",
                f"- reading-order edges: `{order.get('satisfied_edges')}/{order.get('expected_edges')}`",
                f"- source coordinates: `{coords.get('status')}`; unit-attributable geometry `{coords.get('geometry_evidence_count')}/{coords.get('expected_count')}`, contained `{coords.get('contained_count')}` when measured",
                f"- hierarchy: `{hierarchy.get('status')}`; exact semantic types `{hierarchy.get('type_exact_count')}/{hierarchy.get('expected_count')}`; segmentation-exact semantic units `{hierarchy.get('segmentation_exact_count')}/{hierarchy.get('expected_count')}`",
                f"- heading levels: `{levels.get('status')}`; exact `{levels.get('exact_count')}/{levels.get('expected_count')}` when measurable",
                f"- links: `{links.get('status')}`; target exact `{links.get('target_exact_count')}/{links.get('expected_count')}` when measurable",
                f"- page structure observed: `{result.get('page_structure_observed')}`",
                f"- bbox structure observed: `{result.get('bbox_structure_observed')}`",
                f"- Docling body order source: `{result.get('body_order_source')}`",
                f"- raw lossless JSON SHA-256: `{result.get('raw_output_sha256')}`",
                f"- measured-cache delta files: `{result.get('cache_delta_file_count')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation boundary",
            "",
            "- Content preservation and Provider segmentation fidelity are separate dimensions: a reference unit may be preserved inside one larger Provider block without being treated as an exact block boundary.",
            "- Aggregate-block geometry is retained as Provider evidence but is never copied onto each substring-aligned reference unit; only unit-attributable bbox evidence can satisfy coordinate fidelity.",
            "- Docling geometry is compared only when provenance bbox and page identity are explicitly present.",
            "- TOPLEFT provenance is converted using the corresponding Docling page height; BOTTOMLEFT provenance maps directly.",
            "- Heading levels are credited only from explicit Docling level evidence; visual hierarchy is not inferred by the scorer.",
            "- Link targets/associations are credited only if lossless Docling output exposes explicit link evidence; visible text/layout is not enough.",
            "- Missing provenance/unknown labels remain visible warnings or unmeasured dimensions; they are never invented.",
            "- The stable model lock excludes ephemeral `.cache` download metadata while pinning every payload file by path, size and SHA-256.",
            "- No weighted/universal score is produced.",
            "- Comparison with Poppler/Tika is limited to dimensions measured by each route.",
            "- B-01 coverage remains incomplete and #131/G-02/G-04/G-05/first-slice promotion remain open.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _cache_delta(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    before_paths = {item["path"] for item in before.get("files", [])}
    return [
        item["path"]
        for item in after.get("files", [])
        if item["path"] not in before_paths
    ]


def _load_reference_locks() -> tuple[list[str], dict[str, Any]]:
    constraints = load_constraints(CONSTRAINTS_PATH)
    model_lock = json.loads(MODEL_LOCK_PATH.read_text(encoding="utf-8"))
    return constraints, model_lock


def run_baseline(
    output_dir: Path,
    artifacts_path: Path,
    cache_root: Path,
    evidence_source_commit: str | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    observations_dir = output_dir / "observations"
    raw_dir.mkdir(exist_ok=True)
    observations_dir.mkdir(exist_ok=True)

    fixture_dir = output_dir / "fixtures"
    generated = generate_fixtures.generate_all(fixture_dir)
    fixture_manifest = json.loads(
        (MANIFEST_DIR / "fixtures.json").read_text(encoding="utf-8")
    )
    gold = json.loads((MANIFEST_DIR / "gold.json").read_text(encoding="utf-8"))
    fixtures = {item["id"]: item for item in fixture_manifest["fixtures"]}
    generated_by_id = {item["id"]: item for item in generated["generated"]}

    package_environment = installed_environment()
    if package_environment.get("docling_version") != DOCLING_VERSION:
        raise ValueError(
            f"Expected Docling {DOCLING_VERSION}, observed {package_environment.get('docling_version')}"
        )

    expected_freeze, model_lock = _load_reference_locks()
    if package_environment.get("freeze") != expected_freeze:
        raise ValueError(
            "Installed Docling reference environment does not match the pinned constraints"
        )

    models = artifact_manifest(artifacts_path)
    if not models.get("exists") or models.get("file_count", 0) == 0:
        raise ValueError("Docling model artifact root is missing or empty")
    payload = model_payload_manifest(artifacts_path)
    if (
        payload.get("files") != model_lock.get("files")
        or payload.get("payload_manifest_sha256")
        != model_lock.get("payload_manifest_sha256")
    ):
        raise ValueError("Docling model payload does not match the pinned payload lock")

    (output_dir / "docling-model-manifest.json").write_text(
        json.dumps(models, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "docling-model-payload-manifest.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "python-environment-freeze.txt").write_text(
        "\n".join(package_environment.get("freeze", [])) + "\n",
        encoding="utf-8",
    )

    results: list[dict[str, Any]] = []
    for fixture_id in B01_NORMAL_FIXTURES:
        fixture_path = fixture_dir / fixtures[fixture_id]["output"]
        fixture_cache = cache_root / fixture_id
        observation = run_docling_pdf_json(
            fixture_path,
            artifacts_path,
            fixture_cache,
        )
        raw_document = observation.pop("raw_document", None)
        if raw_document is not None:
            (raw_dir / f"{fixture_id}__docling.json").write_text(
                json.dumps(raw_document, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        (observations_dir / f"{fixture_id}__docling.json").write_text(
            json.dumps(observation, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        result = measure_b01_fixture(
            fixture_id,
            observation,
            gold["fixtures"][fixture_id],
        )
        result["fixture_sha256"] = generated_by_id[fixture_id]["sha256"]
        result["provider_conversion_status"] = observation.get(
            "provider_conversion_status"
        )
        result["page_structure_observed"] = observation.get(
            "page_structure_observed"
        )
        result["bbox_structure_observed"] = observation.get(
            "bbox_structure_observed"
        )
        result["body_order_source"] = observation.get("body_order_source")
        result["model_payload_manifest_sha256"] = payload.get(
            "payload_manifest_sha256"
        )
        before = observation.get("cache_before", {})
        after = observation.get("cache_after", {})
        delta = _cache_delta(before, after)
        result["cache_delta_file_count"] = len(delta)
        result["cache_delta_files"] = delta
        result["route_options"] = observation.get("route_options")
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
        "package_provenance": {
            "docling_version": DOCLING_VERSION,
            "wheel_sha256_from_pypi_evidence": DOCLING_WHEEL_SHA256,
            "source_commit_from_pypi_attestation": DOCLING_SOURCE_COMMIT,
        },
        "package_environment": package_environment,
        "model_artifacts": models,
        "model_payload": payload,
        "reference_locks": {
            "dependency_constraints_path": str(CONSTRAINTS_PATH.relative_to(BENCH_DIR)),
            "dependency_constraints_sha256": _sha256(CONSTRAINTS_PATH),
            "expected_environment_freeze_sha256": freeze_sha256(expected_freeze),
            "model_payload_lock_path": str(MODEL_LOCK_PATH.relative_to(BENCH_DIR)),
            "model_payload_lock_sha256": _sha256(MODEL_LOCK_PATH),
            "expected_model_payload_manifest_sha256": model_lock.get(
                "payload_manifest_sha256"
            ),
        },
        "harness_fingerprints": _file_fingerprints(),
        "rights_state": {
            "redistribution": fixture_manifest["rights_gate"]["redistribution"],
            "decision_issue": fixture_manifest["rights_gate"]["decision_issue"],
            "public_rights_safe": False,
            "remote_provider": "denied",
        },
        "route": {
            "route": "docling-2.118.0-standard-pdf-native-no-ocr",
            "docling_version": DOCLING_VERSION,
            "ocr": False,
            "table_structure": False,
            "remote_services": False,
            "external_plugins": False,
            "code_formula_picture_chart_enrichment": False,
            "force_backend_text": False,
            "accelerator": "cpu",
            "threads": 4,
            "artifacts_path": "controlled-prefetched-root",
            "measured_network_policy": (
                "HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1, "
                "enable_remote_services=false; OS-level network isolation not claimed"
            ),
        },
        "results": results,
        "comparison_controls": {
            "poppler_reference_commit": "add6bbe0757848d66d17a364f8566985eef21c60",
            "tika_reference_commit": "7fa34beee53305026d21123de97f522730ce1c58",
            "note": (
                "Existing Poppler/Tika evidence remains canonical for earlier fixtures; "
                "this run extends the current fixture subset and comparisons remain per dimension."
            ),
        },
        "coverage": {
            "benchmark_class": "B-01",
            "normal_fixtures": B01_NORMAL_FIXTURES,
            "full_b01_coverage": False,
            "remaining_gaps": [
                "figures/captions",
                "tables",
                "formula fidelity beyond code/preformatted text",
                "defective native text subprofile",
                "malformed/access-controlled negative fixtures",
                "additional structured Provider measurements if still decision-relevant",
            ],
        },
        "measurement_limits": [
            "The route uses only the prefetched, payload-locked model artifact root recorded in this evidence step.",
            "Ephemeral Hugging Face download/cache metadata is excluded from the stable model payload lock but remains visible in the cache-inclusive artifact manifest.",
            "Offline environment flags and disabled Docling remote services make implicit supported model fetches fail closed; OS-level network isolation is not claimed.",
            "OCR/table/enrichment features are disabled so this B-01 route measures layout/text structure rather than unrelated models.",
            "Content preservation does not imply segmentation preservation; aggregate Provider blocks are aligned conservatively and their geometry is not copied onto substring reference units.",
            "Heading levels and link targets/associations are credited only from explicit lossless Docling evidence; typography/layout is never used as a fallback.",
            "Timing values are single-run observations and are not performance claims.",
            "Results apply only to the recorded package/dependencies/models/runtime/environment and current fixture subset.",
        ],
        "decision_boundary": {
            "provider_selected": False,
            "first_slice_promoted": False,
            "g02_satisfied": False,
            "g04_satisfied": False,
            "g05_satisfied": False,
        },
    }
    (output_dir / "docling-b01-results.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    _write_summary(report, output_dir / "docling-b01-summary.md")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--artifacts-path", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--evidence-source-commit")
    args = parser.parse_args()
    report = run_baseline(
        args.output.resolve(),
        args.artifacts_path.resolve(),
        args.cache_root.resolve(),
        evidence_source_commit=args.evidence_source_commit,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
