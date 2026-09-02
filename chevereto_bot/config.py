"""Configuration management for Chevereto Telegram Bot."""

from __future__ import annotations

import configparser
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class BotConfig:
    mode: str = "POLLING"
    access_token: str = ""
    admin_user_ids: set[int] = field(default_factory=set)
    allowed_user_ids: set[int] = field(default_factory=set)
    webhook_listen: str = "0.0.0.0"
    webhook_port: int = 8443
    webhook_url: str = ""
    webhook_ssl: bool = False
    webhook_key: str = ""
    webhook_cert: str = ""
    webhook_secret_token: str = ""


@dataclass
class HostConfig:
    image_host: str = ""
    image_host_api_key: str = ""
    image_host_return_format: str = "json"
    max_file_size_mb: int = 20
    allowed_file_formats: set[str] = field(
        default_factory=lambda: {
            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".gif",
            ".webp",
            ".avif",
            ".mp4",
            ".webm",
            ".mov",
        }
    )
    allowed_file_mimes: set[str] = field(
        default_factory=lambda: {
            "image/jpeg",
            "image/png",
            "image/bmp",
            "image/gif",
            "image/webp",
            "image/avif",
            "video/mp4",
            "video/webm",
            "video/quicktime",
        }
    )
    album_id: str | None = None
    category_id: int | None = None
    expiration: str | None = None
    nsfw: int = 0
    enable_video: bool = True

    @property
    def upload_url(self) -> str:
        host = self.image_host.strip()
        if not host:
            return ""
        if not host.startswith("http://") and not host.startswith("https://"):
            host = f"https://{host}"
        host = host.rstrip("/")
        if not host.endswith("/api/1/upload"):
            return f"{host}/api/1/upload"
        return host


@dataclass
class Config:
    bot: BotConfig = field(default_factory=BotConfig)
    host: HostConfig = field(default_factory=HostConfig)
    logging_level: str = "INFO"

    def is_user_admin(self, user_id: int) -> bool:
        """Check if a given Telegram user ID is an admin."""
        return user_id in self.bot.admin_user_ids

    def is_user_allowed(self, user_id: int) -> bool:
        """Check if a user is allowed to upload.
        If allowed_user_ids is empty, all users are allowed.
        Admins are always allowed.
        """
        if self.is_user_admin(user_id):
            return True
        if not self.bot.allowed_user_ids:
            return True
        return user_id in self.bot.allowed_user_ids

    def validate(self) -> None:
        """Validate required configuration values."""
        errors: list[str] = []
        if not self.bot.access_token:
            errors.append("Telegram Bot ACCESS_TOKEN is required.")
        if not self.host.image_host:
            errors.append("IMAGE_HOST is required.")
        if not self.host.image_host_api_key:
            errors.append("IMAGE_HOST_API_KEY is required.")
        if self.bot.mode == "WEBHOOK" and not self.bot.webhook_url:
            errors.append("WEBHOOK_URL is required when running in WEBHOOK mode.")

        if errors:
            raise ValueError("Configuration validation failed:\n- " + "\n- ".join(errors))


def _parse_ids(val: str | None) -> set[int]:
    """Parse comma/space-separated string of IDs into a set of ints."""
    if not val:
        return set()
    result: set[int] = set()
    for item in val.replace(",", " ").split():
        clean = item.strip()
        if clean.isdigit() or (clean.startswith("-") and clean[1:].isdigit()):
            result.add(int(clean))
    return result


def _parse_set(val: str | None, lower: bool = True) -> set[str]:
    """Parse comma/space-separated string of tokens into a set."""
    if not val:
        return set()
    tokens = val.replace(",", " ").split()
    if lower:
        return {t.strip().lower() for t in tokens if t.strip()}
    return {t.strip() for t in tokens if t.strip()}


def _to_bool(val: str | bool | None, default: bool = False) -> bool:
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in {"1", "true", "yes", "on"}


def load_config(config_path: str | Path = "config.ini") -> Config:
    """Load configuration from environment variables, .env, and/or config.ini."""
    load_dotenv()

    ini_parser = configparser.ConfigParser()
    path_obj = Path(config_path)
    if path_obj.is_file():
        ini_parser.read(path_obj, encoding="utf-8")

    def get_val(section: str, key: str, env_key: str | None = None, default: str = "") -> str:
        # 1. Environment variable
        if env_key and os.getenv(env_key):
            return os.getenv(env_key, "").strip()
        # Fallback to direct section_key env var, e.g. BOT_ACCESS_TOKEN
        generic_env = f"{section}_{key}".upper()
        if os.getenv(generic_env):
            return os.getenv(generic_env, "").strip()
        # 2. INI file
        if ini_parser.has_section(section) and ini_parser.has_option(section, key):
            return ini_parser.get(section, key).strip()
        return default

    # --- BOT CONFIG ---
    raw_mode = get_val("BOT", "MODE", "BOT_MODE", default="POLLING").upper()
    if raw_mode == "PULLING":  # Backward compatibility with legacy typo
        raw_mode = "POLLING"

    access_token = get_val("BOT", "ACCESS_TOKEN", "TELEGRAM_TOKEN")
    if not access_token:
        access_token = get_val("BOT", "ACCESS_TOKEN", "BOT_ACCESS_TOKEN")

    # Admins can be specified as ADMIN_USER_ID, ADMIN_USER_IDS, or ADMIN_USER
    admin_raw = (
        get_val("BOT", "ADMIN_USER_IDS", "ADMIN_USER_IDS")
        or get_val("BOT", "ADMIN_USER_ID", "ADMIN_USER_ID")
        or get_val("BOT", "ADMIN_USER", "ADMIN_USER")
    )
    admin_ids = _parse_ids(admin_raw)

    allowed_raw = get_val("BOT", "ALLOWED_USER_IDS", "ALLOWED_USER_IDS")
    allowed_ids = _parse_ids(allowed_raw)

    webhook_listen = get_val("BOT", "WEBHOOK_LISTEN", "WEBHOOK_LISTEN", default="0.0.0.0")
    webhook_url = get_val("BOT", "WEBHOOK_URL", "WEBHOOK_URL")

    port_raw = get_val("BOT", "WEBHOOK_PORT", "WEBHOOK_PORT", default="8443")
    webhook_port = int(port_raw) if port_raw.isdigit() else 8443

    webhook_ssl = _to_bool(get_val("BOT", "WEBHOOK_SSL", "WEBHOOK_SSL", default="false"))
    webhook_key = get_val("BOT", "WEBHOOK_KEY", "WEBHOOK_KEY") or get_val(
        "BOT", "WEBHOOK_SSL_KEY", "WEBHOOK_SSL_KEY"
    )
    webhook_cert = get_val("BOT", "WEBHOOK_CERT", "WEBHOOK_CERT") or get_val(
        "BOT", "WEBHOOK_SSL_CERT", "WEBHOOK_SSL_CERT"
    )
    webhook_secret_token = get_val("BOT", "WEBHOOK_SECRET_TOKEN", "WEBHOOK_SECRET_TOKEN")

    bot_config = BotConfig(
        mode=raw_mode,
        access_token=access_token,
        admin_user_ids=admin_ids,
        allowed_user_ids=allowed_ids,
        webhook_listen=webhook_listen,
        webhook_port=webhook_port,
        webhook_url=webhook_url,
        webhook_ssl=webhook_ssl,
        webhook_key=webhook_key,
        webhook_cert=webhook_cert,
        webhook_secret_token=webhook_secret_token,
    )

    # --- HOST CONFIG ---
    image_host = get_val("HOST", "IMAGE_HOST", "IMAGE_HOST")
    image_host_api_key = get_val("HOST", "IMAGE_HOST_API_KEY", "IMAGE_HOST_API_KEY")
    return_format = get_val(
        "HOST", "IMAGE_HOST_RETURN_FORMAT", "IMAGE_HOST_RETURN_FORMAT", default="json"
    )

    max_size_raw = get_val("HOST", "MAX_FILE_SIZE", "MAX_FILE_SIZE", default="20")
    max_file_size_mb = int(max_size_raw) if max_size_raw.isdigit() else 20

    allowed_formats_raw = get_val("HOST", "ALLOWED_FILE_FORMAT", "ALLOWED_FILE_FORMAT")
    allowed_formats = (
        _parse_set(allowed_formats_raw)
        if allowed_formats_raw
        else HostConfig().allowed_file_formats
    )

    # Support typo ALLOWED_FILE_MINE as fallback
    allowed_mimes_raw = get_val("HOST", "ALLOWED_FILE_MIME", "ALLOWED_FILE_MIME") or get_val(
        "HOST", "ALLOWED_FILE_MINE", "ALLOWED_FILE_MINE"
    )
    allowed_mimes = (
        _parse_set(allowed_mimes_raw) if allowed_mimes_raw else HostConfig().allowed_file_mimes
    )

    album_id = get_val("HOST", "ALBUM_ID", "ALBUM_ID") or None
    cat_raw = get_val("HOST", "CATEGORY_ID", "CATEGORY_ID")
    category_id = int(cat_raw) if cat_raw and cat_raw.isdigit() else None
    expiration = get_val("HOST", "EXPIRATION", "EXPIRATION") or None
    nsfw_raw = get_val("HOST", "NSFW", "NSFW", default="0")
    nsfw = int(nsfw_raw) if nsfw_raw.isdigit() else 0
    enable_video = _to_bool(get_val("HOST", "ENABLE_VIDEO", "ENABLE_VIDEO", default="true"))

    host_config = HostConfig(
        image_host=image_host,
        image_host_api_key=image_host_api_key,
        image_host_return_format=return_format,
        max_file_size_mb=max_file_size_mb,
        allowed_file_formats=allowed_formats,
        allowed_file_mimes=allowed_mimes,
        album_id=album_id,
        category_id=category_id,
        expiration=expiration,
        nsfw=nsfw,
        enable_video=enable_video,
    )

    # --- DEBUG CONFIG ---
    logging_level = get_val("DEBUG", "LOGGING_LEVEL", "LOGGING_LEVEL", default="INFO").upper()

    return Config(
        bot=bot_config,
        host=host_config,
        logging_level=logging_level,
    )
