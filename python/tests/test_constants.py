"""Testes de sanidade para src/constants.py."""

from src.constants import CHALLENGE_URL, EXPECTED_COLUMNS, FIELD_MAP, TOTAL_ROUNDS


def test_expected_columns_matches_field_map_keys():
    assert EXPECTED_COLUMNS == list(FIELD_MAP.keys())


def test_total_rounds_is_ten():
    assert TOTAL_ROUNDS == 10


def test_field_map_has_seven_fields():
    assert len(FIELD_MAP) == 7


def test_field_map_values_are_non_empty_strings():
    for ng_reflect_name in FIELD_MAP.values():
        assert isinstance(ng_reflect_name, str)
        assert ng_reflect_name.strip() != ""


def test_challenge_url_is_https():
    assert CHALLENGE_URL.startswith("https://")
