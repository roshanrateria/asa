"""Central config for asa, with a hard production guard.

The whole project is audited on the PayPal sandbox (hackathon rule: free
sandbox environment) and nowhere else. Any resolved non-sandbox environment
is refused at import-of-config time, not per call.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

API_HOSTS = {
    "SANDBOX": "https://api-m.sandbox.paypal.com",
    "PRODUCTION": "https://api-m.paypal.com",  # present only so the guard below reads clearly
}

MCP_REMOTE_DEFAULT = "https://mcp.sandbox.paypal.com/http"


class ProductionRefused(RuntimeError):
    """Raised when configuration would point asa at a non-sandbox edge."""


@dataclass(frozen=True)
class Config:
    client_id: str
    client_secret: str
    environment: str
    api_base: str
    mcp_remote_url: str
    mcp_stdio_command: str
    runs_dir: str
    card_pan: str | None
    card_expiry: str | None
    card_cvv: str | None
    personal_email: str | None


def load_config() -> Config:
    environment = os.getenv("PAYPAL_ENVIRONMENT", "SANDBOX").upper().strip()
    if environment != "SANDBOX":
        raise ProductionRefused(
            "PAYPAL_ENVIRONMENT must be SANDBOX for every asa run; refusing "
            f"resolved environment: {environment!r}"
        )

    client_id = (os.getenv("PAYPAL_CLIENT_ID") or "").strip()
    client_secret = (os.getenv("PAYPAL_CLIENT_SECRET") or "").strip()
    if not (client_id and client_secret):
        raise SystemExit(
            "PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET missing. "
            "Copy .env.example to .env and fill in your sandbox app credentials."
        )

    return Config(
        client_id=client_id,
        client_secret=client_secret,
        environment=environment,
        api_base=API_HOSTS["SANDBOX"],
        mcp_remote_url=(os.getenv("ASA_MCP_REMOTE_URL") or MCP_REMOTE_DEFAULT).strip(),
        # Windows quirk: bare "npx" often needs to be "npx.cmd" when spawned.
        mcp_stdio_command=(os.getenv("ASA_MCP_STDIO_COMMAND") or "npx").strip(),
        runs_dir=(os.getenv("ASA_RUNS_DIR") or "runs").strip(),
        card_pan=os.getenv("ASA_CARD_PAN") or None,
        card_expiry=os.getenv("ASA_CARD_EXPIRY") or None,
        card_cvv=os.getenv("ASA_CARD_CVV") or None,
        personal_email=os.getenv("ASA_SANDBOX_PERSONAL_EMAIL") or None,
    )
