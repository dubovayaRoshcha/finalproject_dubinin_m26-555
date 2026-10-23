class InsufficientFundsError(Exception):
    """Недостаточно средств в кошельке"""

    def __init__(self, available, required, code):
        super().__init__(
            f"Недостаточно средств: доступно {available:.4f} {code}, "
            f"требуется {required:.4f} {code}"
        )


class CurrencyNotFoundError(Exception):
    """Неизвестная валюта"""

    def __init__(self, code):
        super().__init__(f"Неизвестная валюта '{code}'")


class ApiRequestError(Exception):
    """Ошибка обращения к внешнему API"""

    def __init__(self, reason):
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")
