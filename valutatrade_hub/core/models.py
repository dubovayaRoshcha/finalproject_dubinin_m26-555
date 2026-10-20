import hashlib
import math
import secrets
from datetime import datetime


class User:
    """Пользователь"""

    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ):
        self._user_id = user_id
        self.username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def user_id(self):
        return self._user_id

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value

    @property
    def hashed_password(self):
        return self._hashed_password

    @property
    def salt(self):
        return self._salt

    @property
    def registration_date(self):
        return self._registration_date

    def change_password(self, new_password):
        if not isinstance(new_password, str) or len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        self._salt = secrets.token_hex(16)
        self._hashed_password = hashlib.pbkdf2_hmac(
            "sha256", new_password.encode(), bytes.fromhex(self._salt), 100000
        ).hex()

    def verify_password(self, password):
        if not isinstance(password, str):
            return False
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(self._salt), 100000
        ).hex()

        return secrets.compare_digest(password_hash, self._hashed_password)

    def get_user_info(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "registration_date": self.registration_date.isoformat(),
        }


class Wallet:
    """Кошелек для хранения одной валюты"""

    def __init__(self, currency_code, balance=0.0):
        self.currency_code = currency_code
        self.balance = balance

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")

        if not math.isfinite(value) or value < 0:
            raise ValueError("Баланс должен быть неотрицательным")

        self._balance = float(value)

    def deposit(self, amount):
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise TypeError("Сумма должна быть числом")

        if not math.isfinite(amount) or amount <= 0:
            raise ValueError("Сумма должна быть положительным числом")

        self.balance += amount

    def withdraw(self, amount):
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise TypeError("Сумма должна быть числом")

        if not math.isfinite(amount) or amount <= 0:
            raise ValueError("Сумма должна быть положительным числом")

        if amount > self.balance:
            raise ValueError(
                f"Недостаточно средств: доступно {self.balance} {self.currency_code}, "
                f"требуется {amount} {self.currency_code}"
            )

        self.balance -= amount

    def get_balance_info(self):
        return f"{self.currency_code}: {self.balance:.4f}"


EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 1.08,
    "BTC": 59337.21,
    "ETH": 3720.0,
    "RUB": 0.01,
}


class Portfolio:
    """Портфель кошельков пользователя"""

    def __init__(self, user_id, user=None):
        self._user_id = user_id
        self._user = user
        self._wallets = {}

    @property
    def user(self):
        return self._user

    @property
    def user_id(self):
        return self._user_id

    @property
    def wallets(self):
        return self._wallets.copy()

    def add_currency(self, currency_code):
        if currency_code not in self._wallets:
            self._wallets[currency_code] = Wallet(currency_code)

    def get_wallet(self, currency_code):
        return self._wallets.get(currency_code)

    def get_total_value(self, base_currency="USD", rates=None):
        if rates is None:
            rates = EXCHANGE_RATES

        if base_currency not in rates:
            raise ValueError(f"Неизвестная базовая валюта '{base_currency}'")

        total = 0.0

        for code, wallet in self._wallets.items():
            if code not in rates:
                raise ValueError(f"Курс для валюты '{code}' не найден")

            total += wallet.balance * rates[code] / rates[base_currency]

        return total
