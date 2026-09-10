from __future__ import annotations

import logging

from telegram import BotCommand, Update
from telegram.ext import Application, ApplicationBuilder, TypeHandler

from .auth import make_guard
from .config import Settings
from .context import BOT_DATA_KEY, AppContext
from .docker_api import DockerApi
from .handlers import register
from .handlers.common import on_error
from .runner import CommandRunner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
)
log = logging.getLogger("yusha")

_COMMANDS = [
    BotCommand("status", "Host + servis durumları"),
    BotCommand("ps", "Tüm container'lar"),
    BotCommand("logs", "Servis logları: /logs <servis> [satır]"),
    BotCommand("inspect", "Servis detayı: /inspect <servis>"),
    BotCommand("restart", "Servisi yeniden başlat (onaylı)"),
    BotCommand("run", "Tanımlı komut çalıştır: /run <isim>"),
    BotCommand("runs", "Tanımlı komutları listele"),
    BotCommand("help", "Yardım"),
]


async def _post_init(app: Application) -> None:
    await app.bot.set_my_commands(_COMMANDS)
    me = await app.bot.get_me()
    log.info("Bağlandı: @%s", me.username)


async def _post_shutdown(app: Application) -> None:
    ctx: AppContext = app.bot_data[BOT_DATA_KEY]
    await ctx.docker.close()


def build() -> Application:
    settings = Settings()  # type: ignore[call-arg]  # değerler ortam/.env'den
    config = settings.load_app_config()
    docker = DockerApi(settings.docker_host)
    ctx = AppContext(
        settings=settings,
        config=config,
        docker=docker,
        runner=CommandRunner(settings, docker),
    )

    app = (
        ApplicationBuilder()
        .token(settings.bot_token)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )
    app.bot_data[BOT_DATA_KEY] = ctx
    app.add_handler(TypeHandler(Update, make_guard(set(settings.admin_ids))), group=-1)
    register(app)
    app.add_error_handler(on_error)

    log.info(
        "Yapılandırma: %d servis, %d komut, ssh=%s, admin=%s",
        len(config.services),
        len(config.commands),
        "açık" if settings.ssh_enabled else "kapalı",
        settings.admin_ids,
    )
    return app


def main() -> None:
    app = build()
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
