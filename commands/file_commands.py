from core.command import Command

from services.file_manager import (
    create_file,
    create_folder,
    delete_path,
    edit_file,
    list_directory,
    open_file,
    read_file,
    search_files,
    search_file_contents,
)


def search_command(query):
    results = search_files(query)
    if not results:
        return f"No files or folders found matching '{query}'."
    return "\n".join(
        [f"Found {len(results)} result(s):"]
        + [f"{i}. {path}" for i, path in enumerate(results, 1)]
    )


def open_command(path):
    return open_file(path)


def read_command(path, start_line=None, end_line=None):
    return read_file(path, start_line=start_line, end_line=end_line)


def create_file_command(path, content=""):
    return create_file(path, content=content)


def create_folder_command(path):
    return create_folder(path)


def list_directory_command(path="~"):
    return list_directory(path)


def edit_file_command(path, old_text, new_text, expected_hash):
    return edit_file(path, old_text, new_text, expected_hash)


def delete_command(path):
    return delete_path(path)


def search_content_command(query, path=None):
    results = search_file_contents(query, path=path)
    return "\n".join(results)



COMMANDS = [
    Command(
        name="search",
        function=search_command,
        description="Search configured directories live for files and folders by name. Does not search file contents.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Filename or folder-name text to search for."}
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    ),
    Command(
        name="readfile",
        function=read_command,
        description="Read a UTF-8 text file with line numbers and SHA256. Optional line bounds limit the output. Use the returned hash for editfile.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Full or relative path to a text file."},
                "start_line": {"type": ["integer", "null"], "description": "Optional 1-based first line."},
                "end_line": {"type": ["integer", "null"], "description": "Optional 1-based last line."},
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    ),
    Command(
        name="openfile",
        function=open_command,
        description="Open a file or folder using the operating system's default handler.",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Full or relative path to open."}},
            "required": ["path"],
            "additionalProperties": False,
        },
    ),
    Command(
        name="createfile",
        function=create_file_command,
        description="Create a new UTF-8 file without overwriting an existing file. Optional initial content is supported.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path for the new file."},
                "content": {"type": "string", "description": "Optional initial text; defaults to empty."},
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    ),
    Command(
        name="editfile",
        function=edit_file_command,
        description="Replace one exact text segment. First call readfile and pass its SHA256 as expected_hash. Refuses stale hashes or ambiguous old_text and creates a backup.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file."},
                "old_text": {"type": "string", "description": "Exact text to replace; must occur once."},
                "new_text": {"type": "string", "description": "Replacement text."},
                "expected_hash": {"type": "string", "description": "SHA256 returned by readfile for this exact file version."},
            },
            "required": ["path", "old_text", "new_text", "expected_hash"],
            "additionalProperties": False,
        },
    ),
    Command(
        name="createfolder",
        function=create_folder_command,
        description="Create a directory, including missing parent directories.",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Directory path to create."}},
            "required": ["path"],
            "additionalProperties": False,
        },
    ),
    Command(
        name="list_directory",
        function=list_directory_command,
        description="List files and subdirectories in a directory; defaults to the user's home directory.",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Directory path; defaults to '~'."}},
            "required": [],
            "additionalProperties": False,
        },
    ),
    Command(
        name="delete",
        function=delete_command,
        description="Move a file or folder to the Recycle Bin. Protected system paths are blocked.",
        permission="confirm",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path of the item to move to the Recycle Bin."}},
            "required": ["path"],
            "additionalProperties": False,
        },
    ),

    Command(
        name="search_content",
        function=search_content_command,
        description=(
            "Search inside text files for a phrase or code symbol. "
            "Returns matching file paths, line numbers, and matching lines. "
            "Use this to find where a function, variable, or phrase appears "
            "across a project. Optionally restrict the search to a file "
            "or directory."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Text or code symbol to find inside files."
                },
                "path": {
                    "type": ["string", "null"],
                    "description": (
                        "Optional file or directory to search. "
                        "If omitted, search configured directories."
                    )
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    )
]
