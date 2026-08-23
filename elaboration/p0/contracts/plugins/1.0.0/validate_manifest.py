#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


class ManifestError(ValueError):
    pass


PLUGIN_API_SUPPORTED_MIN = (1, 0, 0)
PLUGIN_API_SUPPORTED_MAX_EXCLUSIVE = (2, 0, 0)
EXTRACTION_CONTRACT_ID = "raiatea.extraction.processing-run"
EXTRACTION_SUPPORTED_MIN = (0, 1, 0)
EXTRACTION_SUPPORTED_MAX_EXCLUSIVE = (0, 2, 0)
SAFE_LAUNCH_TOKEN = re.compile(r"^[A-Za-z0-9_.\/-]+$")
SAFE_MODULE_TARGET = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestError(message)


def _version(value: str, label: str) -> tuple[int, int, int]:
    core = value.split("+", 1)[0].split("-", 1)[0]
    try:
        parts = tuple(int(part) for part in core.split("."))
    except Exception as exc:
        raise ManifestError(f"{label}-invalid-version") from exc
    _require(len(parts) == 3, f"{label}-invalid-version")
    return parts  # type: ignore[return-value]


def _range_intersects(value: dict[str, Any], minimum: tuple[int, int, int], maximum: tuple[int, int, int], label: str) -> bool:
    low = _version(value.get("min_inclusive", ""), f"{label}-min")
    high = _version(value.get("max_exclusive", ""), f"{label}-max")
    _require(low < high, f"{label}-empty-or-reversed-range")
    return low < maximum and high > minimum


def _validate_entrypoint(value: Any) -> None:
    _require(isinstance(value, dict), "entrypoint-required")
    _require(value.get("kind") == "process", "entrypoint-kind-unsupported")
    command = value.get("command")
    _require(isinstance(command, list) and command, "entrypoint-command-required")
    _require(all(isinstance(token, str) and token for token in command), "entrypoint-command-token-invalid")

    # V1a launch metadata deliberately carries no free-form runtime arguments.
    # Accepted forms are a single executable target or Python module launch.
    if len(command) == 1:
        _require(bool(SAFE_LAUNCH_TOKEN.fullmatch(command[0])), "entrypoint-command-not-structural")
    elif len(command) == 3:
        _require(command[1] == "-m", "entrypoint-command-not-structural")
        _require(bool(SAFE_LAUNCH_TOKEN.fullmatch(command[0])), "entrypoint-command-not-structural")
        _require(bool(SAFE_MODULE_TARGET.fullmatch(command[2])), "entrypoint-command-not-structural")
    else:
        raise ManifestError("entrypoint-command-not-structural")


def validate(manifest: dict[str, Any]) -> None:
    _require(manifest.get("manifest_version") == "1.0.0", "unsupported-manifest-version")

    plugin = manifest.get("plugin")
    _require(isinstance(plugin, dict), "plugin-identity-required")
    _require(bool(plugin.get("plugin_id")), "plugin-id-required")
    _version(str(plugin.get("version", "")), "plugin")

    api_range = manifest.get("raiatea_plugin_api")
    _require(isinstance(api_range, dict), "plugin-api-range-required")
    _require(
        _range_intersects(api_range, PLUGIN_API_SUPPORTED_MIN, PLUGIN_API_SUPPORTED_MAX_EXCLUSIVE, "plugin-api"),
        "plugin-api-incompatible",
    )

    families = manifest.get("families")
    _require(isinstance(families, list) and families, "families-required")
    family_set = set(families)
    _require(len(family_set) == len(families), "duplicate-plugin-family")
    _require(family_set <= {"source", "extractor", "transformer"}, "unknown-plugin-family")

    capabilities = manifest.get("capabilities")
    _require(isinstance(capabilities, list) and capabilities, "capabilities-required")
    capability_ids: set[str] = set()
    profile_keys: set[tuple[str, str]] = set()

    for cap_index, capability in enumerate(capabilities):
        _require(isinstance(capability, dict), f"capability-{cap_index}-must-be-object")
        capability_id = capability.get("capability_id")
        _require(isinstance(capability_id, str) and capability_id, f"capability-{cap_index}-id-required")
        _require(capability_id not in capability_ids, "duplicate-capability-id")
        capability_ids.add(capability_id)

        expected_family = capability_id.split(".", 1)[0]
        expected_family = {"extract": "extractor", "transform": "transformer"}.get(expected_family, expected_family)
        _require(expected_family in family_set, f"capability-family-not-declared:{capability_id}")

        profiles = capability.get("profiles")
        _require(isinstance(profiles, list) and profiles, f"capability-{cap_index}-profiles-required")
        for profile_index, profile in enumerate(profiles):
            _require(isinstance(profile, dict), f"profile-{cap_index}-{profile_index}-must-be-object")
            profile_id = profile.get("profile_id")
            _require(isinstance(profile_id, str) and profile_id, f"profile-{cap_index}-{profile_index}-id-required")
            key = (capability_id, profile_id)
            _require(key not in profile_keys, "duplicate-capability-profile")
            profile_keys.add(key)
            _require(profile.get("family") == expected_family, f"profile-family-mismatch:{capability_id}:{profile_id}")

            contracts = profile.get("contracts")
            _require(isinstance(contracts, list), f"profile-contracts-required:{capability_id}:{profile_id}")
            contract_ids: set[str] = set()
            for contract in contracts:
                _require(isinstance(contract, dict), "contract-ref-must-be-object")
                contract_id = contract.get("contract_id")
                _require(isinstance(contract_id, str) and contract_id, "contract-id-required")
                _require(contract_id not in contract_ids, "duplicate-contract-ref")
                contract_ids.add(contract_id)
                version_range = contract.get("version_range")
                _require(isinstance(version_range, dict), "contract-version-range-required")
                if contract_id == EXTRACTION_CONTRACT_ID:
                    _require(
                        _range_intersects(
                            version_range,
                            EXTRACTION_SUPPORTED_MIN,
                            EXTRACTION_SUPPORTED_MAX_EXCLUSIVE,
                            "extraction-contract",
                        ),
                        "extraction-contract-incompatible",
                    )

            if expected_family == "extractor" and capability_id in {"extract.run", "extract.probe"}:
                _require(EXTRACTION_CONTRACT_ID in contract_ids, f"extractor-profile-missing-e05-contract:{profile_id}")
            if expected_family != "extractor":
                _require(EXTRACTION_CONTRACT_ID not in contract_ids, f"non-extractor-must-not-own-extraction-contract:{profile_id}")

            for forbidden in ("quality_score", "quality_guarantee", "complete", "accuracy"):
                _require(forbidden not in profile, f"capability-profile-must-not-claim-quality-truth:{forbidden}")

    permissions = manifest.get("permissions")
    _require(isinstance(permissions, dict), "permissions-required")
    for network in permissions.get("network", []):
        _require(isinstance(network, dict), "network-permission-must-be-object")
        host = str(network.get("host", ""))
        _require(host and "*" not in host, "network-wildcard-forbidden")
    for secret in permissions.get("secrets", []):
        _require(isinstance(secret, str) and secret, "secret-name-required")
        _require("=" not in secret and ":" not in secret, "secret-value-must-not-be-embedded")

    _validate_entrypoint(manifest.get("entrypoint"))

    trust_tier = manifest.get("trust_tier")
    _require(trust_tier in {"official", "verified", "community", "local"}, "invalid-trust-tier")
    _require("rights" not in manifest and "rights_decision" not in manifest, "manifest-must-not-own-rights-decision")
    _require("grants" not in permissions and "authorized" not in permissions, "permissions-are-declarations-not-grants")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifests", nargs="+", type=Path)
    args = parser.parse_args()
    for path in args.manifests:
        value = json.loads(path.read_text(encoding="utf-8"))
        validate(value)
        print(f"PASS {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
