from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ..context import AppContext, get_ctx
from ..docker_api import DockerError
from ..formatting import code_block, esc

TG_LIMIT = 3900


def _resolve(ctx: AppContext, token: str) -> str | None:
    """Servis adı ya da bilinen container adını gerçek container adına çevirir."""
    svc = ctx.config.service(token)
    if svc is not None:
        return svc.container
    if ctx.config.service_by_container(token) is not None:
        return token
    return None


def _known_services(ctx: AppContext) -> str:
    return ", ".join(s.name for s in ctx.config.services) or "(config.yaml'da servis yok)"


async def logs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg is None:
        return
    ctx = get_ctx(context)
    if not context.args:
        await msg.reply_text("Kullanım: /logs <servis> [satır]")
        return

    token = context.args[0]
    tail = ctx.settings.log_tail_default
    if len(context.args) > 1 and context.args[1].isdigit():
        tail = min(int(context.args[1]), ctx.settings.log_tail_max)

    container = _resolve(ctx, token)
    if container is None:
        await msg.reply_text(f"Bilinmeyen servis. Tanımlı: {_known_services(ctx)}")
        return

    try:
        text = await ctx.docker.logs(container, tail)
    except DockerError as exc:
        await msg.reply_text(f"⚠️ {exc}")
        return

    text = text.strip() or "(log boş)"
    if len(text) > TG_LIMIT:
        text = "…" + text[-TG_LIMIT:]
    await msg.reply_text(
        f"<b>{esc(token)}</b> — son {tail} satır\n{code_block(text)}",
        parse_mode=ParseMode.HTML,
    )


async def inspect_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg is None:
        return
    ctx = get_ctx(context)
    if not context.args:
        await msg.reply_text("Kullanım: /inspect <servis>")
        return

    token = context.args[0]
    container = _resolve(ctx, token)
    if container is None:
        await msg.reply_text(f"Bilinmeyen servis. Tanımlı: {_known_services(ctx)}")
        return

    try:
        info = await ctx.docker.inspect(container)
    except DockerError as exc:
        await msg.reply_text(f"⚠️ {exc}")
        return

    lines = [
        f"<b>{esc(token)}</b>",
        f"durum: {esc(info['state'])}",
        f"çıkış kodu: {esc(info['exit_code'])}",
        f"restart sayısı: {esc(info['restart_count'])}",
    ]
    if info["health"]:
        lines.append(f"health: {esc(info['health'])}")
    if info["error"]:
        lines.append(f"hata: {esc(info['error'])}")
    lines.append(f"başladı: {esc(info['started_at'])}")
    if info["state"] != "running":
        lines.append(f"bitti: {esc(info['finished_at'])}")
    await msg.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
