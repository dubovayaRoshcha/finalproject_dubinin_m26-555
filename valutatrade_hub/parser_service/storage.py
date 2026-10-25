import json
import os
from datetime import UTC, datetime
from pathlib import Path

from valutatrade_hub.parser_service.config import ParserConfig


class RatesStorage:
    """Хранение текущих курсов и истории обновлений"""

    def __init__(self):
        config = ParserConfig()
        self.rates_path = Path(config.RATES_FILE_PATH)
        self.history_path = Path(config.HISTORY_FILE_PATH)

    def load(self, path, default):
        if not path.exists():
            return default

        with open(path, encoding="utf-8") as file:
            return json.load(file)

    def save(self, path, data):
        temp_path = path.with_suffix(".tmp")

        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        os.replace(temp_path, path)

    def save_rates(self, new_rates):
        rates = self.load(self.rates_path, {})
        history = self.load(self.history_path, [])

        if not rates:
            rates["pairs"] = {}

        now = datetime.now(UTC).isoformat()
        updated_count = 0

        for pair, data in new_rates.items():
            timestamp = data["updated_at"]
            old_data = rates["pairs"].get(pair)

            if old_data and datetime.fromisoformat(
                old_data["updated_at"]
            ) >= datetime.fromisoformat(timestamp):
                continue

            record_id = f"{pair}_{timestamp}"
            if any(record["id"] == record_id for record in history):
                continue

            from_code, to_code = pair.split("_")

            history.append(
                {
                    "id": record_id,
                    "from_currency": from_code,
                    "to_currency": to_code,
                    "rate": data["rate"],
                    "timestamp": timestamp,
                    "source": data["source"],
                    "meta": {},
                }
            )

            rates["pairs"][pair] = data
            updated_count += 1

        if updated_count > 0:
            rates["last_refresh"] = now
            self.save(self.history_path, history)
            self.save(self.rates_path, rates)

        return updated_count
