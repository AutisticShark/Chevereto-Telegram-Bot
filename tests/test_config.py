"""Tests for configuration loading and validation."""

from __future__ import annotations

import pytest

from chevereto_bot.config import Config, HostConfig, load_config


def test_default_config():
    config = Config()
    assert config.bot.mode == "POLLING"
    assert config.host.image_host_return_format == "json"
    assert ".png" in config.host.allowed_file_formats
    assert "video/mp4" in config.host.allowed_file_mimes
    assert config.host.enable_video is True


def test_upload_url_formatting():
    host = HostConfig(image_host="img.example.com")
    assert host.upload_url == "https://img.example.com/api/1/upload"

    host_http = HostConfig(image_host="http://192.168.1.50:8080")
    assert host_http.upload_url == "http://192.168.1.50:8080/api/1/upload"

    host_full = HostConfig(image_host="https://img.example.com/api/1/upload")
    assert host_full.upload_url == "https://img.example.com/api/1/upload"


def test_user_permissions(sample_config: Config):
    assert sample_config.is_user_admin(111222333) is True
    assert sample_config.is_user_admin(999999999) is False

    assert sample_config.is_user_allowed(111222333) is True
    assert sample_config.is_user_allowed(444555666) is True
    assert sample_config.is_user_allowed(999999999) is False

    # When allowed_user_ids is empty, any non-admin can upload
    sample_config.bot.allowed_user_ids.clear()
    assert sample_config.is_user_allowed(999999999) is True


def test_config_validation():
    config = Config()
    with pytest.raises(ValueError, match="ACCESS_TOKEN is required"):
        config.validate()

    config.bot.access_token = "valid_token"
    with pytest.raises(ValueError, match="IMAGE_HOST is required"):
        config.validate()

    config.host.image_host = "demo.com"
    with pytest.raises(ValueError, match="IMAGE_HOST_API_KEY is required"):
        config.validate()

    config.host.image_host_api_key = "test_key"
    # Should not raise now
    config.validate()


def test_load_from_ini(tmp_path):
    ini_file = tmp_path / "test_config.ini"
    ini_file.write_text(
        """[BOT]
MODE = PULLING
ACCESS_TOKEN = ini_bot_token
ADMIN_USER_ID = 555666
ALLOWED_USER_IDS = 111, 222, 333
[HOST]
IMAGE_HOST = test.chevereto.org
IMAGE_HOST_API_KEY = key_abc_123
ALLOWED_FILE_MINE = image/jpeg image/png
ALBUM_ID = album_custom
CATEGORY_ID = 5
EXPIRATION = PT10M
NSFW = 1
ENABLE_VIDEO = False
[DEBUG]
LOGGING_LEVEL = DEBUG
""",
        encoding="utf-8",
    )

    config = load_config(ini_file)
    # Checks legacy PULLING typo converted to POLLING
    assert config.bot.mode == "POLLING"
    assert config.bot.access_token == "ini_bot_token"
    assert 555666 in config.bot.admin_user_ids
    assert {111, 222, 333} == config.bot.allowed_user_ids
    assert config.host.image_host == "test.chevereto.org"
    assert config.host.image_host_api_key == "key_abc_123"
    # Checks legacy ALLOWED_FILE_MINE handled
    assert "image/png" in config.host.allowed_file_mimes
    assert config.host.album_id == "album_custom"
    assert config.host.category_id == 5
    assert config.host.expiration == "PT10M"
    assert config.host.nsfw == 1
    assert config.host.enable_video is False
    assert config.logging_level == "DEBUG"


def test_load_from_env(monkeypatch, tmp_path):
    empty_ini = tmp_path / "empty.ini"
    empty_ini.write_text("", encoding="utf-8")

    monkeypatch.setenv("BOT_MODE", "WEBHOOK")
    monkeypatch.setenv("BOT_ACCESS_TOKEN", "env_token")
    monkeypatch.setenv("BOT_ADMIN_USER_IDS", "101, 102")
    monkeypatch.setenv("BOT_WEBHOOK_URL", "https://webhook.test")
    monkeypatch.setenv("HOST_IMAGE_HOST", "env.chevereto.com")
    monkeypatch.setenv("HOST_IMAGE_HOST_API_KEY", "env_api_key")
    monkeypatch.setenv("HOST_ALBUM_ID", "env_album")

    config = load_config(empty_ini)
    assert config.bot.mode == "WEBHOOK"
    assert config.bot.access_token == "env_token"
    assert config.bot.admin_user_ids == {101, 102}
    assert config.bot.webhook_url == "https://webhook.test"
    assert config.host.image_host == "env.chevereto.com"
    assert config.host.image_host_api_key == "env_api_key"
    assert config.host.album_id == "env_album"
