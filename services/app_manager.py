import os
import json
import subprocess
from pathlib import Path
from config.settings import config

APP_FILE =config["app_registry"]

START_MENU=[
    Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"),
    Path(os.getenv("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
]


def initialize():

    apps = load_apps()

    if not apps:
        scan_apps()


# def scan_appids():

#     apps = {}

#     try:
#         result = subprocess.run(
#             ["powershell", "-Command", "Get-StartApps"],
#             capture_output=True,
#             text=True
#         )

#         lines = result.stdout.splitlines()[2:]  # skip header

#         for line in lines:

#             line = line.strip()

#             if not line:
#                 continue

#             # split from RIGHT → AppID is always last
#             parts = line.rsplit(None, 1)

#             if len(parts) != 2:
#                 continue

#             name, appid = parts

#             apps[name.lower()] = {
#                 "type": "appid",
#                 "value": appid
#             }

#     except Exception as e:
#         print("Failed to scan AppIDs:", e)

#     return apps




def scan_appids():
    apps = {}

    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-StartApps | ConvertTo-Json -Depth 2"],
            capture_output=True,
            text=True
        )

        data = json.loads(result.stdout)

        if not isinstance(data, list):
            data = [data]

        for entry in data:
            name = str(entry.get("Name", "")).strip().lower()
            appid = str(entry.get("AppID", "")).strip()

            if name and appid:
                apps[name] = {
                    "type": "appid",
                    "value": appid
                }

    except Exception as e:
        print("Failed to scan AppIDs:", e)

    return apps


#--------------------------




def scan_apps ():
    apps = {}


    #ink scan 

    for folder in START_MENU:
        if not folder.exists():
            continue

        for file in folder.rglob("*.lnk"):
            app_name=file.stem.lower()

            apps[app_name] = {
                "type": "lnk",
                "value": str(file)
            }


    #App-id scan

    appid_apps = scan_appids()

    apps.update(appid_apps)


    save_apps(apps)
    print(f"found{len(apps)} apps.")








def save_apps(apps):
    with open(APP_FILE , "w") as file :
        json.dump(apps, file , indent=4)


def load_apps():
    try:
        with open(APP_FILE , "r") as file:

            return json.load(file)

    except( FileNotFoundError , json.JSONDecodeError):

        return{}



def launch_app(app_name):
    apps = load_apps()
    app = apps.get(app_name.strip().lower())

    if app is None:
        return f"Application '{app_name}' not found."

    try:
        if app["type"] == "lnk":
            subprocess.Popen(app["value"], shell=True)
            return f"Opening {app_name}."

        elif app["type"] == "appid":
            subprocess.Popen(
                f'explorer shell:AppsFolder\\{app["value"]}',
                shell=True
            )
            return f"Opening {app_name}."

        else:
            return f"Unknown application type for '{app_name}'."

    except (OSError, KeyError) as e:
        return f"Failed to open '{app_name}': {e}"