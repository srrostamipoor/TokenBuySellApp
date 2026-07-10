"""
Tests for the token purchase flow.

The blockchain is mocked: unit tests must never touch the network, and must
never require a funded wallet.
"""

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from .models import Account, transaction_list
from .services import BlockchainError, TokenService

VALID_WALLET = "0x79FB56E28e27338cc36a015c35a1497C70987cE3"


class TokenServiceUnitTests(TestCase):
    """Pure functions that need no network access."""

    def test_to_base_units_applies_decimals(self):
        with self.settings(TOKEN_DECIMALS=10):
            self.assertEqual(TokenService.to_base_units(1), 10_000_000_000)
            self.assertEqual(TokenService.to_base_units(5), 50_000_000_000)

    def test_price_scales_with_amount(self):
        with self.settings(TOKEN_PRICE=10_000):
            self.assertEqual(TokenService.price_for(3), Decimal("30000"))


class BuyTokenViewTests(TestCase):
    def setUp(self):
        self.user = Account.objects.create_user(
            first_name="Sara", last_name="R", username="sara",
            phone="0900000000", email="sara@example.com",
            wallet_address=VALID_WALLET, password="testpass123", balance=50_000,
        )
        self.client.force_login(self.user)

    def _post(self, amount):
        return self.client.post(reverse("buy_token"), {"token-value": amount}, follow=True)

    @patch("myapp.views.TokenService")
    def test_successful_purchase_deducts_balance_and_records_transaction(self, MockService):
        MockService.return_value.price_for.return_value = Decimal("10000")
        MockService.return_value.transfer.return_value = "0xabc123"

        self._post(1)

        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, Decimal("40000"))
        self.assertEqual(transaction_list.objects.count(), 1)
        self.assertEqual(transaction_list.objects.first().transaction_txhash, "0xabc123")

    @patch("myapp.views.TokenService")
    def test_insufficient_balance_is_rejected_before_transfer(self, MockService):
        MockService.return_value.price_for.return_value = Decimal("999999")

        self._post(99)

        MockService.return_value.transfer.assert_not_called()
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, Decimal("50000"))
        self.assertEqual(transaction_list.objects.count(), 0)

    @patch("myapp.views.TokenService")
    def test_balance_is_not_deducted_when_the_chain_fails(self, MockService):
        """The critical invariant: never charge a user for a failed transfer."""
        MockService.return_value.price_for.return_value = Decimal("10000")
        MockService.return_value.transfer.side_effect = BlockchainError("reverted")

        self._post(1)

        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, Decimal("50000"))
        self.assertEqual(transaction_list.objects.count(), 0)

    @patch("myapp.views.TokenService")
    def test_zero_and_negative_amounts_are_rejected(self, MockService):
        for amount in (0, -5):
            self._post(amount)
        MockService.return_value.transfer.assert_not_called()

    @patch("myapp.views.TokenService")
    def test_non_numeric_amount_is_rejected(self, MockService):
        self._post("abc")
        MockService.return_value.transfer.assert_not_called()

    def test_anonymous_user_is_redirected_to_login(self):
        self.client.logout()
        response = self.client.post(reverse("buy_token"), {"token-value": 1})
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)
