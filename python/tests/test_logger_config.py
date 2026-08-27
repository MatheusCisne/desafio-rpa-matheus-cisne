"""Testes unitários para src/logger_config.py."""

import logging

from src.logger_config import configure_logging


def test_log_file_is_created(tmp_path):
    log_file = tmp_path / "logs" / "execucao.log"

    logger = configure_logging(log_file)
    logger.info("mensagem de teste")
    for handler in logger.handlers:
        handler.flush()

    assert log_file.exists()
    assert "mensagem de teste" in log_file.read_text(encoding="utf-8")


def test_configure_logging_attaches_file_and_console_handlers(tmp_path):
    log_file = tmp_path / "execucao.log"

    logger = configure_logging(log_file)

    assert len(logger.handlers) == 2
    handler_types = {type(h) for h in logger.handlers}
    assert logging.FileHandler in handler_types
    assert logging.StreamHandler in handler_types


def test_configure_logging_twice_does_not_duplicate_handlers(tmp_path):
    log_file_a = tmp_path / "a.log"
    log_file_b = tmp_path / "b.log"

    configure_logging(log_file_a)
    logger = configure_logging(log_file_b)

    assert len(logger.handlers) == 2


def test_configure_logging_closes_previous_handlers_on_reconfigure(tmp_path):
    """Achado de revisão: antes da correção, `logger.handlers.clear()` descartava
    a referência ao FileHandler antigo sem chamar `.close()`, vazando o
    descritor de arquivo (o arquivo de log antigo ficava aberto/travado
    indefinidamente). Reconfigurar o logger deve fechar os handlers antigos."""
    log_file_a = tmp_path / "a.log"
    log_file_b = tmp_path / "b.log"

    logger = configure_logging(log_file_a)
    old_file_handler = next(
        h for h in logger.handlers if isinstance(h, logging.FileHandler)
    )

    configure_logging(log_file_b)

    assert old_file_handler.stream is None or old_file_handler.stream.closed


def test_configure_logging_returns_same_named_logger(tmp_path):
    log_file = tmp_path / "execucao.log"

    logger = configure_logging(log_file)

    assert logger.name == "rpa_challenge"
    assert logger.level == logging.INFO
