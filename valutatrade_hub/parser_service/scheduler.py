import time

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import RatesStorage
from valutatrade_hub.parser_service.updater import RatesUpdater


def main():
    clients = {
        "coingecko": CoinGeckoClient(),
        "exchangerate": ExchangeRateApiClient(),
    }

    updater = RatesUpdater(clients, RatesStorage())

    while True:
        try:
            updater.run_update()
        except ApiRequestError as error:
            print(error)

        time.sleep(ParserConfig.UPDATE_INTERVAL)


if __name__ == "__main__":
    main()
