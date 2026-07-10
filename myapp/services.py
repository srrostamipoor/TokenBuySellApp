"""
Blockchain service layer.

All Ethereum interaction lives here, isolated from Django views. This keeps
the views thin, makes the Web3 logic testable in isolation, and ensures no
credential ever appears in application code.

The ERC-20 token is deployed on the Sepolia testnet. The treasury wallet
holds the total supply and transfers tokens to users when they buy.
"""

import json
import logging
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from web3 import Web3
from web3.exceptions import Web3Exception

logger = logging.getLogger(__name__)

CONTRACT_ABI_PATH = Path(settings.BASE_DIR) / "contracts" / "MyContract.json"


class BlockchainError(Exception):
    """Raised when an on-chain operation cannot be completed."""


class TokenService:
    """Wraps the ERC-20 token contract and the treasury wallet."""

    def __init__(self):
        self._validate_config()
        self.w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))
        self.treasury = Web3.to_checksum_address(settings.TREASURY_ADDRESS)
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(settings.TOKEN_CONTRACT_ADDRESS),
            abi=self._load_abi(),
        )

    # ------------------------------------------------------------------ #
    # configuration
    # ------------------------------------------------------------------ #
    @staticmethod
    def _validate_config():
        required = [
            "WEB3_PROVIDER_URL",
            "TOKEN_CONTRACT_ADDRESS",
            "TREASURY_ADDRESS",
            "TREASURY_PRIVATE_KEY",
        ]
        missing = [name for name in required if not getattr(settings, name, None)]
        if missing:
            raise BlockchainError(
                "Missing blockchain settings: " + ", ".join(missing) +
                ". Copy .env.example to .env and fill it in."
            )

    @staticmethod
    def _load_abi():
        try:
            with open(CONTRACT_ABI_PATH) as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            raise BlockchainError(f"Could not read contract ABI: {exc}") from exc

    # ------------------------------------------------------------------ #
    # unit conversion
    # ------------------------------------------------------------------ #
    @staticmethod
    def to_base_units(token_amount: int) -> int:
        """Convert a human token amount into the contract's integer units."""
        return int(token_amount) * (10 ** settings.TOKEN_DECIMALS)

    @staticmethod
    def price_for(token_amount: int) -> Decimal:
        """Fiat/credit cost of buying `token_amount` tokens."""
        return Decimal(token_amount) * Decimal(settings.TOKEN_PRICE)

    # ------------------------------------------------------------------ #
    # on-chain operations
    # ------------------------------------------------------------------ #
    def is_connected(self) -> bool:
        try:
            return self.w3.is_connected()
        except Web3Exception:
            return False

    def transfer(self, recipient: str, token_amount: int) -> str:
        """
        Send `token_amount` tokens from the treasury to `recipient`.

        Returns the transaction hash on success.
        Raises BlockchainError if the transfer fails or is reverted.
        """
        try:
            recipient = Web3.to_checksum_address(recipient)
        except ValueError as exc:
            raise BlockchainError(f"Invalid wallet address: {recipient}") from exc

        value = self.to_base_units(token_amount)

        try:
            tx = self.contract.functions.transfer(recipient, value).build_transaction({
                "from": self.treasury,
                "nonce": self.w3.eth.get_transaction_count(self.treasury),
                "gas": 200_000,
                "gasPrice": self.w3.eth.gas_price,
            })

            signed = self.w3.eth.account.sign_transaction(
                tx, private_key=settings.TREASURY_PRIVATE_KEY
            )
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

        except Web3Exception as exc:
            logger.exception("Token transfer failed")
            raise BlockchainError("The blockchain transaction could not be sent.") from exc

        if receipt.status != 1:
            logger.error("Transfer reverted, tx=%s", tx_hash.hex())
            raise BlockchainError("The blockchain transaction was reverted.")

        return tx_hash.hex()

    def balance_of(self, address: str) -> int:
        """Read a wallet's token balance directly from the contract."""
        try:
            address = Web3.to_checksum_address(address)
            raw = self.contract.functions.balanceOf(address).call()
        except (ValueError, Web3Exception) as exc:
            raise BlockchainError(f"Could not read balance: {exc}") from exc
        return raw // (10 ** settings.TOKEN_DECIMALS)
