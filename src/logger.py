"""
Sistema de logging para o aplicativo
Registra erros, ações e debug em arquivo
"""

import logging
import os
from datetime import datetime

LOGGER = None


def _criar_logger():
    global LOGGER
    if LOGGER is not None:
        return LOGGER

    pasta_app = os.path.expanduser("~/.autodoc")
    os.makedirs(pasta_app, exist_ok=True)

    log_path = os.path.join(pasta_app, "app.log")

    LOGGER = logging.getLogger("AutoDoc")
    LOGGER.setLevel(logging.DEBUG)

    if LOGGER.handlers:
        return LOGGER

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    fh.setFormatter(formatter)
    LOGGER.addHandler(fh)

    LOGGER.info("=" * 50)
    LOGGER.info("autodoc iniciado")
    LOGGER.info("=" * 50)

    return LOGGER


def get_logger():
    return _criar_logger()


def log_info(msg):
    get_logger().info(msg)


def log_erro(msg):
    get_logger().error(msg)


def log_warning(msg):
    get_logger().warning(msg)


def log_debug(msg):
    get_logger().debug(msg)
