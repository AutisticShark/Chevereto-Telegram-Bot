"""Tests for message and keyboard formatters."""

from __future__ import annotations

from chevereto_bot.client import CheveretoMedia
from chevereto_bot.utils.formatters import format_upload_response


def test_format_image_upload_response(v4_image_response: dict):
    media = CheveretoMedia.from_api_response(v4_image_response)
    text, keyboard = format_upload_response(media)

    assert "✅ <b>Upload Succeeded!</b>" in text
    assert "https://demo.chevereto.com/image/AbCd" in text
    assert (
        "<code>![My Awesome Screenshot](https://demo.chevereto.com/images/2026/09/03/sample-photo.png)</code>"
        in text
    )
    assert (
        "<code>[img]https://demo.chevereto.com/images/2026/09/03/sample-photo.png[/img]</code>"
        in text
    )
    assert '&lt;img src="https://demo.chevereto.com/images/2026/09/03/sample-photo.png"' in text
    assert "Size: 1.0 MB" in text
    assert "Res: 1920x1080" in text

    # Check keyboard buttons
    buttons = keyboard.inline_keyboard[0]
    button_urls = [btn.url for btn in buttons]
    assert "https://demo.chevereto.com/image/AbCd" in button_urls
    assert "https://demo.chevereto.com/images/2026/09/03/sample-photo.png" in button_urls
    assert "https://demo.chevereto.com/image/AbCd/delete/token123" in button_urls


def test_format_video_upload_response(v4_video_response: dict):
    media = CheveretoMedia.from_api_response(v4_video_response)
    text, keyboard = format_upload_response(media)

    assert "🎬 Video" in text
    assert (
        "<code>[Funny Cat Video](https://demo.chevereto.com/images/2026/09/03/sample-clip.mp4)</code>"
        in text
    )
    assert '&lt;video src="https://demo.chevereto.com/images/2026/09/03/sample-clip.mp4"' in text

    buttons = keyboard.inline_keyboard[0]
    button_urls = [btn.url for btn in buttons]
    assert "https://demo.chevereto.com/clip/Vid123" in button_urls


def test_title_html_escaping(v4_image_response: dict):
    v4_image_response["image"]["title"] = '<script>alert("hack")</script>'
    media = CheveretoMedia.from_api_response(v4_image_response)
    text, _ = format_upload_response(media)

    assert "<script>" not in text
    assert "&lt;script&gt;alert(&quot;hack&quot;)&lt;/script&gt;" in text
