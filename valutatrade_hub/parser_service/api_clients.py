from abc import ABC, abstractmethod

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    """Общий интерфейс для получения курсов"""

    @abstractmethod
    def fetch_rates(self):
        pass


class CoinGeckoClient(BaseApiClient):
    """Получение курсов криптовалют"""

    def __init__(self):
        self.config = ParserConfig()

    def fetch_rates(self):
        params = {
            "ids": ",".join(self.config.CRYPTO_ID_MAP.values()),
            "vs_currencies": "usd",
        }

        try:
            response = requests.get(
                self.config.COINGECKO_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            rates = {}

            for code, crypto_id in self.config.CRYPTO_ID_MAP.items():
                rate = data[crypto_id]["usd"]

                if (
                    not isinstance(rate, (int, float))
                    or isinstance(rate, bool)
                    or rate <= 0
                ):
                    raise ValueError("Некорректный курс валюты")

                rates[f"{code}_USD"] = rate

            return rates

        except (
            requests.exceptions.RequestException,
            ValueError,
            KeyError,
            TypeError,
        ) as error:
            raise ApiRequestError(f"CoinGecko: {error}") from error


class ExchangeRateApiClient(BaseApiClient):
    """Получение курсов фиатных валют"""

    def __init__(self):
        self.config = ParserConfig()

    def fetch_rates(self):
        if not self.config.EXCHANGERATE_API_KEY:
            raise ApiRequestError("Не указан API-ключ ExchangeRate-API")

        url = (
            f"{self.config.EXCHANGERATE_API_URL}/"
            f"{self.config.EXCHANGERATE_API_KEY}/latest/"
            f"{self.config.BASE_CURRENCY}"
        )

        try:
            response = requests.get(
                url,
                timeout=self.config.REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("result") != "success":
                raise ValueError("API вернул ошибку")

            rates = {}

            for code in self.config.FIAT_CURRENCIES:
                rate = data["conversion_rates"][code]

                if (
                    not isinstance(rate, (int, float))
                    or isinstance(rate, bool)
                    or rate <= 0
                ):
                    raise ValueError("Некорректный курс валюты")

                rates[f"{code}_USD"] = 1 / rate

            return rates

        except requests.exceptions.HTTPError:
            raise ApiRequestError(
                f"ExchangeRate-API: HTTP-ошибка {response.status_code}"
            ) from None

        except requests.exceptions.RequestException:
            raise ApiRequestError("ExchangeRate-API: ошибка соединения") from None

        except (ValueError, KeyError, TypeError, ZeroDivisionError):
            raise ApiRequestError(
                "ExchangeRate-API: некорректный ответ сервера"
            ) from None
