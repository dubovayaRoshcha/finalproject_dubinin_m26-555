from datetime import UTC, datetime
from functools import wraps

from valutatrade_hub.logging_config import setup_logging


def log_action(action, verbose=False):
    """Логирование покупки/продажи"""

    def decorator(func):
        @wraps(func)
        def wrapper(user_id, currency_code, amount):
            logger = setup_logging()
            timestamp = datetime.now(UTC).isoformat()

            message = (
                f"{timestamp} {action} user_id={user_id} "
                f"currency='{currency_code}' amount={amount}"
            )

            try:
                result = func(user_id, currency_code, amount)

                details = f" rate={result['rate']:.2f} base='USD' result=OK"

                if verbose:
                    details += (
                        f" balance={result['old_balance']:.4f}"
                        f"->{result['new_balance']:.4f}"
                    )

                logger.info(message + details)
                return result

            except Exception as error:
                logger.info(
                    f"{message} result=ERROR "
                    f"error_type={type(error).__name__} "
                    f"error_message='{error}'"
                )
                raise

        return wrapper

    return decorator
