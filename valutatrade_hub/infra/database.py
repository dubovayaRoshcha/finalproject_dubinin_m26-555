from valutatrade_hub.core.utils import load_json, save_json


class DatabaseManager:
    """Singleton для работы с JSON файлами"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def load(self, path):
        return load_json(path)

    def save(self, path, data):
        save_json(path, data)
