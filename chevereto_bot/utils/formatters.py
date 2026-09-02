"""Message and keyboard formatters for Telegram responses."""

from __future__ import annotations

import html

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from chevereto_bot.client import CheveretoMedia


def format_upload_response(media: CheveretoMedia) -> tuple[str, InlineKeyboardMarkup]:
    """Format uploaded media details into an HTML Telegram message with inline buttons."""
    title_escaped = html.escape(media.title or "Image")
    is_video = media.media_type.lower() == "video"

    media_badge = "🎬 Video" if is_video else "🖼️ Image"

    text_parts = [
        f"✅ <b>Upload Succeeded!</b> ({media_badge})\n",
        f'🔗 <b>Viewer:</b> <a href="{media.url_viewer}">{media.url_viewer}</a>',
        f'🌐 <b>Direct:</b> <a href="{media.url}">{media.url}</a>\n',
    ]

    if is_video:
        text_parts.extend(
            [
                "📋 <b>Markdown:</b>",
                f"<code>[{title_escaped}]({media.url})</code>\n",
                "📋 <b>HTML:</b>",
                f'<code>&lt;video src="{media.url}" controls&gt;&lt;/video&gt;</code>\n',
            ]
        )
    else:
        text_parts.extend(
            [
                "📋 <b>Markdown:</b>",
                f"<code>![{title_escaped}]({media.url})</code>\n",
                "📋 <b>BBCode:</b>",
                f"<code>[img]{media.url}[/img]</code>\n",
                "📋 <b>HTML:</b>",
                f'<code>&lt;img src="{media.url}" alt="{title_escaped}" /&gt;</code>\n',
            ]
        )

    meta_parts: list[str] = []
    if media.size_formatted:
        meta_parts.append(f"Size: {media.size_formatted}")
    if media.width and media.height:
        meta_parts.append(f"Res: {media.width}x{media.height}")
    if media.extension:
        meta_parts.append(f"Ext: .{media.extension.lstrip('.')}")

    if meta_parts:
        text_parts.append(f"ℹ️ <i>{' | '.join(meta_parts)}</i>")

    # Build keyboard buttons
    row: list[InlineKeyboardButton] = []
    if media.url_viewer:
        row.append(InlineKeyboardButton("🌐 Viewer", url=media.url_viewer))
    if media.url:
        row.append(InlineKeyboardButton("🔗 Direct", url=media.url))
    if media.delete_url:
        row.append(InlineKeyboardButton("🗑️ Delete", url=media.delete_url))

    keyboard = InlineKeyboardMarkup([row]) if row else InlineKeyboardMarkup([])

    return "\n".join(text_parts), keyboard
