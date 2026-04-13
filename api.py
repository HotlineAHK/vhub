import requests
import os

from dotenv import load_dotenv

from headers import headers

# region .env
if not os.path.exists(".env"):
    with open(".env", 'w') as f:
        f.write("SUBSCRIPTION_URL=change_me\n")
    print(f"Файл .env создан с настройками по умолчанию. Пожалуйста, измените файл .env.")
    exit(1)
else:
    print(f"Файл .env найден.")

load_dotenv()

SUBSCRIPTION_URL = os.getenv("SUBSCRIPTION_URL")

if SUBSCRIPTION_URL == None or SUBSCRIPTION_URL == "change_me":
    print(f"Невозможно прочитать URL подписки или вы не заменили заглушку URL, пожалуйста, проверьте файл .env.")
    exit(1)
# endregion


def get_servers() -> requests.Response | str:
    try:
        response = requests.get(SUBSCRIPTION_URL, headers=headers)

        response.raise_for_status()

        return response.text

    except requests.exceptions.RequestException as e:
        return f"Ошибка при выполнении запроса: {e}"