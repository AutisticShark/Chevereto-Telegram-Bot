# AGENTS.md - Developer & Agent Guide

This document serves as the persistent reference and institutional knowledge for AI agents and developers working on the **Chevereto Telegram Bot** codebase.

---

## 📌 Project Overview

- **Purpose**: An asynchronous, production-ready Telegram bot for **Chevereto v4.x** image and video hosting.
- **Python Version**: Python 3.10+ (baseline Python 3.14).
- **Core Dependencies**:
  - `python-telegram-bot[webhooks]>=21.0,<23.0`: Async Telegram bot framework.
  - `httpx>=0.27.0`: Non-blocking async HTTP client for Chevereto API calls.
  - `filetype>=1.2.0`: Pure-Python media sniffing (zero C/DLL dependencies).
  - `psutil>=6.0.0`: Cross-platform system and storage monitoring.
  - `python-dotenv>=1.0.0`: Environment variable support.
- **Development & Testing**:
  - `pytest`, `pytest-asyncio`, `respx` (for HTTP mocking), `ruff` (linter and formatter).

---

## 📁 Repository Architecture & Key Files

```
Chevereto-Telegram-Bot/
├── bot.py                                # Application bootstrap & CLI entrypoint
├── chevereto_bot/                        # Core package
│   ├── __init__.py                       # Package version metadata (__version__ = "2.0.0")
│   ├── __main__.py                       # Allows running via `python -m chevereto_bot`
│   ├── client.py                         # Async Chevereto v4 API client (httpx)
│   ├── config.py                         # Typed dataclass config (INI, ENV, .env)
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── admin.py                      # Admin commands (/uptime, /storage_status, /system_status)
│   │   ├── common.py                     # /start, /help, /login, /logout, /whoami, /album
│   │   └── upload.py                     # Media upload handlers with video support detection
│   └── utils/
│       ├── __init__.py
│       ├── formatters.py                 # HTML embed codes (Markdown, BBCode, HTML) & inline buttons
│       ├── media.py                      # Pure-Python MIME & extension detection
│       └── system.py                     # psutil-based cross-platform system telemetry
├── tests/                                # Automated test suite (31 tests)
│   ├── conftest.py                       # Fixtures for Chevereto v4 API image/video payloads
│   ├── test_client.py                    # Mocked Chevereto API tests (respx)
│   ├── test_config.py                    # Configuration loading and validation tests
│   ├── test_formatters.py                # Response embed code formatting tests
│   ├── test_handlers.py                  # Handler logic, session login, and permission tests
│   ├── test_media.py                     # Pure-Python MIME sniffing tests
│   └── test_system.py                    # psutil telemetry tests
├── .github/workflows/
│   └── docker-publish.yml                # Multi-arch CI/CD pipeline (GHCR + optional Docker Hub)
├── Dockerfile                            # Production-ready Python 3.14-slim image (non-root)
├── docker-compose.yml                    # 1-command container orchestration
├── chevereto-bot.service                 # Linux systemd service unit
├── config.ini.new                        # Configuration template (INI)
├── .env.example                          # Environment variable template
├── pyproject.toml                        # PEP 518/621 packaging & ruff/pytest config
├── requirements.txt                      # Runtime dependencies
└── requirements-dev.txt                  # Testing & linting dependencies
```

---

## 💡 Chevereto v4.x API Insights & Rules

1. **Upload Endpoint**:
   - `POST https://{IMAGE_HOST}/api/1/upload`
   - Authorization: `X-API-Key: <key>` header (or `key` parameter).
   - The bot supports both personal user API keys and system/public API keys.

2. **Album Ownership**:
   - In Chevereto v4, the `album_id` parameter **must be owned by the user of the API key**.
   - For guest/public keys, album assignment will fail. Therefore, dynamic album switching via `/album <id>` is strictly scoped to **logged-in users** who have linked their personal API key via `/login <api_key>`.

3. **Response Schema**:
   - Even when uploading videos, Chevereto v4 returns metadata inside the `"image"` JSON dictionary for backward compatibility (e.g. `response["image"]["type"] == "video"`).
   - Key attributes: `url`, `url_viewer`, `url_short`, `delete_url`, `thumb.url`, `medium.url`, `display_url`, `size_formatted`, `width`, `height`.

4. **Error Handling**:
   - Error responses have structure: `{"status_code": 400, "error": {"message": "...", "code": ...}}`.
   - `chevereto_bot/client.py` captures these into structured exceptions: `CheveretoAuthError`, `CheveretoUploadError`, and `CheveretoVideoDisabledError`.

---

## 🎬 Video Upload Policy

1. **Uncompressed File / Document Only**:
   - Telegram built-in video (`message.video`) and GIF animations (`message.animation`) are re-encoded and heavily compressed by Telegram.
   - Per project requirement, videos must **only** be uploaded as uncompressed **Files / Documents** (`message.document`).
   - When a user sends a built-in Telegram video, `handle_builtin_video_notice` politely informs them to send the video as a File attachment. It **does not** download or re-upload the video.

2. **Host Video Capability Detection**:
   - Chevereto v1 API does not expose a `/settings` endpoint to query server capabilities.
   - Video upload support was introduced in Chevereto v4.1 and requires FFmpeg and video extensions enabled on the host.
   - If Chevereto rejects a video file with an extension/format error, the bot detects this, raises `CheveretoVideoDisabledError`, sets `context.bot_data["host_video_enabled"] = False`, and provides actionable troubleshooting steps.
   - Upon a successful video upload, `context.bot_data["host_video_enabled"] = True` is cached.

---

## 🔐 Security & User Session Handling

1. **Open by Default**:
   - The bot allows any user to upload by default unless `ALLOWED_USER_IDS` is specified in `config.ini` or `.env`.
   - Admin commands (`/uptime`, `/storage_status`, `/system_status`, `/cache_clean`) are strictly restricted to `ADMIN_USER_IDS`.

2. **Personal Login (`/login <api_key>`)**:
   - Users can link their personal Chevereto account.
   - The bot immediately attempts to delete the `/login <key>` message to ensure secret API keys do not remain in Telegram chat history.
   - The key is saved in `context.user_data["api_key"]`.
   - `/logout` clears the session key and active custom album.
   - `/whoami` displays whether the user is running under a personal session (with masked key) or default bot guest credentials.

---

## 🛠️ Cross-Platform & Streaming Architecture

1. **Zero Disk Leak**:
   - Telegram media is downloaded directly into memory via `tg_file.download_to_memory(buffer)` (`io.BytesIO`).
   - No temporary files are saved to `./cache/` during normal operation, preventing server disk exhaustion.
   - Legacy `/cache_clean` and `/cache_status` remain for backward compatibility with old disk caches.

2. **Pure-Python Sniffing**:
   - `filetype` and `mimetypes` are used instead of `python-magic`.
   - This eliminates crashes on Windows (missing `libmagic.dll`) and minimal Alpine/Debian Docker containers.

3. **System Telemetry**:
   - `psutil` replaces Linux-only shell commands (`os.popen("uptime")` and `os.popen("df -lh")`), working identically on Windows, Linux, and macOS.

---

## 🚀 CI/CD & Publishing Rules

- **Workflow**: `.github/workflows/docker-publish.yml`
- **Registries**:
  - **GHCR** (`ghcr.io`): Always published using `${{ secrets.GITHUB_TOKEN }}`.
  - **Docker Hub**: **Optional**. Evaluated dynamically. If `DOCKERHUB_USERNAME` or `DOCKERHUB_TOKEN` secrets are missing, Docker Hub steps are skipped without failing the CI run.
- **Branch Triggers**:
  - Pushes to `main`: publishes `:dev` and `:sha-<commit>`.
  - Pushes to `v*` tags: publishes `:latest`, `:vX.Y.Z`, `:X.Y`, `:X`.
- **Pre-Push Quality Gate**:
  - The workflow runs `ruff check`, `ruff format --check`, and `pytest -v` before building container images.

---

## 🧪 Testing & Verification Commands

```bash
# Run pytest test suite
pytest -v

# Run linter
ruff check .

# Run code formatter
ruff format .

# Check formatting without modifying
ruff format --check .
```
