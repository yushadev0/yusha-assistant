from __future__ import annotations

from collections.abc import Awaitable, Callable

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ..context import AppContext, get_ctx
from ..docker_api import DockerError
from ..formatting import code_block, esc

TG_LIMIT = 3900

Sender = Callable[..., Awaitable[object]]


def _confirm_kb(action: str, name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Evet", callback_data=f"{action}:{name}"),
                InlineKeyboardButton("❌ İptal", callback_data="cancel"),
            ]
        ]
    )


# ---------------------------------------------------------------- /restart


async def restart_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg is None:
        return
    ctx = get_ctx(context)
    if not context.args:
        await msg.reply_text("Kullanım: /restart <servis>")
        return

    name = context.args[0]
    svc = ctx.config.service(name)
    if svc is None or "restart" not in svc.actions:
        await msg.reply_text("Bu servis için restart tanımlı değil (config.yaml → actions).")
        return

    await msg.reply_text(
        f"<b>{esc(name)}</b> yeniden başlatılsın mı?",
        reply_markup=_confirm_kb("restart", name),
        parse_mode=ParseMode.HTML,
    )


# ---------------------------------------------------------------- /run(s)


async def runs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg is None:
        return
    ctx = get_ctx(context)
    if not ctx.config.commands:
        await msg.reply_text("Tanımlı komut yok (config.yaml → commands).")
        return
    lines = ["<b>Tanımlı komutlar</b>"]
    for c in ctx.config.commands:
        tail = f" — {esc(c.description)}" if c.description else ""
        flag = " 🔒" if c.confirm else ""
        lines.append(f"• <code>{esc(c.name)}</code> [{esc(c.target)}]{flag}{tail}")
    lines.append("\nÇalıştır: <code>/run &lt;isim&gt;</code>")
    await msg.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def run_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg is None:
        return
    ctx = get_ctx(context)
    if not context.args:
        await msg.reply_text("Kullanım: /run <isim>   ·   liste: /runs")
        return

    cmd = ctx.config.command(context.args[0])
    if cmd is None:
        await msg.reply_text("Bilinmeyen komut. /runs ile listele.")
        return

    if cmd.confirm:
        await msg.reply_text(
            f"<code>{esc(cmd.name)}</code> çalıştırılsın mı?\n"
            f"{code_block(' '.join(cmd.argv))}",
            reply_markup=_confirm_kb("run", cmd.name),
            parse_mode=ParseMode.HTML,
        )
        return

    await _execute_run(msg.reply_text, ctx, cmd.name)


async def _execute_run(send: Sender, ctx: AppContext, cmd_name: str) -> None:
    cmd = ctx.config.command(cmd_name)
    if cmd is None:
        await send("Komut artık tanımlı değil.")
        return
    res = await ctx.runner.run(cmd)
    head = "✅" if res.ok else f"❌ (exit {res.exit_code})"
    out = res.output.strip() or "(çıktı yok)"
    if len(out) > TG_LIMIT:
        out = out[:TG_LIMIT] + "\n…(kısaltıldı)"
    await send(
        f"{head} <code>{esc(cmd_name)}</code>\n{code_block(out)}",
        parse_mode=ParseMode.HTML,
    )


# ---------------------------------------------------------------- callback butonları


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    ctx = get_ctx(context)
    data = query.data or ""

    if data == "cancel":
        await query.edit_message_text("İptal edildi.")
        return

    if data.startswith("restart:"):
        name = data.split(":", 1)[1]
        svc = ctx.config.service(name)
        if svc is None or "restart" not in svc.actions:
            await query.edit_message_text("Servis artık tanımlı değil.")
            return
        await query.edit_message_text(
            f"♻️ {esc(name)} yeniden başlatılıyor…", parse_mode=ParseMode.HTML
        )
        try:
            await ctx.docker.restart(svc.container)
        except DockerError as exc:
            await query.edit_message_text(f"⚠️ {exc}")
            return
        await query.edit_message_text(
            f"✅ {esc(name)} yeniden başlatıldı.", parse_mode=ParseMode.HTML
        )
        return

    if data.startswith("run:"):
        await _execute_run(query.edit_message_text, ctx, data.split(":", 1)[1])
        return
