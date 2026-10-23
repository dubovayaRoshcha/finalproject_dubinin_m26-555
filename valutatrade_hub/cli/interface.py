import shlex

from prettytable import PrettyTable

from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.usecases import (
    buy,
    get_rate,
    login,
    register,
    sell,
    show_portfolio,
)


def parse_args(args):
    result = {}

    for i in range(0, len(args), 2):
        if i + 1 >= len(args) or not args[i].startswith("--"):
            raise ValueError("Некорректные аргументы команды")

        result[args[i][2:]] = args[i + 1]

    return result


def main():
    current_user = None

    print("ValutaTrade Hub. Введите help для списка команд.")

    while True:
        try:
            command_line = input("> ")
            parts = shlex.split(command_line)

            if not parts:
                continue

            command = parts[0]

            if command in ("exit", "quit"):
                break

            if command == "help":
                print("register --username NAME --password PASS")
                print("login --username NAME --password PASS")
                print("show-portfolio [--base USD]")
                print("buy --currency BTC --amount 0.05")
                print("sell --currency BTC --amount 0.01")
                print("get-rate --from USD --to BTC")
                print("exit")
                continue

            args = parse_args(parts[1:])

            if command == "register":
                user = register(args["username"], args["password"])
                print(
                    f"Пользователь '{user.username}' зарегистрирован (id={user.user_id})"
                )

            elif command == "login":
                current_user = login(args["username"], args["password"])
                print(f"Вы вошли как '{current_user.username}'")

            elif command == "get-rate":
                result = get_rate(args["from"], args["to"])
                print(f"Курс {result['from']}->{result['to']}: {result['rate']:.8f}")
                print(
                    f"Обратный курс {result['to']}->{result['from']}: "
                    f"{result['reverse_rate']:.8g}"
                )
                print(f"Обновлено: {result['updated_at']}")

            elif command in ("buy", "sell", "show-portfolio"):
                if current_user is None:
                    print("Сначала выполните login")
                    continue

                if command == "buy":
                    result = buy(
                        current_user.user_id,
                        args["currency"],
                        float(args["amount"]),
                    )

                    print(
                        f"Покупка выполнена: {result['amount']:.4f} {result['currency']} "
                        f"по курсу {result['rate']:.2f} USD"
                    )
                    print(
                        f"Баланс: {result['old_balance']:.4f} -> "
                        f"{result['new_balance']:.4f}"
                    )
                    print(f"Оценочная стоимость покупки: {result['total']:.2f} USD")

                elif command == "sell":
                    result = sell(
                        current_user.user_id,
                        args["currency"],
                        float(args["amount"]),
                    )

                    print(
                        f"Продажа выполнена: {result['amount']:.4f} {result['currency']} "
                        f"по курсу {result['rate']:.2f} USD"
                    )
                    print(
                        f"Баланс: {result['old_balance']:.4f} -> "
                        f"{result['new_balance']:.4f}"
                    )
                    print(f"Оценочная выручка: {result['total']:.2f} USD")

                else:
                    result = show_portfolio(
                        current_user.user_id,
                        args.get("base", "USD"),
                    )

                    if not result["wallets"]:
                        print("Портфель пуст")
                        continue

                    table = PrettyTable()
                    table.field_names = ["Валюта", "Баланс", "Стоимость"]

                    for wallet in result["wallets"]:
                        table.add_row(
                            [
                                wallet["currency"],
                                f"{wallet['balance']:.4f}",
                                f"{wallet['value']:.2f}",
                            ]
                        )

                    print(table)
                    print(f"ИТОГО: {result['total']:.2f} {result['base']}")

            else:
                print("Неизвестная команда. Введите help.")

        except InsufficientFundsError as error:
            print(error)

        except CurrencyNotFoundError as error:
            print(f"{error}. Используйте help для списка команд")

        except ApiRequestError as error:
            print(f"{error}. Повторите попытку позже")

        except (ValueError, TypeError, KeyError) as error:
            print(f"Ошибка: {error}")

        except EOFError:
            break
