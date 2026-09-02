"""Common Telegram command and fallback handlers."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from chevereto_bot.config import Config

logger = logging.getLogger(__name__)


def is_user_logged_in(user_id: int, context: ContextTypes.DEFAULT_TYPE, config: Config) -> bool:
    """Check if user has provided personal API key or is admin."""
    return bool(context.user_data.get("api_key")) or config.is_user_admin(user_id)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if not update.effective_message or not update.effective_user:
        return

    config: Config = context.bot_data["config"]
    user_id = update.effective_user.id

    if not config.is_user_allowed(user_id):
        await update.effective_message.reply_text(
            "⛔ <b>Access Denied</b>\n\nYou are not authorized to use this bot.",
            parse_mode=ParseMode.HTML,
        )
        return

    text = (
        "👋 <b>Welcome to Chevereto Bot!</b>\n\n"
        "Send photos or document files to upload directly to your Chevereto v4 site.\n"
        "<i>Note: Videos should be sent as uncompressed Files/Documents (📎 &gt; File).</i>\n\n"
        "<b>User Commands:</b>\n"
        "• /login <code>&lt;api_key&gt;</code> - Log in with personal Chevereto API key\n"
        "• /logout - Clear your personal session\n"
        "• /whoami - Check your login status\n"
        "• /album <code>&lt;id&gt;</code> - Set target album (logged-in users)\n"
        "• /help - View server limits and usage guide\n"
    )
    if config.is_user_admin(user_id):
        text += (
            "\n<b>Admin Commands:</b>\n"
            "• /uptime - System uptime\n"
            "• /storage_status - Disk usage\n"
            "• /system_status - Full system overview\n"
        )

    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    if not update.effective_message:
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING,
    )

    config: Config = context.bot_data["config"]
    formats_str = ", ".join(sorted(config.host.allowed_file_formats))
    active_album = (
        context.user_data.get("album_id") or config.host.album_id or "None (Default stream)"
    )
    has_key = bool(context.user_data.get("api_key"))
    auth_mode = "Personal Account" if has_key else "Default Bot Account"

    video_status = "Enabled (via File only)" if config.host.enable_video else "Disabled"
    help_text = (
        "📷 <b>Chevereto Telegram Bot Help</b>\n\n"
        f"🌐 <b>Host:</b> <code>{config.host.image_host}</code>\n"
        f"🔑 <b>Session:</b> <i>{auth_mode}</i>\n"
        f"📁 <b>Target Album:</b> <code>{active_album}</code>\n"
        f"📦 <b>Max File Size:</b> {config.host.max_file_size_mb} MB\n"
        f"🎬 <b>Video Uploads:</b> {video_status}\n"
        f"📄 <b>Allowed Formats:</b>\n{formats_str}\n\n"
        "<b>How to Upload:</b>\n"
        "• <b>Photos:</b> Send directly or as a file.\n"
        "• <b>Videos/GIFs:</b> Send as uncompressed <b>File / Document</b> (📎 &gt; File).\n\n"
        "<b>Account & Albums:</b>\n"
        "• Use <code>/login &lt;api_key&gt;</code> to link your personal Chevereto account.\n"
        "• Use <code>/album &lt;id&gt;</code> to upload directly to your personal album."
    )

    await update.effective_message.reply_text(help_text, parse_mode=ParseMode.HTML)


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /login <api_key> to set user personal API key."""
    if not update.effective_message or not update.effective_user:
        return

    config: Config = context.bot_data["config"]
    if not config.is_user_allowed(update.effective_user.id):
        return

    args = context.args or []
    if not args:
        await update.effective_message.reply_text(
            "ℹ️ <b>How to Log In:</b>\n\n"
            "1. Go to your Chevereto site > <b>User Settings &gt; API</b>.\n"
            "2. Generate or copy your personal API key.\n"
            "3. Send: <code>/login &lt;your_personal_api_key&gt;</code>\n\n"
            "<i>Your message containing the key will be deleted automatically for security.</i>",
            parse_mode=ParseMode.HTML,
        )
        return

    key = args[0].strip()

    # Delete the message containing the secret key for privacy/security
    try:
        await update.effective_message.delete()
    except Exception:
        pass

    context.user_data["api_key"] = key
    masked_key = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "***"

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "✅ <b>Logged In Successfully!</b>\n\n"
            f"Active personal API key: <code>{masked_key}</code>\n"
            "Uploads will now be associated with your personal Chevereto account.\n"
            "You can now set a personal target album using <code>/album &lt;id&gt;</code>."
        ),
        parse_mode=ParseMode.HTML,
    )


async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /logout to remove personal API key and session album."""
    if not update.effective_message:
        return

    had_key = bool(context.user_data.pop("api_key", None))
    context.user_data.pop("album_id", None)

    if had_key:
        await update.effective_message.reply_text(
            "✅ <b>Logged Out</b>\n\nPersonal API key and album settings have been cleared.",
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.effective_message.reply_text(
            "ℹ️ You were not logged in with a personal API key.",
            parse_mode=ParseMode.HTML,
        )


async def whoami_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /whoami to display active session information."""
    if not update.effective_message or not update.effective_user:
        return

    config: Config = context.bot_data["config"]
    user_id = update.effective_user.id
    personal_key = context.user_data.get("api_key")
    album_id = context.user_data.get("album_id") or config.host.album_id or "Default stream"

    if personal_key:
        masked = f"{personal_key[:4]}...{personal_key[-4:]}" if len(personal_key) > 8 else "***"
        auth_info = f"Logged in with personal API key (<code>{masked}</code>)"
    elif config.is_user_admin(user_id):
        auth_info = "Bot Administrator (Host Master Key)"
    else:
        auth_info = "Default Bot Guest / Public Key"

    await update.effective_message.reply_text(
        f"👤 <b>Session Status:</b>\n"
        f"• Telegram User ID: <code>{user_id}</code>\n"
        f"• Account: {auth_info}\n"
        f"• Active Album: <code>{album_id}</code>",
        parse_mode=ParseMode.HTML,
    )


async def album_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /album command for logged-in users."""
    if not update.effective_message or not update.effective_user:
        return

    config: Config = context.bot_data["config"]
    user_id = update.effective_user.id
    if not config.is_user_allowed(user_id):
        return

    # Check if user is logged in
    if not is_user_logged_in(user_id, context, config):
        await update.effective_message.reply_text(
            "⚠️ <b>Login Required</b>\n\n"
            "Album switching is only available for logged-in users with personal API keys.\n\n"
            "To log in, obtain your API key from your Chevereto site (<b>Settings &gt; API</b>) "
            "and send:\n<code>/login &lt;your_api_key&gt;</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    args = context.args or []
    if not args:
        current_album = (
            context.user_data.get("album_id")
            or config.host.album_id
            or "Not set (uploads to personal stream)"
        )
        await update.effective_message.reply_text(
            f"📁 <b>Current Target Album:</b> <code>{current_album}</code>\n\n"
            f"To change it, send: <code>/album &lt;album_id&gt;</code>\n"
            f"To reset to default, send: <code>/album clear</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    subcommand = args[0].strip()
    if subcommand.lower() in {"clear", "reset", "none"}:
        context.user_data.pop("album_id", None)
        await update.effective_message.reply_text(
            "✅ Target album reset to default.",
            parse_mode=ParseMode.HTML,
        )
    else:
        context.user_data["album_id"] = subcommand
        await update.effective_message.reply_text(
            f"✅ Target album set to: <code>{subcommand}</code>",
            parse_mode=ParseMode.HTML,
        )


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown text messages in private chats."""
    if not update.effective_message or not update.effective_user:
        return

    config: Config = context.bot_data["config"]
    if not config.is_user_allowed(update.effective_user.id):
        return

    await update.effective_message.reply_text(
        "ℹ️ Send me a photo or document file to upload it.\n"
        "Send videos as uncompressed <b>Files</b> (📎 &gt; File).\n"
        "Type /help for more options.",
        parse_mode=ParseMode.HTML,
    )
