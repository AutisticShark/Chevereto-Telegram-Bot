"""Tests for CheveretoClient using respx."""

from __future__ import annotations

import httpx
import pytest
import respx

from chevereto_bot.client import CheveretoAuthError, CheveretoClient, CheveretoUploadError


@pytest.mark.asyncio
@respx.mock
async def test_successful_image_upload(v4_image_response: dict):
    endpoint = "https://demo.chevereto.com/api/1/upload"
    route = respx.post(endpoint).mock(return_value=httpx.Response(200, json=v4_image_response))

    async with CheveretoClient(endpoint_url=endpoint, api_key="test_key") as client:
        media = await client.upload(
            file_content=b"fake_image_bytes",
            filename="test.png",
            mime_type="image/png",
            title="My Awesome Screenshot",
            album_id="albumXYZ",
            category_id=2,
            expiration="P1D",
            nsfw=0,
        )

    assert route.called
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == "test_key"
    assert "Chevereto-Telegram-Bot" in request.headers["User-Agent"]

    assert media.id_encoded == "AbCd"
    assert media.url == "https://demo.chevereto.com/images/2026/09/03/sample-photo.png"
    assert media.url_viewer == "https://demo.chevereto.com/image/AbCd"
    assert media.delete_url == "https://demo.chevereto.com/image/AbCd/delete/token123"
    assert media.thumb_url == "https://demo.chevereto.com/images/2026/09/03/sample-photo.th.png"
    assert media.size_formatted == "1.0 MB"
    assert media.media_type == "image"


@pytest.mark.asyncio
@respx.mock
async def test_successful_video_upload(v4_video_response: dict):
    endpoint = "https://demo.chevereto.com/api/1/upload"
    respx.post(endpoint).mock(return_value=httpx.Response(200, json=v4_video_response))

    async with CheveretoClient(endpoint_url=endpoint, api_key="test_key") as client:
        media = await client.upload(
            file_content=b"fake_video_bytes",
            filename="clip.mp4",
            mime_type="video/mp4",
            title="Funny Cat Video",
        )

    assert media.id_encoded == "Vid123"
    assert media.media_type == "video"
    assert media.url == "https://demo.chevereto.com/images/2026/09/03/sample-clip.mp4"
    assert media.url_viewer == "https://demo.chevereto.com/clip/Vid123"
    assert media.delete_url == "https://demo.chevereto.com/clip/Vid123/delete/tok999"


@pytest.mark.asyncio
@respx.mock
async def test_auth_error_handling():
    endpoint = "https://demo.chevereto.com/api/1/upload"
    error_payload = {
        "status_code": 403,
        "error": {
            "message": "Invalid API key",
            "code": 100,
        },
        "status_txt": "Forbidden",
    }
    respx.post(endpoint).mock(return_value=httpx.Response(403, json=error_payload))

    async with CheveretoClient(endpoint_url=endpoint, api_key="invalid_key") as client:
        with pytest.raises(CheveretoAuthError, match="Invalid API key"):
            await client.upload(
                file_content=b"test",
                filename="test.jpg",
                mime_type="image/jpeg",
            )


@pytest.mark.asyncio
@respx.mock
async def test_upload_rejection_error_handling():
    endpoint = "https://demo.chevereto.com/api/1/upload"
    error_payload = {
        "status_code": 400,
        "error": {
            "message": "File too big - max 5 MB",
            "code": 313,
        },
        "status_txt": "Bad Request",
    }
    respx.post(endpoint).mock(return_value=httpx.Response(400, json=error_payload))

    async with CheveretoClient(endpoint_url=endpoint, api_key="valid_key") as client:
        with pytest.raises(CheveretoUploadError, match="File too big"):
            await client.upload(
                file_content=b"huge_file",
                filename="huge.jpg",
                mime_type="image/jpeg",
            )


@pytest.mark.asyncio
@respx.mock
async def test_non_json_response_handling():
    endpoint = "https://demo.chevereto.com/api/1/upload"
    respx.post(endpoint).mock(return_value=httpx.Response(502, text="<html>502 Bad Gateway</html>"))

    async with CheveretoClient(endpoint_url=endpoint, api_key="valid_key") as client:
        with pytest.raises(CheveretoUploadError, match="Invalid response from server"):
            await client.upload(
                file_content=b"test",
                filename="test.jpg",
                mime_type="image/jpeg",
            )
