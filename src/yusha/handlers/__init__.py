from __future__ import annotations

from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from .actions import on_callback, restart_cmd, run_cmd, runs_cmd
from .common import help_cmd, start_cmd
from .logs import inspect_cmd, logs_cmd
from .status import ps_cmd, status_cmd


def register(app: Application) -> None:
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("ps", ps_cmd))
    app.add_handler(CommandHandler("logs", logs_cmd))
    app.add_handler(CommandHandler("inspect", inspect_cmd))
    app.add_handler(CommandHandler("restart", restart_cmd))
    app.add_handler(CommandHandler("run", run_cmd))
    app.add_handler(CommandHandler("runs", runs_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))
