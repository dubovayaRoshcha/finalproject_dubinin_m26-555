import os


class ParserConfig:
    EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY")

    COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL = "https://v6.exchangerate-api.com/v6"

    BASE_CURRENCY = "USD"

    FIAT_CURRENCIES = ("EUR", "RUB")
    CRYPTO_CURRENCIES = ("BTC", "ETH")

    def __init__(self):
        self.CRYPTO_ID_MAP = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
        }

    RATES_FILE_PATH = "data/rates.json"
    HISTORY_FILE_PATH = "data/exchange_rates.json"

    REQUEST_TIMEOUT = 10
