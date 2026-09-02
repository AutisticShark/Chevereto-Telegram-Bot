#!/usr/bin/env python3
"""Chevereto Telegram Bot - Modern async Telegram bot for Chevereto v4.x."""

from __future__ import annotations

import logging
import sys

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from chevereto_bot.client import CheveretoClient
from chevereto_bot.config import Config, load_config
from chevereto_bot.handlers.admin import (
    cache_clean_command,
    cache_status_command,
    storage_status_command,
    system_status_command,
    uptime_command,
)
from chevereto_bot.handlers.common import (
    album_command,
    help_command,
    login_command,
    logout_command,
    start_command,
    unknown_message,
    whoami_command,
)
from chevereto_bot.handlers.upload import handle_builtin_video_notice, handle_media_upload

logger = logging.getLogger("chevereto_bot")


def build_application(config: Config) -> Application:
    """Build and configure the Telegram Application instance."""
    app = Application.builder().token(config.bot.access_token).build()

    # Shared client and config stored in bot_data
    chevereto_client = CheveretoClient(
        endpoint_url=config.host.upload_url,
        api_key=config.host.image_host_api_key,
    )
    app.bot_data["config"] = config
    app.bot_data["chevereto_client"] = chevereto_client

    # User commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(CommandHandler("logout", logout_command))
    app.add_handler(CommandHandler("whoami", whoami_command))
    app.add_handler(CommandHandler("account", whoami_command))
    app.add_handler(CommandHandler("album", album_command))

    # Admin commands
    app.add_handler(CommandHandler("uptime", uptime_command))
    app.add_handler(CommandHandler("storage_status", storage_status_command))
    app.add_handler(CommandHandler("system_status", system_status_command))
    app.add_handler(CommandHandler("stats", system_status_command))
    app.add_handler(CommandHandler("cache_status", cache_status_command))
    app.add_handler(CommandHandler("cache_clean", cache_clean_command))

    # Built-in Telegram videos/animations notice (guide users to send as Document/File)
    app.add_handler(MessageHandler(filters.VIDEO | filters.ANIMATION, handle_builtin_video_notice))

    # Media uploads (photo or uncompressed document files only)
    media_filter = filters.PHOTO | filters.Document.ALL
    app.add_handler(MessageHandler(media_filter, handle_media_upload))

    # Fallback for unknown private text messages
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, unknown_message))

    return app


def main() -> int:
    """Main application bootstrap."""
    try:
        config = load_config()
    except Exception as err:
        print(f"Error loading configuration: {err}", file=sys.stderr)
        return 1

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=getattr(logging, config.logging_level.upper(), logging.INFO),
    )

    try:
        config.validate()
    except ValueError as err:
        logger.critical(str(err))
        return 1

    logger.info("Initializing Chevereto Telegram Bot (Mode: %s)...", config.bot.mode)
    logger.info("Target Chevereto host: %s", config.host.image_host)

    app = build_application(config)

    if config.bot.mode == "POLLING":
        logger.info("Starting bot in POLLING mode...")
        app.run_polling(drop_pending_updates=True)
    elif config.bot.mode == "WEBHOOK":
        webhook_url = config.bot.webhook_url
        if not webhook_url.startswith("http://") and not webhook_url.startswith("https://"):
            webhook_url = f"https://{webhook_url}"

        path = config.bot.webhook_secret_token or "webhook"
        full_webhook_url = f"{webhook_url.rstrip('/')}/{path}"

        logger.info(
            "Starting bot in WEBHOOK mode on %s:%d...",
            config.bot.webhook_listen,
            config.bot.webhook_port,
        )

        webhook_kwargs = {
            "listen": config.bot.webhook_listen,
            "port": config.bot.webhook_port,
            "url_path": path,
            "webhook_url": full_webhook_url,
            "secret_token": config.bot.webhook_secret_token or None,
            "drop_pending_updates": True,
        }

        if config.bot.webhook_ssl:
            webhook_kwargs["key"] = config.bot.webhook_key
            webhook_kwargs["cert"] = config.bot.webhook_cert

        app.run_webhook(**webhook_kwargs)
    else:
        logger.error("Unknown BOT MODE '%s'. Expected 'POLLING' or 'WEBHOOK'.", config.bot.mode)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
