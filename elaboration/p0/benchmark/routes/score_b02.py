"""Provider-neutral scoring helpers for the B-02 benchmark subset."""

from __future__ import annotations

from typing import Any


def _resource_match(expected: str | None, observed: str | None) -> tuple[bool, bool]:
    if expected is None or observed is None:
        return False, False
    exact = expected == observed
    suffix = exact or expected.endswith("/" + observed)
    return exact, suffix


def _find_block_by_text(observation: dict[str, Any], text: str) -> dict[str, Any] | None:
    for block in observation.get("blocks", []):
        if block.get("text") == text:
            return block
    return None


def _semantic_target(target: str | None) -> str | None:
    if target is None:
        return None
    if target.startswith("#") and ".xhtml#" in target:
        return target[1:]
    return target


def measure_normal_fixture(
    fixture_id: str,
    observation: dict[str, Any],
    gold_fixture: dict[str, Any],
) -> dict[str, Any]:
    """Measure dimensions independently. No weighted/total score is produced."""
    dimensions: dict[str, Any] = {}

    expected_spine = gold_fixture.get("spine")
    if expected_spine is not None:
        observed_spine = observation.get("spine")
        dimensions["spine_order"] = {
            "status": "measured",
            "expected": expected_spine,
            "observed": observed_spine,
            "exact": observed_spine == expected_spine,
        }

    reference_units = gold_fixture.get("reference_units", [])
    if reference_units:
        matched_text = 0
        heading_expected = 0
        heading_matched = 0
        coordinate_rows = []
        for unit in reference_units:
            text = unit.get("text")
            block = _find_block_by_text(observation, text) if text else None
            if block is not None:
                matched_text += 1
            if unit.get("type") == "heading":
                heading_expected += 1
                if block is not None and block.get("type") == "heading":
                    heading_matched += 1
            if "resource" in unit or "fragment" in unit:
                observed_resource = block.get("resource") if block else None
                observed_fragment = block.get("fragment") if block else None
                resource_exact, resource_traceable = _resource_match(
                    unit.get("resource"), observed_resource
                )
                fragment_exact = (
                    unit.get("fragment") == observed_fragment
                    if unit.get("fragment") is not None
                    else True
                )
                coordinate_rows.append(
                    {
                        "reference_unit": unit.get("id"),
                        "resource_exact": resource_exact,
                        "resource_traceable_suffix": resource_traceable,
                        "fragment_exact": fragment_exact,
                        "full_exact": bool(block and resource_exact and fragment_exact),
                        "traceable": bool(block and resource_traceable and fragment_exact),
                        "observed_resource": observed_resource,
                        "observed_fragment": observed_fragment,
                    }
                )

        dimensions["content_text"] = {
            "status": "measured",
            "matched_units": matched_text,
            "expected_units": len(reference_units),
            "exact_fraction": matched_text / len(reference_units),
        }
        if heading_expected:
            dimensions["heading_structure"] = {
                "status": "measured",
                "matched_headings": heading_matched,
                "expected_headings": heading_expected,
                "exact_fraction": heading_matched / heading_expected,
            }
        if coordinate_rows:
            dimensions["source_coordinates"] = {
                "status": "measured",
                "units": coordinate_rows,
                "full_exact_count": sum(row["full_exact"] for row in coordinate_rows),
                "traceable_count": sum(row["traceable"] for row in coordinate_rows),
                "expected_count": len(coordinate_rows),
            }

    reading_order = gold_fixture.get("reading_order", [])
    if reading_order and reference_units:
        text_by_id = {
            unit["id"]: unit.get("text")
            for unit in reference_units
            if unit.get("id") and unit.get("text")
        }
        expected_texts = set(text_by_id.values())
        observed_texts = [
            block.get("text")
            for block in observation.get("blocks", [])
            if block.get("text") in expected_texts
        ]
        positions = {text: index for index, text in enumerate(observed_texts)}
        edge_rows = []
        for before_id, after_id in reading_order:
            before_text = text_by_id.get(before_id)
            after_text = text_by_id.get(after_id)
            satisfied = (
                before_text in positions
                and after_text in positions
                and positions[before_text] < positions[after_text]
            )
            edge_rows.append({"before": before_id, "after": after_id, "satisfied": satisfied})
        dimensions["reading_order"] = {
            "status": "measured",
            "satisfied_edges": sum(row["satisfied"] for row in edge_rows),
            "expected_edges": len(edge_rows),
            "edges": edge_rows,
        }

    expected_nav = gold_fixture.get("navigation")
    if expected_nav is not None:
        observed_nav = observation.get("navigation", [])
        rows = []
        for item in expected_nav:
            match = next(
                (observed for observed in observed_nav if observed.get("label") == item.get("label")),
                None,
            )
            exact_resource, traceable_resource = _resource_match(
                item.get("resource"), match.get("resource") if match else None
            )
            fragment_exact = match is not None and match.get("fragment") == item.get("fragment")
            rows.append(
                {
                    "label": item.get("label"),
                    "found": match is not None,
                    "resource_exact": exact_resource,
                    "resource_traceable_suffix": traceable_resource,
                    "fragment_exact": fragment_exact,
                }
            )
        dimensions["navigation"] = {
            "status": "measured",
            "matched_exact": sum(
                row["found"] and row["resource_exact"] and row["fragment_exact"]
                for row in rows
            ),
            "expected": len(rows),
            "items": rows,
        }

    expected_links = gold_fixture.get("links")
    if expected_links is not None:
        observed_links = observation.get("links", [])
        rows = []
        for expected in expected_links:
            semantic_expected = _semantic_target(expected.get("target"))
            best = next(
                (
                    observed
                    for observed in observed_links
                    if _semantic_target(observed.get("raw_target")) == semantic_expected
                ),
                None,
            )
            rows.append(
                {
                    "expected_target": expected.get("target"),
                    "found_semantic": best is not None,
                    "authored_target_exact": (
                        best is not None and best.get("raw_target") == expected.get("target")
                    ),
                    "observed_target": best.get("raw_target") if best else None,
                    "from_fragment_preserved": (
                        best is not None and best.get("from_fragment") == expected.get("from_fragment")
                    ),
                }
            )
        dimensions["links"] = {
            "status": "measured",
            "semantic_matches": sum(row["found_semantic"] for row in rows),
            "authored_exact_matches": sum(row["authored_target_exact"] for row in rows),
            "expected": len(rows),
            "items": rows,
        }

    return {
        "fixture_id": fixture_id,
        "route": observation.get("route"),
        "route_status": observation.get("status"),
        "warnings": observation.get("warnings", []),
        "dimensions": dimensions,
        "duration_seconds": observation.get("duration_seconds"),
        "timing_semantics": "single-run-observation-not-performance-claim",
        "raw_output_sha256": observation.get("raw_output_sha256"),
        "raw_output_bytes": observation.get("raw_output_bytes"),
        "side_effect_files": observation.get("side_effect_files", []),
    }


def _warning_codes(observation: dict[str, Any]) -> set[str]:
    return {
        str(item.get("code"))
        for item in observation.get("warnings", [])
        if item.get("code") is not None
    }


def _expected_state_assessment(expected: str | None, observation: dict[str, Any]) -> dict[str, Any]:
    status = observation.get("status")
    warnings = _warning_codes(observation)
    side_effects = observation.get("side_effect_files", [])
    if expected == "degraded-with-warning-or-safe-success":
        satisfied = (status == "degraded" and bool(warnings)) or (
            status == "success" and not side_effects
        )
    elif expected == "rejected-or-degraded-with-warning":
        satisfied = status == "rejected" or (status == "degraded" and bool(warnings))
    else:
        return {
            "status": "not-measured",
            "expected": expected,
            "observed": status,
            "reason": "No benchmark evaluator exists for this expected-state expression.",
        }
    return {
        "status": "measured",
        "expected": expected,
        "observed": status,
        "satisfied": satisfied,
    }


def _security_expectation_assessment(
    expectation: str,
    observation: dict[str, Any],
) -> dict[str, Any]:
    route = observation.get("route")
    warnings = _warning_codes(observation)
    side_effects = observation.get("side_effect_files", [])

    if expectation == "script-not-executed":
        if route == "direct-epub-stdlib":
            return {
                "status": "measured",
                "satisfied": "active-content-present" in warnings,
                "evidence": "Direct route treats script elements as data, skips their body, and emits active-content-present.",
            }
        return {
            "status": "not-measured",
            "satisfied": None,
            "evidence": "Pandoc ran with --sandbox and produced no file side effects, but the current inert script has no observable execution probe.",
        }

    if expectation == "no-network-required":
        return {
            "status": "fixture-property",
            "satisfied": True,
            "evidence": "The generated fixture contains no script src/fetch/XHR/network-dependent payload; provider network traffic is not instrumented.",
        }

    if expectation == "no-path-escape":
        if route == "direct-epub-stdlib":
            return {
                "status": "measured",
                "satisfied": observation.get("status") == "rejected" and "unsafe-package-member" in warnings,
                "evidence": "Direct route rejects parent-traversal members before semantic parsing and never extracts ZIP members.",
            }
        return {
            "status": "partial",
            "satisfied": not side_effects,
            "evidence": "Pandoc input/cwd are inside a controlled temporary parent with --sandbox; no file side effects were observed inside that parent. OS-level writes outside the controlled parent are not instrumented.",
        }

    if expectation == "no-extractall":
        if route == "direct-epub-stdlib":
            return {
                "status": "measured",
                "satisfied": True,
                "evidence": "Direct route reads ZIP members in memory and has no extract/extractall operation.",
            }
        return {
            "status": "not-measured",
            "satisfied": None,
            "evidence": "Pandoc internals are opaque to this harness; only observable file side effects are captured.",
        }

    return {
        "status": "not-measured",
        "satisfied": None,
        "evidence": "No benchmark evaluator exists for this security expectation.",
    }


def measure_negative_fixture(
    fixture_id: str,
    observation: dict[str, Any],
    gold_fixture: dict[str, Any],
) -> dict[str, Any]:
    expectations = gold_fixture.get("security_expectations", [])
    return {
        "fixture_id": fixture_id,
        "route": observation.get("route"),
        "route_status": observation.get("status"),
        "expected_state": gold_fixture.get("expected_state"),
        "expected_state_assessment": _expected_state_assessment(
            gold_fixture.get("expected_state"), observation
        ),
        "security_expectations": [
            {"expectation": expectation, **_security_expectation_assessment(expectation, observation)}
            for expectation in expectations
        ],
        "warnings": observation.get("warnings", []),
        "side_effect_files": observation.get("side_effect_files", []),
        "duration_seconds": observation.get("duration_seconds"),
        "timing_semantics": "single-run-observation-not-performance-claim",
        "raw_output_sha256": observation.get("raw_output_sha256"),
        "raw_output_bytes": observation.get("raw_output_bytes"),
        "sandbox_enabled": observation.get("sandbox_enabled"),
        "network_instrumentation": observation.get("network_instrumentation", "not-applicable"),
        "normal_quality_aggregate": "excluded",
    }
