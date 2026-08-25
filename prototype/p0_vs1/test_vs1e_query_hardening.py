from __future__ import annotations

import unittest

from prototype.p0_vs1.search_contract import SearchContractError, normalize_query_plan


class QueryTypeHardeningTests(unittest.TestCase):
    def test_non_string_operator_sort_and_fields_fail_as_contract_errors(self) -> None:
        cases = [
            {
                "criteria": [
                    {"field": "extracted_text", "operator": ["contains"], "value": "x"}
                ],
                "sort_field": "source_ref_id",
                "descending": False,
            },
            {
                "criteria": [
                    {"field": ["extracted_text"], "operator": "contains", "value": "x"}
                ],
                "sort_field": "source_ref_id",
                "descending": False,
            },
            {
                "criteria": [],
                "sort_field": ["source_ref_id"],
                "descending": False,
            },
            {
                "criteria": [
                    {"field": "extracted_text", "operator": "contains", "value": {"x": 1}}
                ],
                "sort_field": "source_ref_id",
                "descending": False,
            },
        ]
        for candidate in cases:
            with self.subTest(candidate=candidate):
                with self.assertRaises(SearchContractError):
                    normalize_query_plan(candidate)

    def test_unknown_extra_query_keys_fail_closed(self) -> None:
        with self.assertRaises(SearchContractError):
            normalize_query_plan(
                {
                    "criteria": [],
                    "sort_field": "source_ref_id",
                    "descending": False,
                    "script": "do something",
                }
            )


if __name__ == "__main__":
    unittest.main()
