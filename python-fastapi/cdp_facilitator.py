"""Coinbase's x402 facilitator (Base mainnet) for the Python x402 client.

The Node package @coinbase/x402 does this for you; in Python it's a few lines:
each facilitator request carries a short-lived JWT signed with your CDP API key.
Create a key at https://portal.cdp.coinbase.com.
"""

import base64
import secrets
import time

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from x402.http import FacilitatorConfig
from x402.http.facilitator_client_base import CreateHeadersAuthProvider

HOST = "api.cdp.coinbase.com"
ROUTE = "/platform/v2/x402"


def _private_key(secret: str):
    secret = secret.replace("\\n", "\n")
    if "BEGIN" in secret:  # EC key in PEM format
        key = serialization.load_pem_private_key(secret.encode(), password=None)
        if isinstance(key, ec.EllipticCurvePrivateKey):
            return key, "ES256"
    raw = base64.b64decode(secret)  # Ed25519 key: 32-byte seed followed by the public key
    return ed25519.Ed25519PrivateKey.from_private_bytes(raw[:32]), "EdDSA"


def cdp_facilitator(key_id: str, key_secret: str) -> FacilitatorConfig:
    key, algorithm = _private_key(key_secret)

    def token(method: str, path: str) -> str:
        now = int(time.time())
        claims = {
            "sub": key_id,
            "iss": "cdp",
            "nbf": now,
            "exp": now + 120,
            "uris": [f"{method} {HOST}{path}"],
        }
        headers = {"kid": key_id, "typ": "JWT", "nonce": secrets.token_hex(8)}
        return "Bearer " + jwt.encode(claims, key, algorithm=algorithm, headers=headers)

    def create_headers() -> dict[str, dict[str, str]]:
        return {
            "verify": {"Authorization": token("POST", f"{ROUTE}/verify")},
            "settle": {"Authorization": token("POST", f"{ROUTE}/settle")},
            "supported": {"Authorization": token("GET", f"{ROUTE}/supported")},
        }

    return FacilitatorConfig(
        url=f"https://{HOST}{ROUTE}", auth_provider=CreateHeadersAuthProvider(create_headers)
    )
