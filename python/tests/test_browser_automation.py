"""Testes unitários para src/browser_automation.py.

Como todas as funções recebem um `Page` do Playwright, usamos Mock/MagicMock
para simular `Page`/`Locator` e testar a lógica sem abrir navegador nenhum.
"""

import logging
from unittest.mock import MagicMock, Mock, call

import pytest

from src import browser_automation as browser
from src.constants import FIELD_MAP


# ---------------------------------------------------------------------------
# fill_field
# ---------------------------------------------------------------------------


def test_fill_field_builds_correct_selector_and_fills_value():
    page = Mock()
    locator = Mock()
    page.locator.return_value = locator

    browser.fill_field(page, "labelFirstName", "Ada")

    page.locator.assert_called_once_with('input[ng-reflect-name="labelFirstName"]')
    locator.fill.assert_called_once_with("Ada")


def test_fill_field_converts_non_string_value_to_str():
    page = Mock()
    locator = Mock()
    page.locator.return_value = locator

    browser.fill_field(page, "labelPhone", 1234567890)

    locator.fill.assert_called_once_with("1234567890")


def test_fill_field_converts_none_to_empty_string():
    page = Mock()
    locator = Mock()
    page.locator.return_value = locator

    browser.fill_field(page, "labelRole", None)

    locator.fill.assert_called_once_with("")


def test_fill_field_converts_nan_to_empty_string():
    """Célula vazia (não a linha inteira) em uma coluna obrigatória chega como
    NaN (float) vindo do pandas. Preencher literalmente "nan" no formulário
    seria um bug — o campo deve ficar vazio."""
    page = Mock()
    locator = Mock()
    page.locator.return_value = locator

    browser.fill_field(page, "labelCompanyName", float("nan"))

    locator.fill.assert_called_once_with("")


# ---------------------------------------------------------------------------
# fill_round
# ---------------------------------------------------------------------------


def test_fill_round_calls_fill_field_once_per_column_in_order(monkeypatch):
    page = Mock()
    mock_fill_field = Mock()
    monkeypatch.setattr(browser, "fill_field", mock_fill_field)

    row = {column: f"value-{column}" for column in FIELD_MAP}

    browser.fill_round(page, row, FIELD_MAP)

    expected_calls = [
        call(page, ng_reflect_name, row[column])
        for column, ng_reflect_name in FIELD_MAP.items()
    ]
    assert mock_fill_field.call_args_list == expected_calls


def test_fill_round_uses_empty_string_default_for_missing_column(monkeypatch):
    page = Mock()
    mock_fill_field = Mock()
    monkeypatch.setattr(browser, "fill_field", mock_fill_field)

    field_map = {"First Name": "labelFirstName"}
    row = {}  # coluna ausente do dict

    browser.fill_round(page, row, field_map)

    mock_fill_field.assert_called_once_with(page, "labelFirstName", "")


def test_fill_round_logs_and_reraises_exception(monkeypatch, caplog):
    page = Mock()

    def fake_fill_field(page, ng_reflect_name, value):
        if ng_reflect_name == "labelLastName":
            raise RuntimeError("elemento não encontrado")

    monkeypatch.setattr(browser, "fill_field", fake_fill_field)

    row = dict.fromkeys(FIELD_MAP, "x")

    with (
        caplog.at_level(logging.ERROR, logger="rpa_challenge"),
        pytest.raises(RuntimeError, match="elemento não encontrado"),
    ):
        browser.fill_round(page, row, FIELD_MAP)

    assert any("Last Name" in record.message for record in caplog.records)
    assert any("labelLastName" in record.message for record in caplog.records)


# ---------------------------------------------------------------------------
# submit_round / open_challenge / click_start
# ---------------------------------------------------------------------------


def test_submit_round_clicks_submit_selector():
    page = Mock()

    browser.submit_round(page)

    page.click.assert_called_once_with(browser.SUBMIT_SELECTOR)


def test_open_challenge_navigates_to_url():
    page = Mock()

    browser.open_challenge(page, "https://rpachallenge.com/")

    page.goto.assert_called_once_with("https://rpachallenge.com/")


def test_click_start_clicks_start_button():
    page = Mock()
    button = Mock()
    page.get_by_role.return_value = button

    browser.click_start(page)

    page.get_by_role.assert_called_once_with("button", name=browser.START_BUTTON_NAME)
    button.click.assert_called_once()


# ---------------------------------------------------------------------------
# wait_for_final_screen
# ---------------------------------------------------------------------------


def test_wait_for_final_screen_waits_and_returns_message():
    page = Mock()
    message_locator = Mock()
    message_locator.inner_text.return_value = "Congratulations! You are done!"
    page.locator.return_value = message_locator

    result = browser.wait_for_final_screen(page, timeout=5000)

    page.wait_for_selector.assert_called_once_with(
        browser.CONGRATULATIONS_SELECTOR, timeout=5000
    )
    page.locator.assert_called_once_with(browser.RESULT_MESSAGE_SELECTOR)
    assert result == "Congratulations! You are done!"


# ---------------------------------------------------------------------------
# download_challenge_excel / capture_result (testes leves)
# ---------------------------------------------------------------------------


def test_download_challenge_excel_clicks_link_and_saves_file(tmp_path):
    page = MagicMock()
    download = Mock()
    page.expect_download.return_value.__enter__.return_value.value = download
    link = Mock()
    page.get_by_role.return_value = link

    dest = tmp_path / "subdir" / "challenge.xlsx"
    result = browser.download_challenge_excel(page, dest)

    page.get_by_role.assert_called_once_with("link", name=browser.DOWNLOAD_LINK_NAME)
    link.click.assert_called_once()
    download.save_as.assert_called_once_with(str(dest))
    assert dest.parent.exists()
    assert result == dest


def test_capture_result_takes_full_page_screenshot(tmp_path):
    page = Mock()
    dest = tmp_path / "evidencias" / "resultado.png"

    browser.capture_result(page, dest)

    page.screenshot.assert_called_once_with(path=str(dest), full_page=True)
    assert dest.parent.exists()
