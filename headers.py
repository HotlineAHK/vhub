import yaml
import os
import secrets

from devices import device_list

if not os.path.exists("config.yaml"):
    random_hwid = secrets.token_hex(8).upper()
    random_device = secrets.choice(device_list)

    with open("config.yaml", 'w') as f:
        yaml.dump({"User-Agent": "v2raytun/android", "X-Device-Os": "Android", "X-Device-Locale": secrets.choice(["ru", "en"]), "X-Device-Model": str(random_device), "X-Ver-Os": str(9 + secrets.randbelow(7)), "Connection": "close", "X-Hwid": str(random_hwid)}, f)
    print(f"Файл config.yaml не был найден и был создан автоматически. Пожалуйста, измените файл config.yaml.")
    exit(1)
else:
    print(f"Файл config.yaml был найден.")
    config = yaml.safe_load(open("config.yaml", 'r'))

headers = {
    "User-Agent": config["User-Agent"],
    "X-Device-Os": config["X-Device-Os"],
    "X-Device-Locale": config["X-Device-Locale"],
    "X-Device-Model": config["X-Device-Model"],
    "X-Ver-Os": config["X-Ver-Os"],
    "Connection": "close",
    "X-Hwid": config["X-Hwid"]
}