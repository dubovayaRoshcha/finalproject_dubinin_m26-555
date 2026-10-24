from datetime import UTC, datetime

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.logging_config import setup_parser_logging

logger = setup_parser_logging()


class RatesUpdater:
    """Обновление курсов через внешние API"""

    def __init__(self, clients, storage):
        self.clients = clients
        self.storage = storage

    def run_update(self):
        logger.info("Начало обновления курсов")

        new_rates = {}
        errors = []

        for name, client in self.clients.items():
            try:
                rates = client.fetch_rates()
                now = datetime.now(UTC).isoformat()

                for pair, rate in rates.items():
                    new_rates[pair] = {
                        "rate": rate,
                        "updated_at": now,
                        "source": name,
                    }

                logger.info("%s: получено %s курсов", name, len(rates))

            except ApiRequestError as error:
                logger.error("%s: %s", name, error)
                errors.append(str(error))

        if not new_rates:
            raise ApiRequestError("Не удалось обновить курсы")

        updated_count = self.storage.save_rates(new_rates)

        logger.info("Обновление завершено. Сохранено курсов: %s", updated_count)

        return {
            "updated_count": updated_count,
            "errors": errors,
            "last_refresh": datetime.now(UTC).isoformat(),
        }
