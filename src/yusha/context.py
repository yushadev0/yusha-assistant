from __future__ import annotations

from dataclasses import dataclass

from telegram.ext import ContextTypes

from .config import AppConfig, Settings
from .docker_api import DockerApi
from .runner import CommandRunner

BOT_DATA_KEY = "ctx"


@dataclass
class AppContext:
    settings: Settings
    config: AppConfig
    docker: DockerApi
    runner: CommandRunner


def get_ctx(context: ContextTypes.DEFAULT_TYPE) -> AppContext:
    return context.application.bot_data[BOT_DATA_KEY]
