"""Pytest fixtures and sample data."""

from __future__ import annotations

import pytest

from chevereto_bot.config import BotConfig, Config, HostConfig


@pytest.fixture
def sample_config() -> Config:
    return Config(
        bot=BotConfig(
            mode="POLLING",
            access_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            admin_user_ids={111222333},
            allowed_user_ids={111222333, 444555666},
        ),
        host=HostConfig(
            image_host="demo.chevereto.com",
            image_host_api_key="chv_test_key_12345",
            album_id="albumXYZ",
            category_id=2,
            enable_video=True,
        ),
    )


@pytest.fixture
def v4_image_response() -> dict:
    return {
        "status_code": 200,
        "success": {
            "message": "file uploaded",
            "code": 200,
        },
        "image": {
            "name": "sample-photo",
            "extension": "png",
            "size": 1048576,
            "size_formatted": "1.0 MB",
            "width": 1920,
            "height": 1080,
            "date": "2026-09-03 00:00:00",
            "title": "My Awesome Screenshot",
            "type": "image",
            "id_encoded": "AbCd",
            "filename": "sample-photo.png",
            "mime": "image/png",
            "url": "https://demo.chevereto.com/images/2026/09/03/sample-photo.png",
            "url_viewer": "https://demo.chevereto.com/image/AbCd",
            "url_short": "https://demo.chevereto.com/image/AbCd",
            "display_url": "https://demo.chevereto.com/images/2026/09/03/sample-photo.png",
            "delete_url": "https://demo.chevereto.com/image/AbCd/delete/token123",
            "thumb": {
                "filename": "sample-photo.th.png",
                "url": "https://demo.chevereto.com/images/2026/09/03/sample-photo.th.png",
            },
            "medium": {
                "filename": "sample-photo.md.png",
                "url": "https://demo.chevereto.com/images/2026/09/03/sample-photo.md.png",
            },
        },
        "status_txt": "OK",
    }


@pytest.fixture
def v4_video_response() -> dict:
    return {
        "status_code": 200,
        "success": {
            "message": "file uploaded",
            "code": 200,
        },
        "image": {
            "name": "sample-clip",
            "extension": "mp4",
            "size": 5242880,
            "size_formatted": "5.0 MB",
            "width": 1280,
            "height": 720,
            "title": "Funny Cat Video",
            "type": "video",
            "id_encoded": "Vid123",
            "filename": "sample-clip.mp4",
            "mime": "video/mp4",
            "url": "https://demo.chevereto.com/images/2026/09/03/sample-clip.mp4",
            "url_viewer": "https://demo.chevereto.com/clip/Vid123",
            "url_short": "https://demo.chevereto.com/clip/Vid123",
            "delete_url": "https://demo.chevereto.com/clip/Vid123/delete/tok999",
            "thumb": {
                "url": "https://demo.chevereto.com/images/2026/09/03/sample-clip.th.jpg",
            },
        },
        "status_txt": "OK",
    }
