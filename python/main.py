"""Ponto de entrada: automatiza o RPA Challenge (rpachallenge.com) do início ao fim.

Fluxo:
1. Abre o site e baixa o challenge.xlsx.
2. Lê e valida os dados do Excel.
3. Clica em Start e percorre uma linha por vez, preenchendo cada campo
   pelo atributo ng-reflect-name (não pela posição na tela).
4. Envia cada rodada até a tela de conclusão aparecer.
5. Salva um screenshot do resultado final em evidencias/resultado-python.png.

Uso:
    python main.py
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from src import browser_automation as browser
from src.constants import CHALLENGE_URL, FIELD_MAP, TOTAL_ROUNDS
from src.excel_reader import ExcelValidationError, read_challenge_data
from src.logger_config import configure_logging

PYTHON_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PYTHON_DIR.parent

EXCEL_PATH = PYTHON_DIR / "data" / "challenge.xlsx"
LOG_PATH = PYTHON_DIR / "logs" / "execucao.log"
EVIDENCE_PATH = PROJECT_ROOT / "evidencias" / "resultado-python.png"

# RPA_HEADLESS=1 forca modo headless (util para CI/sandboxes sem display).
# Padrao: headed (visivel).
HEADLESS = os.environ.get("RPA_HEADLESS", "").strip().lower() in {"1", "true", "yes"}

# RPA_BROWSER_CHANNEL=msedge usa o Edge do sistema em vez do Chromium do
# Playwright (ver README: workaround para uma falha de ativacao do Chromium
# em algumas instalacoes do Windows). Padrao: Chromium do Playwright.
BROWSER_CHANNEL = os.environ.get("RPA_BROWSER_CHANNEL", "").strip() or None


def main() -> int:
    logger = configure_logging(LOG_PATH)
    logger.info("=== Iniciando automação do RPA Challenge ===")

    with sync_playwright() as playwright:
        chromium = playwright.chromium.launch(headless=HEADLESS, channel=BROWSER_CHANNEL)
        page = chromium.new_page()

        try:
            browser.open_challenge(page, CHALLENGE_URL)
            browser.download_challenge_excel(page, EXCEL_PATH)

            data = read_challenge_data(EXCEL_PATH)
            logger.info("%d linha(s) válida(s) encontradas no Excel", len(data))

            if len(data) != TOTAL_ROUNDS:
                logger.warning(
                    "Esperava %d linhas, mas o Excel tem %d. Continuando mesmo assim.",
                    TOTAL_ROUNDS,
                    len(data),
                )

            browser.click_start(page)

            for index, row in enumerate(data, start=1):
                logger.info("Preenchendo rodada %d/%d", index, len(data))
                try:
                    browser.fill_round(page, row, FIELD_MAP)
                    browser.submit_round(page)
                except Exception:
                    logger.error("Falha na rodada %d/%d", index, len(data))
                    raise

            result_message = browser.wait_for_final_screen(page)
            logger.info("Desafio concluído: %s", result_message)

            browser.capture_result(page, EVIDENCE_PATH)

        except ExcelValidationError:
            logger.exception("Falha na validação do Excel. Encerrando.")
            return 1
        except Exception:
            logger.exception("Erro inesperado durante a automação. Encerrando.")
            return 1
        finally:
            chromium.close()

    logger.info("=== Execução finalizada com sucesso ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
