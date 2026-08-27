"""Interações com o navegador (Playwright) para o RPA Challenge.

Estratégia de localização de campos: cada input é encontrado pelo atributo
`ng-reflect-name`, exposto pelo Angular (modo desenvolvimento) e que não
muda entre rodadas, mesmo com os campos trocando de posição na tela.
Nenhuma coordenada fixa é usada.
"""

import logging
import math
from pathlib import Path

from playwright.sync_api import Page

logger = logging.getLogger("rpa_challenge")

DOWNLOAD_LINK_NAME = "Download Excel"
START_BUTTON_NAME = "Start"
SUBMIT_SELECTOR = 'input[type="submit"]'
CONGRATULATIONS_SELECTOR = ".congratulations"
RESULT_MESSAGE_SELECTOR = ".message2"


def open_challenge(page: Page, url: str) -> None:
    """Navega até o RPA Challenge."""
    page.goto(url)
    logger.info("Site do desafio aberto: %s", url)


def download_challenge_excel(page: Page, dest_path: str | Path) -> Path:
    """Clica em 'Download Excel' e salva o arquivo em dest_path (caminho relativo ao projeto)."""
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    with page.expect_download() as download_info:
        page.get_by_role("link", name=DOWNLOAD_LINK_NAME).click()
    download = download_info.value
    download.save_as(str(dest_path))

    logger.info("Arquivo Excel baixado em: %s", dest_path)
    return dest_path


def click_start(page: Page) -> None:
    """Clica no botão Start para iniciar as 10 rodadas."""
    page.get_by_role("button", name=START_BUTTON_NAME).click()
    logger.info("Rodadas iniciadas (botão Start clicado)")


def fill_field(page: Page, ng_reflect_name: str, value: object) -> None:
    """Preenche um único campo, localizado pelo atributo ng-reflect-name.

    Função pequena e isolada de propósito: é o ponto natural para uma
    alteração pontual (ex.: trocar a estratégia de seletor) sem tocar no
    resto do fluxo.

    Células vazias em colunas obrigatórias chegam do pandas como `None` ou
    `NaN` (quando a linha tem outros campos preenchidos, `dropna(how="all")`
    não remove essa célula individual). Sem tratamento, `str(value)` gera
    literalmente "None"/"nan" digitado no formulário — por isso ambos os
    casos são normalizados para string vazia antes do fill.
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        text = ""
    else:
        text = str(value)

    selector = f'input[ng-reflect-name="{ng_reflect_name}"]'
    page.locator(selector).fill(text)


def fill_round(page: Page, row: dict[str, object], field_map: dict[str, str]) -> None:
    """Preenche todos os campos de uma rodada a partir de uma linha do Excel.

    Cada campo é preenchido dentro de seu próprio try/except só para registrar,
    com precisão, qual coluna/atributo falhou antes de propagar o erro (a
    execução continua fail-fast: nenhum retry é feito aqui).
    """
    for column, ng_reflect_name in field_map.items():
        try:
            fill_field(page, ng_reflect_name, row.get(column, ""))
        except Exception:
            logger.error(
                "Falha ao preencher o campo '%s' (ng-reflect-name=%s)",
                column,
                ng_reflect_name,
            )
            raise


def submit_round(page: Page) -> None:
    """Envia o formulário da rodada atual."""
    page.click(SUBMIT_SELECTOR)


def wait_for_final_screen(page: Page, timeout: int = 15000) -> str:
    """Espera a tela de conclusão (.congratulations) e devolve o texto de resultado."""
    page.wait_for_selector(CONGRATULATIONS_SELECTOR, timeout=timeout)
    return page.locator(RESULT_MESSAGE_SELECTOR).inner_text()


def capture_result(page: Page, path: str | Path) -> None:
    """Salva um screenshot da tela final como evidência."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path), full_page=True)
    logger.info("Screenshot do resultado salvo em: %s", path)
