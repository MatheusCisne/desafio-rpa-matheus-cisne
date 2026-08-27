"""Testes unitários para src/excel_reader.py.

Cada teste cria um .xlsx temporário (via pandas/openpyxl) dentro do próprio
teste, para não depender de nenhum arquivo fixo no repositório.
"""

from pathlib import Path

import pandas as pd
import pytest

from src.excel_reader import ExcelValidationError, _normalize_phone, read_challenge_data

REQUIRED_COLUMNS = [
    "First Name",
    "Last Name",
    "Company Name",
    "Role in Company",
    "Address",
    "Email",
    "Phone Number",
]


def _write_xlsx(tmp_path: Path, df: pd.DataFrame, name: str = "challenge.xlsx") -> Path:
    path = tmp_path / name
    df.to_excel(path, index=False)
    return path


def test_normal_case_reads_all_rows(tmp_path):
    df = pd.DataFrame(
        {
            "First Name": ["Ada", "Alan"],
            "Last Name": ["Lovelace", "Turing"],
            "Company Name": ["Acme", "Beta"],
            "Role in Company": ["Engineer", "Scientist"],
            "Address": ["123 St", "456 Ave"],
            "Email": ["ada@example.com", "alan@example.com"],
            "Phone Number": ["1234567890", "0987654321"],
        }
    )
    path = _write_xlsx(tmp_path, df)

    result = read_challenge_data(path)

    assert len(result) == 2
    assert result[0]["First Name"] == "Ada"
    assert result[1]["Last Name"] == "Turing"
    assert result[0]["Phone Number"] == "1234567890"


def test_header_with_trailing_space_is_stripped(tmp_path):
    df = pd.DataFrame(
        {
            "First Name": ["Ada"],
            "Last Name ": ["Lovelace"],  # espaço no final, como no site real
            "Company Name": ["Acme"],
            "Role in Company": ["Engineer"],
            "Address": ["123 St"],
            "Email": ["ada@example.com"],
            "Phone Number": ["1234567890"],
        }
    )
    path = _write_xlsx(tmp_path, df)

    result = read_challenge_data(path)

    assert len(result) == 1
    assert result[0]["Last Name"] == "Lovelace"


def test_extra_ghost_column_is_ignored(tmp_path):
    df = pd.DataFrame(
        {
            "First Name": ["Ada"],
            "Last Name": ["Lovelace"],
            "Company Name": ["Acme"],
            "Role in Company": ["Engineer"],
            "Address": ["123 St"],
            "Email": ["ada@example.com"],
            "Phone Number": ["1234567890"],
            "Unnamed: 7": [None],  # 8ª coluna fantasma
        }
    )
    path = _write_xlsx(tmp_path, df)

    result = read_challenge_data(path)

    assert len(result) == 1
    assert "Unnamed: 7" not in result[0]
    assert set(result[0].keys()) == set(REQUIRED_COLUMNS)


def test_fully_empty_rows_are_removed(tmp_path):
    df = pd.DataFrame(
        {
            "First Name": ["Ada", None, None],
            "Last Name": ["Lovelace", None, None],
            "Company Name": ["Acme", None, None],
            "Role in Company": ["Engineer", None, None],
            "Address": ["123 St", None, None],
            "Email": ["ada@example.com", None, None],
            "Phone Number": ["1234567890", None, None],
        }
    )
    path = _write_xlsx(tmp_path, df)

    result = read_challenge_data(path)

    assert len(result) == 1
    assert result[0]["First Name"] == "Ada"


def test_phone_number_as_float_is_converted_without_trailing_zero(tmp_path):
    df = pd.DataFrame(
        {
            "First Name": ["Ada"],
            "Last Name": ["Lovelace"],
            "Company Name": ["Acme"],
            "Role in Company": ["Engineer"],
            "Address": ["123 St"],
            "Email": ["ada@example.com"],
            "Phone Number": [1234567890],  # numérico, não texto
        }
    )
    path = _write_xlsx(tmp_path, df)

    result = read_challenge_data(path)

    assert result[0]["Phone Number"] == "1234567890"
    assert not result[0]["Phone Number"].endswith(".0")


def test_phone_number_as_text_is_preserved(tmp_path):
    df = pd.DataFrame(
        {
            "First Name": ["Ada"],
            "Last Name": ["Lovelace"],
            "Company Name": ["Acme"],
            "Role in Company": ["Engineer"],
            "Address": ["123 St"],
            "Email": ["ada@example.com"],
            "Phone Number": ["555-1234"],
        }
    )
    path = _write_xlsx(tmp_path, df)

    result = read_challenge_data(path)

    assert result[0]["Phone Number"] == "555-1234"


def test_missing_required_column_raises_excel_validation_error(tmp_path):
    df = pd.DataFrame(
        {
            "First Name": ["Ada"],
            "Last Name": ["Lovelace"],
            "Company Name": ["Acme"],
            "Role in Company": ["Engineer"],
            "Address": ["123 St"],
            "Email": ["ada@example.com"],
            # "Phone Number" ausente de propósito
        }
    )
    path = _write_xlsx(tmp_path, df)

    with pytest.raises(ExcelValidationError, match="Phone Number"):
        read_challenge_data(path)


def test_nonexistent_file_raises_excel_validation_error(tmp_path):
    missing_path = tmp_path / "does_not_exist.xlsx"

    with pytest.raises(ExcelValidationError, match="não encontrado"):
        read_challenge_data(missing_path)


# ---- testes diretos de _normalize_phone ----


def test_normalize_phone_integer_float():
    assert _normalize_phone(1234567890.0) == "1234567890"


def test_normalize_phone_text():
    assert _normalize_phone("555-1234") == "555-1234"


def test_normalize_phone_nan_becomes_empty_string():
    assert _normalize_phone(float("nan")) == ""


def test_normalize_phone_none_becomes_empty_string():
    assert _normalize_phone(None) == ""
