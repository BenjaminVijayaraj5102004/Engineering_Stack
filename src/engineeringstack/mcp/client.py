import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from ..util.config import settings
import httpx
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client

load_dotenv()

CONFIG_PATH = Path(__file__).parent / "config" / "github.json"


def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found at {CONFIG_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    token = settings.GITHUB_ACCESS_TOKEN

    if not token:
        token = "dummy_token"  # Fallback for initialization without active network token

    github = config.get("servers", {}).get("github", {})
    url = github.get("url", "https://api.githubcopilot.com/mcp/")

    headers = dict(github.get("headers", {}))
    headers["Authorization"] = f"Bearer {token}"

    return url, headers


@asynccontextmanager
async def get_github_client():
    url, headers = load_config()

    if "/sse" in url:
        async with sse_client(url=url, headers=headers) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await asyncio.wait_for(session.initialize(), timeout=3.0)
                yield session
    else:
        timeout_config = httpx.Timeout(5.0, connect=3.0)
        async with httpx.AsyncClient(headers=headers, timeout=timeout_config) as http_client:
            async with streamable_http_client(url=url, http_client=http_client) as (
                read_stream,
                write_stream,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await asyncio.wait_for(session.initialize(), timeout=3.0)
                    yield session
