from core.command import Command
from services.file_manager import (
    search_files,
    open_file,
    read_file,
    create_file,
    create_folder,
    delete_path,
    pick_and_open
)


# ---------- COMMAND FUNCTIONS ----------

def search_command(query):
    results = search_files(query)

    if not results:
        return f"No files found matching '{query}'."

    lines = [f"Found {len(results)} file(s):"]
    lines.extend(
        f"{index}. {path}"
        for index, path in enumerate(results, start=1)
    )
    return "\n".join(lines)


def open_command(path):
    return open_file(path)


def read_command(path):
    return read_file(path)


def create_file_command(path):
    return create_file(path)


def create_folder_command(path):

    return create_folder(path)


def delete_command(path):
    return delete_path(path)


# ---------- COMMAND REGISTRY ----------

COMMANDS = [

    Command(
        name="search",
        function=search_command,
        description="Search for files or folders by name.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Name or text to search for in file and folder names."
                }
            },
            "required": ["query"]
        }
    ),

    Command(
        name="openfile",
        function=open_command,
        description="Open a specific file or folder using its path.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Full path or relative path of the file or folder to open."
                }
            },
            "required": ["path"]
        }
    ),

    Command(
        name="readfile",
        function=read_command,
        description="Read and return the contents of a specific file.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Full path or relative path of the file to read."
                }
            },
            "required": ["path"]
        }
    ),

    Command(
        name="createfile",
        function=create_file_command,
        description="Create a new file at the specified path.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Full path or relative path where the new file should be created."
                }
            },
            "required": ["path"]
        }
    ),

    Command(
        name="createfolder",
        function=create_folder_command,
        description="Create a new folder at the specified path.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Full path or relative path where the new folder should be created."
                }
            },
            "required": ["path"]
        }
    ),

    Command(
        name="delete",
        function=delete_command,
        description="Delete a specified file or folder by moving it to the Recycle Bin.",
        permission="confirm",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Full path or relative path of the file or folder to delete."
                }
            },
            "required": ["path"]
        }
    ),

]