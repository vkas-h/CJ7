# import os
# import shutil
import subprocess
from pathlib import Path
from send2trash import send2trash
from services.indexer import search_index
from config.settings import config

#--config-------------


BLOCKED_PATHS = [
    Path(p).expanduser().resolve()
    for p in config["blocked_paths"]
]

MAX_RESULTS =config["max_result"]

#-----------search file --------------



def search_files(query):
    results = search_index(query)
    return [Path(p) for p in results]


#-------open file __________

def open_file(path):
    path = Path(path).expanduser().resolve()

    if not path.exists():
        return f"File not found: {path}"

    try:
        if path.is_dir():
            subprocess.Popen(f'explorer "{path}"')
        else:
            subprocess.Popen(str(path), shell=False)

        return f"Opened: {path}"

    except OSError as e:
        return f"Failed to open '{path}': {e}"


#_________-read file-____________



def read_file(path):
    path = Path(path).expanduser().resolve()

    if not path.exists():
        return f"File not found: {path}"

    if path.is_dir():
        return f"Cannot read a folder: {path}"

    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    except (OSError, UnicodeDecodeError) as e:
        return f"Failed to read '{path}': {e}"

    

#-------------------create file -------------


def create_file(path):
    path = Path(path).expanduser().resolve()

    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            return f"File already exists: {path}"

        path.touch()
        return f"File created: {path}"
    except OSError as e:
        return f"Failed to create file '{path}': {e}"


def create_folder(path):
    path = Path(path).expanduser().resolve()

    try:
        if path.exists():
            if path.is_dir():
                return f"Folder already exists: {path}"
            return f"A file already exists at: {path}"

        path.mkdir(parents=True, exist_ok=True)
        return f"Folder created: {path}"
    except OSError as e:
        return f"Failed to create folder '{path}': {e}"



# =-----------delete file/folder --------------


def delete_path(path):
    target = Path(path).expanduser().resolve()

    if not target.exists():
        return f"Path not found: {target}"

    if is_dangerous(target):
        return f"Blocked: Cannot delete system-critical path: {target}"

    try:
        send2trash(str(target))
        return f"Moved to Recycle Bin: {target}"
    except OSError as e:
        return f"Failed to delete '{target}': {e}"

#-----------pick and open ---------------------

def pick_and_open(results):

    if not results:

        print("No files found.")
        return


    for i , path in enumerate(results):
        print(f"{i+1} .{path}")

    try:
        choice = int(input("select file number: ")) -1
        
        if 0 <= choice < len(results):
            open_file(results[choice])

        else:
            print("Invalid Choice.")

    except:
        print("invalid input.")

#--=- confirmation --------
def is_dangerous(path):
    path = path.resolve()

    for blocked in BLOCKED_PATHS:
        if path == blocked or blocked in path.parents:
            return True

    return False


#----------confirm action ------------------


def confirm_action(path):
    choice = input(f"[WARNING] Delete '{path}' ? (yes/no): ").strip().lower()
    return choice in ["yes", "y"]


