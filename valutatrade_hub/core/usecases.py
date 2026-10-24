from datetime import UTC, datetime

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import ApiRequestError, CurrencyNotFoundError
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader

db = DatabaseManager()
settings = SettingsLoader()


def register(username, password):
    if not isinstance(username, str) or not username.strip():
        raise ValueError("Имя пользователя не может быть пустым")

    if not isinstance(password, str) or len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    users = db.load(settings.get("users_path"))

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

    db.save(settings.get("users_path"), users)

    portfolios = db.load(settings.get("portfolios_path"))
    portfolios.append({"user_id": user_id, "wallets": {}})
    db.save(settings.get("portfolios_path"), portfolios)

    return new_user


def login(username, password):
    users = db.load(settings.get("users_path"))

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
    portfolios = db.load(settings.get("portfolios_path"))

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
    portfolios = db.load(settings.get("portfolios_path"))

    for portfolio_data in portfolios:
        if portfolio_data["user_id"] == portfolio.user_id:
            portfolio_data["wallets"] = {
                code: {"balance": wallet.balance}
                for code, wallet in portfolio.wallets.items()
            }
            db.save(settings.get("portfolios_path"), portfolios)
            return

    raise ValueError("Портфель пользователя не найден")


def get_portfolio_by_id(user_id):
    users = db.load(settings.get("users_path"))

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


@log_action("BUY", verbose=True)
def buy(user_id, currency_code, amount):
    get_currency(currency_code)

    portfolio = get_portfolio_by_id(user_id)
    portfolio.add_currency(currency_code)

    wallet = portfolio.get_wallet(currency_code)
    if wallet is None:
        raise ValueError("Кошелёк не найден")

    old_balance = wallet.balance
    rate = get_rate(currency_code, "USD")["rate"]

    wallet.deposit(amount)

    save_portfolio(portfolio)

    return {
        "currency": currency_code,
        "amount": amount,
        "old_balance": old_balance,
        "new_balance": wallet.balance,
        "rate": rate,
        "total": amount * rate,
    }


@log_action("SELL", verbose=True)
def sell(user_id, currency_code, amount):
    get_currency(currency_code)

    portfolio = get_portfolio_by_id(user_id)
    wallet = portfolio.get_wallet(currency_code)

    if wallet is None:
        raise ValueError(f"У вас нет кошелька '{currency_code}'")

    old_balance = wallet.balance
    rate = get_rate(currency_code, "USD")["rate"]

    wallet.withdraw(amount)

    save_portfolio(portfolio)

    return {
        "currency": currency_code,
        "amount": amount,
        "old_balance": old_balance,
        "new_balance": wallet.balance,
        "rate": rate,
        "total": amount * rate,
    }


def get_rate(from_code, to_code):
    get_currency(from_code)
    get_currency(to_code)

    rates = db.load(settings.get("rates_path"))

    if not rates or not rates.get("pairs"):
        raise ApiRequestError("Кеш курсов пуст. Выполните update-rates")

    last_refresh = rates.get("last_refresh")

    if not last_refresh:
        raise ApiRequestError("Нет времени обновления курсов")

    pairs = rates["pairs"]

    now = datetime.now(UTC)
    ttl = settings.get("rates_ttl_seconds")

    for code in (from_code, to_code):
        if code == "USD":
            continue

        pair = pairs[f"{code}_USD"]
        updated_at = datetime.fromisoformat(pair["updated_at"])
        elapsed = (now - updated_at).total_seconds()

        if elapsed > ttl:
            raise ApiRequestError(f"Курс {code} устарел. Выполните update-rates")

    if from_code != "USD" and f"{from_code}_USD" not in pairs:
        raise ApiRequestError(f"Курс {from_code}->USD недоступен")

    if to_code != "USD" and f"{to_code}_USD" not in pairs:
        raise ApiRequestError(f"Курс {to_code}->USD недоступен")

    from_rate = 1.0 if from_code == "USD" else pairs[f"{from_code}_USD"]["rate"]
    to_rate = 1.0 if to_code == "USD" else pairs[f"{to_code}_USD"]["rate"]

    rate = from_rate / to_rate

    return {
        "from": from_code,
        "to": to_code,
        "rate": rate,
        "reverse_rate": 1 / rate,
        "updated_at": last_refresh,
    }


def show_portfolio(user_id, base_currency="USD"):
    try:
        get_currency(base_currency)
    except CurrencyNotFoundError:
        raise ValueError(f"Неизвестная базовая валюта '{base_currency}'") from None

    portfolio = get_portfolio_by_id(user_id)

    wallets = []
    rates = {"USD": 1.0}

    for code in portfolio.wallets:
        rates[code] = get_rate(code, "USD")["rate"]

    rates[base_currency] = get_rate(base_currency, "USD")["rate"]

    total = portfolio.get_total_value(base_currency, rates)

    for code, wallet in portfolio.wallets.items():
        value = wallet.balance * rates[code] / rates[base_currency]

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


def show_rates(currency=None, top=None, base="USD"):
    get_currency(base)

    if currency:
        get_currency(currency)

    data = db.load(settings.get("rates_path"))
    pairs = data.get("pairs", {})

    if not pairs:
        raise ValueError("Кеш курсов пуст. Выполните update-rates")

    rates = {"USD": 1.0}

    for pair, info in pairs.items():
        code = pair.split("_")[0]
        rates[code] = info["rate"]

    if base not in rates:
        raise ValueError(f"Курс для '{base}' не найден в кеше")

    result = []

    for pair, info in pairs.items():
        code = pair.split("_")[0]

        if currency and code != currency:
            continue

        if top is not None and code not in ("BTC", "ETH"):
            continue

        result.append(
            {
                "currency": code,
                "rate": rates[code] / rates[base],
                "updated_at": info["updated_at"],
            }
        )

    if currency and not result:
        raise ValueError(f"Курс для '{currency}' не найден в кеше")

    result.sort(key=lambda item: item["rate"], reverse=True)

    if top is not None:
        if top <= 0:
            raise ValueError("Значение --top должно быть положительным")
        result = result[:top]

    return result
