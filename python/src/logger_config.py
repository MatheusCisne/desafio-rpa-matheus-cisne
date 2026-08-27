"""Configuração de logging (arquivo + console) para a automação."""

import logging
from pathlib import Path


def configure_logging(log_file: str | Path) -> logging.Logger:
    """Cria/limpa o logger 'rpa_challenge' com saída em arquivo e console."""
    log_file = Path(log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("rpa_challenge")
    logger.setLevel(logging.INFO)

    # Fecha explicitamente os handlers de uma configuração anterior antes de
    # descartá-los: `.clear()` sozinho apenas remove as referências da lista,
    # sem liberar o descritor de arquivo do FileHandler antigo (vazamento de
    # recurso caso configure_logging seja chamado mais de uma vez).
    for handler in logger.handlers:
        handler.close()
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
