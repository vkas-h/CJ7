from pathlib import Path
from utils.config_loader import load_json


config = load_json("cj7.json")



def show_banner():
    print(r"""
 ██████╗      ████╗  ████████╗
██╔════╝        ██╗  ╚════██║
██║             ██║       ██╔╝
██║        ██║  ██║      ██╔╝
╚██████╗   ╚██████╔╝    ██╔╝
 ╚═════╝    ╚═════╝     ╚═╝

CJ7 v0.4  •  modular desktop assistant  •  plugin runtime
""")
