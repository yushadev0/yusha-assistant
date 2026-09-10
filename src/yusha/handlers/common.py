from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

log = logging.getLogger(__name__)

HELP = """<b>Yusha Assistant</b>

<b>İzleme</b>
/status — host CPU/RAM/disk + servis durumları
/ps — tüm container'lar
/logs &lt;servis&gt; [satır] — son loglar
/inspect &lt;servis&gt; — durum / çıkış kodu / restart sayısı

<b>Aksiyon</b>
/restart &lt;servis&gt; — onaylı yeniden başlatma
/run &lt;isim&gt; — tanımlı komutu çalıştır
/runs — tanımlı komutları listele

/help — bu mesaj"""


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(HELP, parse_mode=ParseMode.HTML)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(HELP, parse_mode=ParseMode.HTML)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.exception("Handler hatası", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(f"⚠️ Beklenmeyen hata: {context.error}")
