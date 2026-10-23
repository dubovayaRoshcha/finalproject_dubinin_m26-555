import tomllib


class SettingsLoader:
    """Singleton для загруки конфигурации"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        if not hasattr(self, "_settings"):
            with open("pyproject.toml", "rb") as file:
                config = tomllib.load(file)

            self._settings = config["tool"]["valutatrade"]

    def get(self, key, default=None):
        return self._settings.get(key, default)
