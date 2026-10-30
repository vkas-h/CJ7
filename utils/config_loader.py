import json
from pathlib import Path
from dataclasses import make_dataclass



CONFIG_DIR = Path("config")


def load_json (filename):

    file_path = CONFIG_DIR / filename


    with open (file_path, "r") as file:
        return json.load(file)


config = load_json("cj7.json")




# _fields = [
#     (key, type(value))
#     for key, value in config.items()
# ]

# Settings = make_dataclass(
#     "Settings",
#     _fields,
#     frozen=True
# )

# settings = Settings(**config)

# print(settings.data_dir)




