from datetime import UTC, datetime

from valutatrade_hub.core.models import EXCHANGE_RATES, Portfolio, User
from valutatrade_hub.core.utils import load_json, save_json


def register(username, password):
    if not isinstance(username, str) or not username.strip():
        raise ValueError("Имя пользователя не может быть пустым")

    if not isinstance(password, str) or len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    users = load_json("data/users.json")

    for user in users:
        if user["username"] == username:
            raise ValueError(f"Имя пользователя '{username}' уже занято")

    user_id = max((user["user_id"] for user in users), default=0) + 1

    new_user = User(user_id, username, "", "", datetime.now(UTC))
    new_user.change_password(password)

    users.append(
        {
            "user_id": new_user.user_id,
            "username": new_user.username,
            "hashed_password": new_user.hashed_password,
            "salt": new_user.salt,
            "registration_date": new_user.registration_date.isoformat(),
        }
    )

    save_json("data/users.json", users)

    portfolios = load_json("data/portfolios.json")
    portfolios.append({"user_id": user_id, "wallets": {}})
    save_json("data/portfolios.json", portfolios)

    return new_user


def login(username, password):
    users = load_json("data/users.json")

    for user_data in users:
        if user_data["username"] == username:
            user = User(
                user_data["user_id"],
                user_data["username"],
                user_data["hashed_password"],
                user_data["salt"],
                datetime.fromisoformat(user_data["registration_date"]),
            )

            if not user.verify_password(password):
                raise ValueError("Неверный пароль")

            return user

    raise ValueError(f"Пользователь '{username}' не найден")


def get_portfolio(user):
    portfolios = load_json("data/portfolios.json")

    for portfolio_data in portfolios:
        if portfolio_data["user_id"] == user.user_id:
            portfolio = Portfolio(user.user_id, user)

            for code, wallet_data in portfolio_data["wallets"].items():
                portfolio.add_currency(code)

                wallet = portfolio.get_wallet(code)
                if wallet is not None:
                    wallet.balance = wallet_data["balance"]

            return portfolio

    raise ValueError("Портфель пользователя не найден")


def save_portfolio(portfolio):
    portfolios = load_json("data/portfolios.json")

    for portfolio_data in portfolios:
        if portfolio_data["user_id"] == portfolio.user_id:
            portfolio_data["wallets"] = {
                code: {"balance": wallet.balance}
                for code, wallet in portfolio.wallets.items()
            }
            save_json("data/portfolios.json", portfolios)
            return

    raise ValueError("Портфель пользователя не найден")


def get_portfolio_by_id(user_id):
    users = load_json("data/users.json")

    for user_data in users:
        if user_data["user_id"] == user_id:
            user = User(
                user_data["user_id"],
                user_data["username"],
                user_data["hashed_password"],
                user_data["salt"],
                datetime.fromisoformat(user_data["registration_date"]),
            )
            return get_portfolio(user)

    raise ValueError("Пользователь не найден")


def buy(user_id, currency_code, amount):
    if currency_code not in EXCHANGE_RATES:
        raise ValueError(f"Неизвестная валюта '{currency_code}'")

    portfolio = get_portfolio_by_id(user_id)
    portfolio.add_currency(currency_code)

    wallet = portfolio.get_wallet(currency_code)
    if wallet is None:
        raise ValueError("Кошелёк не найден")

    old_balance = wallet.balance
    wallet.deposit(amount)

    save_portfolio(portfolio)

    return {
        "currency": currency_code,
        "amount": amount,
        "old_balance": old_balance,
        "new_balance": wallet.balance,
        "rate": EXCHANGE_RATES[currency_code],
        "total": amount * EXCHANGE_RATES[currency_code],
    }


def sell(user_id, currency_code, amount):
    if currency_code not in EXCHANGE_RATES:
        raise ValueError(f"Неизвестная валюта '{currency_code}'")

    portfolio = get_portfolio_by_id(user_id)
    wallet = portfolio.get_wallet(currency_code)

    if wallet is None:
        raise ValueError(f"У вас нет кошелька '{currency_code}'")

    old_balance = wallet.balance
    wallet.withdraw(amount)

    save_portfolio(portfolio)

    return {
        "currency": currency_code,
        "amount": amount,
        "old_balance": old_balance,
        "new_balance": wallet.balance,
        "rate": EXCHANGE_RATES[currency_code],
        "total": amount * EXCHANGE_RATES[currency_code],
    }


def get_rate(from_code, to_code):
    if from_code not in EXCHANGE_RATES:
        raise ValueError(f"Неизвестная валюта '{from_code}'")

    if to_code not in EXCHANGE_RATES:
        raise ValueError(f"Неизвестная валюта '{to_code}'")

    rate = EXCHANGE_RATES[from_code] / EXCHANGE_RATES[to_code]

    return {
        "from": from_code,
        "to": to_code,
        "rate": rate,
        "reverse_rate": 1 / rate,
        "updated_at": datetime.now(UTC).isoformat(),
    }


def show_portfolio(user_id, base_currency="USD"):
    if base_currency not in EXCHANGE_RATES:
        raise ValueError(f"Неизвестная базовая валюта '{base_currency}'")

    portfolio = get_portfolio_by_id(user_id)
    total = portfolio.get_total_value(base_currency)

    wallets = []

    for code, wallet in portfolio.wallets.items():
        value = wallet.balance * EXCHANGE_RATES[code] / EXCHANGE_RATES[base_currency]

        wallets.append(
            {
                "currency": code,
                "balance": wallet.balance,
                "value": value,
            }
        )

    return {
        "base": base_currency,
        "wallets": wallets,
        "total": total,
    }
