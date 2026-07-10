"""
Template context processors.

These run on *every* request, so they must never raise: a failure in an
external API call should degrade gracefully, not break the whole site.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

ETHERSCAN_TIMEOUT = 5  # seconds


def balance(request):
    """The user's off-chain credit balance."""
    if not request.user.is_authenticated:
        return {"balance": 0}
    return {"balance": request.user.balance}


def token(request):
    """
    The user's on-chain token balance, read from Etherscan.

    Returns 0 if the user is anonymous, has no wallet, or the API is
    unavailable -- the page should still render.
    """
    if not request.user.is_authenticated:
        return {"token": 0}

    address = getattr(request.user, "wallet_address", None)
    if not address:
        return {"token": 0}

    if not settings.ETHERSCAN_API_KEY:
        logger.warning("ETHERSCAN_API_KEY is not configured")
        return {"token": 0}

    params = {
        "module": "account",
        "action": "tokenbalance",
        "contractaddress": settings.TOKEN_CONTRACT_ADDRESS,
        "address": address,
        "tag": "latest",
        "apikey": settings.ETHERSCAN_API_KEY,
    }

    try:
        response = requests.get(
            settings.ETHERSCAN_API_URL, params=params, timeout=ETHERSCAN_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Etherscan lookup failed: %s", exc)
        return {"token": 0}

    if data.get("status") != "1":
        logger.info("Etherscan returned no balance: %s", data.get("message"))
        return {"token": 0}

    try:
        raw = int(data["result"])
    except (KeyError, TypeError, ValueError):
        return {"token": 0}

    return {"token": raw // (10 ** settings.TOKEN_DECIMALS)}
