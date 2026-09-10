from __future__ import annotations

import asyncio

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ..context import get_ctx
from ..docker_api import DockerError
from ..formatting import code_block, esc, human_bytes, human_duration, state_emoji
from ..metrics import collect


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg is None:
        return
    ctx = get_ctx(context)

    metrics = await asyncio.to_thread(
        collect, ctx.settings.host_proc, ctx.settings.host_root
    )

    lines = [
        "<b>🖥️ Host</b>",
        f"CPU: {metrics.cpu_percent:.0f}%   yük: "
        f"{metrics.load1:.2f} / {metrics.load5:.2f} / {metrics.load15:.2f}",
        f"RAM: {human_bytes(metrics.mem_used)} / {human_bytes(metrics.mem_total)} "
        f"({metrics.mem_percent:.0f}%)",
        f"Swap: {human_bytes(metrics.swap_used)} / {human_bytes(metrics.swap_total)}",
        f"Disk: {human_bytes(metrics.disk_used)} / {human_bytes(metrics.disk_total)} "
        f"({metrics.disk_percent:.0f}%)",
        f"Uptime: {human_duration(metrics.uptime_seconds)}",
        "",
        "<b>📦 Servisler</b>",
    ]

    try:
        containers = await ctx.docker.list_containers()
    except DockerError as exc:
        lines.append(f"⚠️ {esc(exc)}")
        await msg.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
        return

    by_name = {c["name"]: c for c in containers}
    watched = ctx.config.services
    if watched:
        for svc in watched:
            c = by_name.get(svc.container)
            if c is None:
                lines.append(f"❔ <b>{esc(svc.name)}</b> — container yok ({esc(svc.container)})")
            else:
                lines.append(
                    f"{state_emoji(c['state'])} <b>{esc(svc.name)}</b> — "
                    f"{esc(c['status'] or c['state'])}"
                )
    else:
        for c in containers:
            lines.append(
                f"{state_emoji(c['state'])} <b>{esc(c['name'])}</b> — "
                f"{esc(c['status'] or c['state'])}"
            )

    await msg.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def ps_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg is None:
        return
    ctx = get_ctx(context)
    try:
        containers = await ctx.docker.list_containers()
    except DockerError as exc:
        await msg.reply_text(f"⚠️ {exc}")
        return
    if not containers:
        await msg.reply_text("Hiç container yok.")
        return
    rows = [
        f"{state_emoji(c['state'])} {c['name'][:24]:<24} {c['status']}" for c in containers
    ]
    await msg.reply_text(code_block("\n".join(rows)), parse_mode=ParseMode.HTML)
