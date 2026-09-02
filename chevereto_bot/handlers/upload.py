"""Upload handlers for photos and documents with video detection."""

from __future__ import annotations

import io
import logging
import uuid

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from chevereto_bot.client import (
    CheveretoAuthError,
    CheveretoClient,
    CheveretoUploadError,
    CheveretoVideoDisabledError,
)
from chevereto_bot.config import Config
from chevereto_bot.utils.formatters import format_upload_response
from chevereto_bot.utils.media import detect_media_info, format_file_size, is_media_allowed

logger = logging.getLogger(__name__)

# Standard Telegram Bot API file download limit is 20MB
TELEGRAM_DOWNLOAD_LIMIT_BYTES = 20 * 1024 * 1024


async def handle_builtin_video_notice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inform users that videos should be sent as uncompressed files/documents."""
    message = update.effective_message
    if not message:
        return

    config: Config = context.bot_data["config"]
    user = update.effective_user
    if user and not config.is_user_allowed(user.id):
        return

    await message.reply_text(
        "ℹ️ <b>Video Upload via File Only</b>\n\n"
        "To upload a video or GIF, please send it as an uncompressed <b>File / Document</b> "
        "(📎 <b>Attachment &gt; File</b>) instead of a built-in Telegram video.\n\n"
        "This ensures maximum quality without Telegram re-encoding.",
        parse_mode=ParseMode.HTML,
    )


async def handle_media_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for photo and document uploads."""
    message = update.effective_message
    user = update.effective_user
    if not message or not user:
        return

    config: Config = context.bot_data["config"]
    if not config.is_user_allowed(user.id):
        await message.reply_text(
            "⛔ <b>Access Denied</b>\n\nYou are not authorized to upload to this bot.",
            parse_mode=ParseMode.HTML,
        )
        return

    # Identify the media object (photos or documents only)
    file_id: str | None = None
    file_size: int | None = None
    hint_filename: str | None = None
    hint_mime: str | None = None

    if message.photo:
        photo = message.photo[-1]
        file_id = photo.file_id
        file_size = photo.file_size
        hint_filename = f"{uuid.uuid4().hex}.jpg"
        hint_mime = "image/jpeg"
    elif message.document:
        doc = message.document
        file_id = doc.file_id
        file_size = doc.file_size
        hint_filename = doc.file_name or f"{uuid.uuid4().hex}.bin"
        hint_mime = doc.mime_type
    else:
        return

    # Check file size limit
    max_size_bytes = min(config.host.max_file_size_mb * 1024 * 1024, TELEGRAM_DOWNLOAD_LIMIT_BYTES)
    if file_size and file_size > max_size_bytes:
        limit_str = format_file_size(max_size_bytes)
        current_str = format_file_size(file_size)
        await message.reply_text(
            f"❌ <b>File too large:</b> {current_str}\n"
            f"The maximum allowed file size is {limit_str}.",
            parse_mode=ParseMode.HTML,
        )
        return

    await context.bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.UPLOAD_DOCUMENT)
    status_msg = await message.reply_text(
        "⏳ <i>Downloading media from Telegram...</i>", parse_mode=ParseMode.HTML
    )

    try:
        # In-memory streaming download
        buffer = io.BytesIO()
        tg_file = await context.bot.get_file(file_id)
        await tg_file.download_to_memory(buffer)
        buffer.seek(0)
        content = buffer.getvalue()

        # Sniff media type using pure-Python detection
        detected_mime, detected_ext = detect_media_info(
            content=content,
            hint_filename=hint_filename,
            hint_mime=hint_mime,
        )
        is_video = detected_mime.startswith("video/") or detected_ext in {
            ".mp4",
            ".webm",
            ".mov",
            ".mkv",
        }

        # Check if video uploads are disabled in bot configuration
        if is_video and not config.host.enable_video:
            await status_msg.edit_text(
                "❌ <b>Video Uploads Disabled</b>\n\n"
                "Video uploads are currently disabled on this bot.",
                parse_mode=ParseMode.HTML,
            )
            return

        # Check if we previously detected that the host does not have video enabled
        if is_video and context.bot_data.get("host_video_enabled") is False:
            await status_msg.edit_text(
                "❌ <b>Video Uploads Disabled on Host</b>\n\n"
                "The Chevereto host has not enabled video uploads (requires Chevereto v4.1+ "
                "with FFmpeg and video extensions enabled in Admin Dashboard).",
                parse_mode=ParseMode.HTML,
            )
            return

        # Check allowed mime/format
        if not is_media_allowed(
            mime=detected_mime,
            ext=detected_ext,
            allowed_mimes=config.host.allowed_file_mimes,
            allowed_formats=config.host.allowed_file_formats,
        ):
            allowed_str = ", ".join(sorted(config.host.allowed_file_formats))
            await status_msg.edit_text(
                f"❌ <b>Unsupported file format</b>\n"
                f"(<code>{detected_mime}</code> / <code>{detected_ext}</code>)\n\n"
                f"Allowed formats: {allowed_str}",
                parse_mode=ParseMode.HTML,
            )
            return

        await status_msg.edit_text("⏳ <i>Uploading to Chevereto...</i>", parse_mode=ParseMode.HTML)

        # Resolve personal API key if logged in, otherwise default host API key
        user_api_key = context.user_data.get("api_key") or config.host.image_host_api_key

        # Resolve target album (session override or global default)
        target_album = context.user_data.get("album_id") or config.host.album_id
        caption = message.caption.strip() if message.caption else None

        # Build clean upload filename
        base_name = hint_filename if hint_filename else uuid.uuid4().hex
        if not base_name.lower().endswith(detected_ext.lower()):
            final_filename = f"{base_name.rsplit('.', 1)[0]}{detected_ext}"
        else:
            final_filename = base_name

        client: CheveretoClient = context.bot_data["chevereto_client"]
        media = await client.upload(
            file_content=content,
            filename=final_filename,
            mime_type=detected_mime,
            title=caption,
            album_id=target_album,
            category_id=config.host.category_id,
            expiration=config.host.expiration,
            nsfw=config.host.nsfw,
            api_key=user_api_key,
        )

        # Successfully uploaded video - host has video support enabled
        if is_video:
            context.bot_data["host_video_enabled"] = True

        reply_text, keyboard = format_upload_response(media)
        await status_msg.edit_text(
            text=reply_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            disable_web_page_preview=False,
        )

    except CheveretoVideoDisabledError as err:
        logger.warning("Chevereto video rejected: %s", err)
        context.bot_data["host_video_enabled"] = False
        await status_msg.edit_text(
            "❌ <b>Video Uploads Not Enabled on Host</b>\n\n"
            "The Chevereto server rejected this video. Ensure video extensions "
            "(.mp4, .webm, .mov) are enabled in Chevereto Dashboard > Settings > File uploads.",
            parse_mode=ParseMode.HTML,
        )
    except CheveretoAuthError as err:
        logger.error("Chevereto auth error: %s", err)
        await status_msg.edit_text(
            f"❌ <b>Authentication Failed</b>\n\n{err}",
            parse_mode=ParseMode.HTML,
        )
    except CheveretoUploadError as err:
        logger.error("Chevereto upload error: %s", err)
        await status_msg.edit_text(
            f"❌ <b>Upload Failed</b>\n\n{err}",
            parse_mode=ParseMode.HTML,
        )
    except Exception as err:
        logger.exception("Unexpected error during media processing: %s", err)
        await status_msg.edit_text(
            f"❌ <b>Processing Error:</b> {err}",
            parse_mode=ParseMode.HTML,
        )
