import base64
import os

import requests
import yaml

from dotenv import load_dotenv

from headers import headers

# region .env
if not os.path.exists(".env"):
    with open(".env", 'w') as f:
        f.write("SUBSCRIPTION_URL=change_me\n")
    print(f"Файл .env не был найден и был создан автоматически с заглушкой вместо реального URL подписки. Пожалуйста, измените файл .env.")
    exit(1)
else:
    print(f"Файл .env был найден.")

load_dotenv()

SUBSCRIPTION_URL = os.getenv("SUBSCRIPTION_URL")

if SUBSCRIPTION_URL == None or SUBSCRIPTION_URL == "change_me":
    print(f"Невозможно прочитать URL подписки или вы не заменили заглушку URL, пожалуйста, проверьте файл .env.")
    exit(1)
# endregion

# region error fallback config
LAST_CONFIG_PATH = ".last_config.b64"
ERROR_UUID = "00000000-0000-0000-0000-000000000000"
ERROR_HOST = "0.0.0.0"

def _get_force_error_enabled() -> bool:
    """При error_fallback: true принудительно вызывается ошибка для проверки fallback-механизма."""
    try:
        if os.path.exists("config.yaml"):
            with open("config.yaml", 'r') as f:
                config = yaml.safe_load(f)
                if isinstance(config, dict):
                    return config.get("error_fallback", False)
    except Exception:
        pass
    return False

def _build_fallback_response(saved_b64: str, error_msg: str) -> str:
    """
    Decode saved BASE64, prepend 3 fake vless:// servers that show as errors in the client.
    """
    try:
        decoded = base64.b64decode(saved_b64).decode("utf-8")
    except Exception:
        return saved_b64

    base = f"vless://{ERROR_UUID}@{ERROR_HOST}:0?encryption=none&type=tcp&security=none"

    error_servers = [
        f"{base}#-",
        f"{base}#⚠️ {error_msg}",
        f"{base}#-",
    ]

    new_config = "\n".join(error_servers + decoded.strip().split("\n"))
    return base64.b64encode(new_config.encode("utf-8")).decode("utf-8")
# endregion


def get_servers() -> str:
    force_error = _get_force_error_enabled()
    if SUBSCRIPTION_URL == None or SUBSCRIPTION_URL == "change_me":
        return _build_fallback_response("", "Не указан URL подписки в .env")
    try:
        if force_error:
            raise requests.exceptions.RequestException(
                "Принудительная проверка fallback-механизма"
            )

        response = requests.get(SUBSCRIPTION_URL, headers=headers)

        response.raise_for_status()

        # Always save the last successfully received BASE64 config
        with open(LAST_CONFIG_PATH, 'w') as f:
            f.write(response.text)

        return response.text

    except requests.exceptions.RequestException as e:
        # Always try fallback if a saved config exists
        if os.path.exists(LAST_CONFIG_PATH):
            try:
                with open(LAST_CONFIG_PATH, 'r') as f:
                    saved_b64 = f.read()
                return _build_fallback_response(saved_b64, str(e))
            except Exception:
                pass

        return f"Ошибка при выполнении запроса: {e}"