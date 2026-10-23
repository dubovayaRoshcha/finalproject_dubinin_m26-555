from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Класс валюты"""

    def __init__(self, name, code):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Название валюты не может быть пустым")

        if (
            not isinstance(code, str)
            or not 2 <= len(code) <= 5
            or not code.isalpha()
            or not code.isupper()
        ):
            raise ValueError("Некорректный код валюты")

        self.name = name
        self.code = code

    @abstractmethod
    def get_display_info(self):
        pass


class FiatCurrency(Currency):
    """Фиатная валюта"""

    def __init__(self, name, code, issuing_country):
        super().__init__(name, code)
        self.issuing_country = issuing_country

    def get_display_info(self):
        return f"[FIAT] {self.code} - {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """Криптовалюта"""

    def __init__(self, name, code, algorithm, market_cap):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self):
        return (
            f"[CRYPTO] {self.code} - {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


CURRENCIES = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Proof of Stake", 4.5e11),
}


def get_currency(code):
    if code not in CURRENCIES:
        raise CurrencyNotFoundError(code)

    return CURRENCIES[code]
