"""MCP client wrappers: local stdio (@paypal/mcp via npx) and remote HTTP.

Two transports, per the official quickstart [V-1105]:
  * stdio:  command spawns `npx -y @paypal/mcp --tools=all` with
            PAYPAL_ACCESS_TOKEN + PAYPAL_ENVIRONMENT=SANDBOX
  * remote: streamable HTTP against https://mcp.sandbox.paypal.com/http;
            client_credentials bearer-header auth is documented for
            mcp-remote (--header "Authorization: Bearer <token>") but is
            UNVERIFIED for direct SDK connections until the spike proves it.
            Fallback documented in docs/plan.md is the stdio transport.

NOTE(spike-verify): import names follow the official `mcp` Python SDK;
confirmed live in spike 4 before later phases depend on them.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from asa.config import Config


async def _list_tools_stdio(cfg: Config) -> list[dict[str, Any]]:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    env = {
        "PAYPAL_ACCESS_TOKEN": os.getenv("PAYPAL_ACCESS_TOKEN", ""),
        "PAYPAL_ENVIRONMENT": "SANDBOX",
    }
    params = StdioServerParameters(
        command=cfg.mcp_stdio_command,
        args=["-y", "@paypal/mcp", "--tools=all"],
        env=env,
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            resp = await session.list_tools()
            return [{"name": t.name, "input_schema": t.inputSchema} for t in resp.tools]


async def _list_tools_http(cfg: Config) -> list[dict[str, Any]]:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    token = os.getenv("PAYPAL_ACCESS_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}"} if token else None
    async with streamablehttp_client(cfg.mcp_remote_url, headers=headers) as (read, write, _get_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            resp = await session.list_tools()
            return [{"name": t.name, "input_schema": t.inputSchema} for t in resp.tools]


def snapshot_tools(cfg: Config, transport: str = "stdio") -> list[dict[str, Any]]:
    """Return [{name, input_schema}, ...] for the chosen transport."""
    if transport == "stdio":
        return asyncio.run(_list_tools_stdio(cfg))
    elif transport == "http":
        return asyncio.run(_list_tools_http(cfg))
    raise ValueError(f"unknown transport: {transport!r} (stdio | http)")


class McpStdioSession:
    """One long-lived stdio session over @paypal/mcp, reused across probes.

    The harness mints a sandbox access token (PAYPAL_ACCESS_TOKEN) before
    open(); the stdio env is read at spawn time.
    """

    def __init__(self, cfg: Config) -> None:
        self._cfg = cfg
        self._context = None
        self._session = None
        self.tool_names: list[str] = []

    async def open(self) -> "McpStdioSession":
        import os

        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        env = {
            "PAYPAL_ACCESS_TOKEN": os.getenv("PAYPAL_ACCESS_TOKEN", ""),
            "PAYPAL_ENVIRONMENT": "SANDBOX",
        }
        params = StdioServerParameters(
            command=self._cfg.mcp_stdio_command,
            args=["-y", "@paypal/mcp", "--tools=all"],
            env=env,
        )
        self._context = stdio_client(params)
        read, write = await self._context.__aenter__()
        self._session = ClientSession(read, write)
        await self._session.__aenter__()
        await self._session.initialize()
        listed = await self._session.list_tools()
        self.tool_names = [t.name for t in listed.tools]
        return self

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Returns {"ok": bool, "texts": [...]} for the tool result."""
        result = await self._session.call_tool(name, arguments)
        texts = [c.text for c in result.content if getattr(c, "text", None) is not None]
        return {"ok": not result.isError, "texts": texts, "isError": bool(result.isError)}

    async def close(self) -> None:
        if self._session is not None:
            await self._session.__aexit__(None, None, None)
            self._session = None
        if self._context is not None:
            await self._context.__aexit__(None, None, None)
            self._context = None
