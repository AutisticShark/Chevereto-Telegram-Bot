"""Tests for Telegram handlers."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from chevereto_bot.config import BotConfig, Config, HostConfig
from chevereto_bot.handlers.admin import uptime_command
from chevereto_bot.handlers.common import (
    album_command,
    login_command,
    logout_command,
    start_command,
    whoami_command,
)
from chevereto_bot.handlers.upload import handle_builtin_video_notice


@pytest.fixture
def mock_context():
    context = MagicMock()
    context.bot_data = {
        "config": Config(
            bot=BotConfig(
                access_token="123:ABC",
                admin_user_ids={111},
                allowed_user_ids={111, 222},
            ),
            host=HostConfig(
                image_host="img.test.com",
                image_host_api_key="key123",
                album_id="defaultAlbum",
            ),
        )
    }
    context.user_data = {}
    context.args = []
    context.bot = MagicMock()
    context.bot.send_chat_action = AsyncMock()
    context.bot.send_message = AsyncMock()
    return context


@pytest.mark.asyncio
async def test_start_command_allowed_user(mock_context):
    update = MagicMock()
    update.effective_user.id = 222
    update.effective_message.reply_text = AsyncMock()

    await start_command(update, mock_context)

    assert update.effective_message.reply_text.called
    reply_args = update.effective_message.reply_text.call_args[0][0]
    assert "Welcome to Chevereto Bot!" in reply_args
    assert "Admin Commands" not in reply_args


@pytest.mark.asyncio
async def test_start_command_admin_user(mock_context):
    update = MagicMock()
    update.effective_user.id = 111
    update.effective_message.reply_text = AsyncMock()

    await start_command(update, mock_context)

    assert update.effective_message.reply_text.called
    reply_args = update.effective_message.reply_text.call_args[0][0]
    assert "Welcome to Chevereto Bot!" in reply_args
    assert "Admin Commands" in reply_args


@pytest.mark.asyncio
async def test_start_command_denied_user(mock_context):
    update = MagicMock()
    update.effective_user.id = 999
    update.effective_message.reply_text = AsyncMock()

    await start_command(update, mock_context)

    assert update.effective_message.reply_text.called
    reply_args = update.effective_message.reply_text.call_args[0][0]
    assert "Access Denied" in reply_args


@pytest.mark.asyncio
async def test_login_and_logout_flow(mock_context):
    update = MagicMock()
    update.effective_user.id = 222
    update.effective_message.delete = AsyncMock()
    update.effective_message.reply_text = AsyncMock()

    # 1. Login
    mock_context.args = ["chv_user_secret_key_12345"]
    await login_command(update, mock_context)

    assert mock_context.user_data["api_key"] == "chv_user_secret_key_12345"
    assert update.effective_message.delete.called
    assert mock_context.bot.send_message.called
    sent_text = mock_context.bot.send_message.call_args[1]["text"]
    assert "Logged In Successfully!" in sent_text

    # 2. Whoami
    await whoami_command(update, mock_context)
    whoami_reply = update.effective_message.reply_text.call_args[0][0]
    assert "Logged in with personal API key" in whoami_reply

    # 3. Logout
    await logout_command(update, mock_context)
    logout_reply = update.effective_message.reply_text.call_args[0][0]
    assert "Logged Out" in logout_reply
    assert "api_key" not in mock_context.user_data


@pytest.mark.asyncio
async def test_album_command_requires_login(mock_context):
    update = MagicMock()
    update.effective_user.id = 222  # non-admin, not logged in
    update.effective_message.reply_text = AsyncMock()

    mock_context.args = ["some_album"]
    await album_command(update, mock_context)

    reply = update.effective_message.reply_text.call_args[0][0]
    assert "Login Required" in reply
    assert "album_id" not in mock_context.user_data


@pytest.mark.asyncio
async def test_album_command_flow_logged_in(mock_context):
    update = MagicMock()
    update.effective_user.id = 222
    mock_context.user_data["api_key"] = "personal_key_xyz"
    update.effective_message.reply_text = AsyncMock()

    # 1. View album
    mock_context.args = []
    await album_command(update, mock_context)
    reply = update.effective_message.reply_text.call_args[0][0]
    assert "Current Target Album:" in reply

    # 2. Set new album
    mock_context.args = ["myTrip2026"]
    await album_command(update, mock_context)
    reply = update.effective_message.reply_text.call_args[0][0]
    assert "myTrip2026" in reply
    assert mock_context.user_data["album_id"] == "myTrip2026"

    # 3. Clear album
    mock_context.args = ["clear"]
    await album_command(update, mock_context)
    reply = update.effective_message.reply_text.call_args[0][0]
    assert "reset to default" in reply
    assert "album_id" not in mock_context.user_data


@pytest.mark.asyncio
async def test_builtin_video_notice(mock_context):
    update = MagicMock()
    update.effective_user.id = 222
    update.effective_message.reply_text = AsyncMock()

    await handle_builtin_video_notice(update, mock_context)

    assert update.effective_message.reply_text.called
    reply = update.effective_message.reply_text.call_args[0][0]
    assert "Video Upload via File Only" in reply
    assert "Attachment &gt; File" in reply


@pytest.mark.asyncio
async def test_admin_uptime_permission(mock_context):
    update = MagicMock()
    update.effective_message.reply_text = AsyncMock()

    # Non-admin user
    update.effective_user.id = 222
    await uptime_command(update, mock_context)
    reply = update.effective_message.reply_text.call_args[0][0]
    assert "Admin permission required" in reply

    # Admin user
    update.effective_user.id = 111
    await uptime_command(update, mock_context)
    reply = update.effective_message.reply_text.call_args[0][0]
    assert "System Uptime:" in reply
