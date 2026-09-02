"""Chevereto v4 API async client."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class CheveretoError(Exception):
    """Base exception for Chevereto API errors."""


class CheveretoAuthError(CheveretoError):
    """Raised when authentication fails."""


class CheveretoUploadError(CheveretoError):
    """Raised when file upload fails."""

    def __init__(self, message: str, status_code: int | None = None, api_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.api_code = api_code


class CheveretoVideoDisabledError(CheveretoUploadError):
    """Raised when the Chevereto host rejects video upload because video support is disabled."""


@dataclass
class CheveretoMedia:
    id_encoded: str
    url: str
    url_viewer: str
    url_short: str = ""
    delete_url: str | None = None
    display_url: str | None = None
    thumb_url: str | None = None
    medium_url: str | None = None
    title: str | None = None
    size: int = 0
    size_formatted: str = ""
    width: int | None = None
    height: int | None = None
    media_type: str = "image"
    mime: str = ""
    extension: str = ""
    raw_data: dict[str, Any] | None = None

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> CheveretoMedia:
        image_data: dict[str, Any] = data.get("image", {})

        thumb = image_data.get("thumb")
        thumb_url = thumb.get("url") if isinstance(thumb, dict) else None

        medium = image_data.get("medium")
        medium_url = medium.get("url") if isinstance(medium, dict) else None

        return cls(
            id_encoded=image_data.get("id_encoded", ""),
            url=image_data.get("url", ""),
            url_viewer=image_data.get("url_viewer", ""),
            url_short=image_data.get("url_short", "") or image_data.get("url_viewer", ""),
            delete_url=image_data.get("delete_url"),
            display_url=image_data.get("display_url") or image_data.get("url", ""),
            thumb_url=thumb_url,
            medium_url=medium_url,
            title=image_data.get("title") or image_data.get("name"),
            size=int(image_data.get("size", 0)),
            size_formatted=image_data.get("size_formatted", ""),
            width=image_data.get("width"),
            height=image_data.get("height"),
            media_type=image_data.get("type", "image"),
            mime=image_data.get("mime", ""),
            extension=image_data.get("extension", ""),
            raw_data=image_data,
        )


class CheveretoClient:
    """Asynchronous client for Chevereto API v1.1 (Chevereto v4.x)."""

    def __init__(
        self,
        endpoint_url: str,
        api_key: str,
        timeout: float = 60.0,
        user_agent: str = "Chevereto-Telegram-Bot/2.0",
        http_client: httpx.AsyncClient | None = None,
    ):
        self.endpoint_url = endpoint_url
        self.api_key = api_key
        self.timeout = timeout
        self.user_agent = user_agent
        self._custom_client = http_client
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> CheveretoClient:
        if self._custom_client is not None:
            self._client = self._custom_client
        else:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client is not None and self._custom_client is None:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        if self._custom_client is not None:
            return self._custom_client
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        if self._client is not None and self._custom_client is None:
            await self._client.aclose()
            self._client = None

    async def upload(
        self,
        file_content: bytes,
        filename: str,
        mime_type: str = "application/octet-stream",
        title: str | None = None,
        description: str | None = None,
        tags: str | None = None,
        album_id: str | None = None,
        category_id: int | None = None,
        expiration: str | None = None,
        nsfw: int | None = None,
        width: int | None = None,
        api_key: str | None = None,
    ) -> CheveretoMedia:
        """Upload media to Chevereto v4 instance."""
        client = self._get_client()

        effective_key = api_key or self.api_key
        headers = {
            "User-Agent": self.user_agent,
            "X-API-Key": effective_key,
        }

        # Parameters accepted by Chevereto v4 API v1.1
        data: dict[str, Any] = {
            "format": "json",
        }
        if title:
            data["title"] = title
        if description:
            data["description"] = description
        if tags:
            data["tags"] = tags
        if album_id:
            data["album_id"] = album_id
        if category_id is not None:
            data["category_id"] = str(category_id)
        if expiration:
            data["expiration"] = expiration
        if nsfw is not None:
            data["nsfw"] = str(nsfw)
        if width is not None:
            data["width"] = str(width)

        files = {
            "source": (filename, file_content, mime_type),
        }

        logger.info(
            "Uploading %s (%d bytes, %s) to %s (album=%s, category=%s)",
            filename,
            len(file_content),
            mime_type,
            self.endpoint_url,
            album_id,
            category_id,
        )

        try:
            response = await client.post(
                self.endpoint_url,
                headers=headers,
                data=data,
                files=files,
            )
        except httpx.RequestError as exc:
            logger.error("HTTP request error during upload: %s", exc)
            raise CheveretoUploadError(
                f"Network error communicating with Chevereto: {exc}"
            ) from exc

        # Parse JSON response
        try:
            res_json = response.json()
        except Exception as exc:
            logger.error(
                "Non-JSON response from Chevereto (HTTP %d): %s",
                response.status_code,
                response.text[:200],
            )
            msg = (
                f"Invalid response from server (HTTP {response.status_code}). "
                "Please verify your IMAGE_HOST URL."
            )
            raise CheveretoUploadError(
                msg,
                status_code=response.status_code,
            ) from exc

        status_code = res_json.get("status_code", response.status_code)

        if response.status_code == 200 and status_code == 200:
            return CheveretoMedia.from_api_response(res_json)

        # Handle API Error payload
        err_obj = res_json.get("error", {})
        err_msg = err_obj.get("message") if isinstance(err_obj, dict) else None
        err_code = err_obj.get("code") if isinstance(err_obj, dict) else None

        if not err_msg:
            err_msg = res_json.get("status_txt", f"HTTP {response.status_code}")

        logger.error(
            "Chevereto error (HTTP %d, status_code %s, error code %s): %s",
            response.status_code,
            status_code,
            err_code,
            err_msg,
        )

        if response.status_code in {401, 403} or (err_code in {100, 101, 102}):
            raise CheveretoAuthError(
                f"Chevereto authentication failed: {err_msg}. Please check your IMAGE_HOST_API_KEY."
            )

        # Detect video disabled on host
        is_video = mime_type.startswith("video/") or any(
            filename.lower().endswith(ext) for ext in [".mp4", ".webm", ".mov", ".mkv"]
        )
        if is_video and any(
            token in err_msg.lower()
            for token in ["extension not allowed", "format not allowed", "video", "ffmpeg"]
        ):
            raise CheveretoVideoDisabledError(
                f"Video upload rejected: {err_msg}. "
                "The image host may not have enabled video uploads or FFmpeg.",
                status_code=response.status_code,
                api_code=err_code,
            )

        raise CheveretoUploadError(
            f"Upload rejected by Chevereto: {err_msg}",
            status_code=response.status_code,
            api_code=err_code,
        )
