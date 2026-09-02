"""Admin command handlers."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from chevereto_bot.config import Config
from chevereto_bot.utils.media import format_file_size
from chevereto_bot.utils.system import get_storage_status, get_system_overview, get_system_uptime

logger = logging.getLogger(__name__)


def _is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    config: Config = context.bot_data.get("config")
    user_id = update.effective_user.id if update.effective_user else 0
    return config.is_user_admin(user_id) if config else False


async def uptime_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Report system uptime."""
    if not update.effective_message:
        return
    if not _is_admin(update, context):
        await update.effective_message.reply_text("⛔ Admin permission required.")
        return

    uptime_text = get_system_uptime()
    await update.effective_message.reply_text(f"⏱️ {uptime_text}")


async def storage_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Report storage status for host machine."""
    if not update.effective_message:
        return
    if not _is_admin(update, context):
        await update.effective_message.reply_text("⛔ Admin permission required.")
        return

    storage_text = get_storage_status()
    await update.effective_message.reply_text(f"💾 {storage_text}")


async def system_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Report overall system overview (CPU, memory, disk, uptime)."""
    if not update.effective_message:
        return
    if not _is_admin(update, context):
        await update.effective_message.reply_text("⛔ Admin permission required.")
        return

    overview = get_system_overview()
    await update.effective_message.reply_text(overview)


async def cache_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Report cache status (for legacy cache directory)."""
    if not update.effective_message:
        return
    if not _is_admin(update, context):
        await update.effective_message.reply_text("⛔ Admin permission required.")
        return

    cache_dir = Path("cache")
    if not cache_dir.exists():
        await update.effective_message.reply_text(
            "🧹 <b>Cache Status:</b>\n"
            "Cache is clean. Modern bot processes uploads in-memory with zero disk leaks.",
            parse_mode=ParseMode.HTML,
        )
        return

    files = [f for f in cache_dir.iterdir() if f.is_file()]
    total_size = sum(f.stat().st_size for f in files)

    await update.effective_message.reply_text(
        f"🧹 <b>Cache Status:</b>\n"
        f"Files: {len(files)}\n"
        f"Size: {format_file_size(total_size)}\n"
        f"<i>Note: Modern uploads are processed with zero-leak streaming.</i>",
        parse_mode=ParseMode.HTML,
    )


async def cache_clean_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clean legacy cache directory."""
    if not update.effective_message:
        return
    if not _is_admin(update, context):
        await update.effective_message.reply_text("⛔ Admin permission required.")
        return

    cache_dir = Path("cache")
    count = 0
    if cache_dir.exists():
        for f in cache_dir.iterdir():
            if f.is_file():
                try:
                    os.remove(f)
                    count += 1
                except OSError as err:
                    logger.warning("Failed to remove cached file %s: %s", f, err)

    await update.effective_message.reply_text(f"✅ Cleared {count} legacy cache file(s).")
