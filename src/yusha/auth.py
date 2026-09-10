from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from telegram import Update
from telegram.ext import ApplicationHandlerStop, ContextTypes

log = logging.getLogger(__name__)

Guard = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]


def make_guard(admin_ids: set[int]) -> Guard:
    """group=-1'de TypeHandler olarak kaydedilir. Yetkisiz kullanıcı için
    ApplicationHandlerStop fırlatır; hiçbir komut handler'ı çalışmaz."""

    async def guard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if user is not None and user.id in admin_ids:
            return
        log.warning(
            "Yetkisiz erişim reddedildi: user_id=%s username=%s",
            getattr(user, "id", "?"),
            getattr(user, "username", "?"),
        )
        if update.effective_message is not None:
            await update.effective_message.reply_text("⛔ Yetkin yok.")
        raise ApplicationHandlerStop

    return guard
