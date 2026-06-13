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

def _get_error_fallback_enabled() -> bool:
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
    """Decode saved BASE64, append 3 dummy servers: dash, error, dash, then re-encode."""
    try:
        decoded = base64.b64decode(saved_b64).decode("utf-8")
    except Exception:
        # If saved data is corrupted, return raw saved data as-is
        return saved_b64

    lines = decoded.strip().split("\n")

    error_lines = [
        "-",
        f"# subscription error: {error_msg}",
        "-",
    ]

    new_config = "\n".join(lines + [""] + error_lines)
    return base64.b64encode(new_config.encode("utf-8")).decode("utf-8")
# endregion


def get_servers() -> str:
    error_fallback = _get_error_fallback_enabled()

    try:
        response = requests.get(SUBSCRIPTION_URL, headers=headers)

        response.raise_for_status()

        # Save the last successfully received BASE64 config
        if error_fallback:
            with open(LAST_CONFIG_PATH, 'w') as f:
                f.write(response.text)

        return response.text

    except requests.exceptions.RequestException as e:
        if error_fallback and os.path.exists(LAST_CONFIG_PATH):
            try:
                with open(LAST_CONFIG_PATH, 'r') as f:
                    saved_b64 = f.read()
                return _build_fallback_response(saved_b64, str(e))
            except Exception:
                pass

        return f"Ошибка при выполнении запроса: {e}"