"""Leitura e validação dos dados de challenge.xlsx."""

from pathlib import Path

import pandas as pd

from .constants import EXPECTED_COLUMNS


class ExcelValidationError(Exception):
    """Levantada quando o Excel não contém as colunas obrigatórias."""


def read_challenge_data(path: str | Path) -> list[dict]:
    """Lê o challenge.xlsx e devolve uma lista de dicts, uma por linha válida.

    - Aplica strip() nos cabeçalhos (ex.: "Last Name " -> "Last Name").
    - Valida que as 7 colunas esperadas existem.
    - Ignora a 8ª coluna fantasma e qualquer linha totalmente vazia
      (o arquivo declara ~999 linhas no metadado, mas só ~10 têm dados).
    - Converte "Phone Number" para string.
    """
    path = Path(path)
    if not path.exists():
        raise ExcelValidationError(f"Arquivo Excel não encontrado: {path}")

    df = pd.read_excel(path)
    df.columns = [str(column).strip() for column in df.columns]

    missing_columns = [column for column in EXPECTED_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ExcelValidationError(
            f"Colunas obrigatórias ausentes no Excel: {missing_columns}"
        )

    df = df[EXPECTED_COLUMNS].dropna(how="all")
    df["Phone Number"] = df["Phone Number"].apply(_normalize_phone)

    return df.to_dict(orient="records")


def _normalize_phone(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)
