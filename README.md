# TokenBuySellApp

A Django web application for buying ERC-20 tokens with an off-chain credit
balance. Users register with an Ethereum wallet address, charge their account,
and purchase **SaraToken (SAR)** — a custom ERC-20 token deployed on the
Sepolia testnet.

Built as an undergraduate final project, then refactored for security and
maintainability.

---

## How it works

The application maintains **two ledgers**:

| Ledger | Where it lives | What it holds |
|---|---|---|
| Credit balance | Django database | Off-chain currency the user charges into their account |
| Token balance | Ethereum (Sepolia) | Real ERC-20 tokens owned by the user's wallet |

Buying a token converts credit into an on-chain transfer:

```
User submits amount
        │
        ▼
Validate amount  ──►  reject if not a positive integer
        │
        ▼
Lock user row, check credit  ──►  reject if insufficient
        │
        ▼
Send ERC-20 transfer from treasury wallet  ──►  on failure: nothing is charged
        │
        ▼
Deduct credit + record transaction hash
```

The order matters: the on-chain transfer happens **before** any credit is
deducted, so a failed or reverted transaction never costs the user anything.

---

## The smart contract

`contracts/TokenFirst.sol` implements the ERC-20 standard.

- **Name / symbol:** SaraToken / SAR
- **Decimals:** 10
- **Total supply:** 10¹² base units = 100 whole tokens
- **Network:** Sepolia testnet

The entire supply is minted to the deployer, who acts as the **treasury**.
When a user buys tokens, the backend signs a `transfer()` call from the
treasury wallet to the user's wallet.

Because the contract targets Solidity 0.8+, arithmetic overflow and underflow
revert automatically — no `SafeMath` library is required.

---

## Project structure

```
myapp/
  models.py              Account, order, invoice, transaction_list
  views.py               HTTP layer — thin, no blockchain code
  services.py            TokenService — all Web3 interaction lives here
  context_processors.py  Injects credit and token balances into templates
  tests.py               Test suite (blockchain mocked)
contracts/
  TokenFirst.sol         The ERC-20 contract source
  MyContract.json        Compiled ABI
mysite/
  settings.py            Configuration, read entirely from the environment
```

Blockchain logic is isolated in `services.py`. Views never import `web3`
directly, which keeps them readable and makes the purchase flow testable
without a network connection.

---

## Getting started

```bash
git clone https://github.com/rossaYY/TokenBuySellApp.git
cd TokenBuySellApp

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Configure your environment:

```bash
cp .env.example .env
```

Then edit `.env` and fill in your own values — a Django secret key, an Infura
(or other RPC) URL, your contract address, and a **dedicated testnet wallet**.

```bash
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000`.

### Running the tests

```bash
python manage.py test
```

The tests mock the blockchain, so they run offline and need no funded wallet.

---

## Security notes

- **No credentials in source.** Every key, address and RPC URL is read from
  `.env`, which is gitignored. `.env.example` documents what is needed.
- **Use a throwaway testnet wallet.** The treasury private key can sign
  transactions on behalf of the treasury. Never point this at a wallet
  holding real funds.
- **Row-level locking.** `select_for_update()` prevents two concurrent
  requests from spending the same credit balance.
- **Graceful degradation.** If Etherscan is unreachable, pages still render
  rather than raising a 500.

---

## Tech stack

Python · Django 4.2 · web3.py · Solidity 0.8 · SQLite · Etherscan API

---

## Status

Coursework project, maintained as a portfolio piece. Deployed only on the
Sepolia testnet; not intended for production or for handling real assets.
