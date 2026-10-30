from __future__ import annotations
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from send2trash import send2trash
from config.settings import config

BLOCKED_PATHS = [Path(p).expanduser().resolve() for p in config.get("blocked_paths", [])]
SEARCH_PATHS = [Path(p).expanduser().resolve() for p in config.get("search_paths", ["~"])]
IGNORE = tuple(str(x).casefold() for x in config.get("ignore", []) if str(x).strip())
MAX_RESULTS = max(1, int(config.get("max_result", 20)))
MAX_READ_CHARS = 30000
MAX_EDIT_FILE_BYTES = 2_000_000
BACKUP_DIR = Path(config.get("data_dir", "data")) / "file_backups"


def _resolve(path):
    return Path(path).expanduser().resolve()


def _is_blocked(path):
    path = path.resolve()
    return any(path == root or root in path.parents for root in BLOCKED_PATHS)


def _is_ignored(path):
    value = str(path).casefold()
    return any(token in value for token in IGNORE)


def _hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_text(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise IsADirectoryError(f"Cannot read a folder: {path}")
    if path.stat().st_size > MAX_EDIT_FILE_BYTES:
        raise ValueError(f"File exceeds the {MAX_EDIT_FILE_BYTES:,}-byte limit: {path}")
    return path.read_text(encoding="utf-8")


def search_files(query):
    """Search configured roots live for filename/folder-name matches."""
    needle = query.strip().casefold()
    if not needle:
        return []
    results, seen = [], set()
    for root in SEARCH_PATHS:
        if not root.is_dir():
            continue
        try:
            for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
                here = Path(current)
                dirs[:] = [d for d in dirs if not _is_ignored(here / d) and not (here / d).is_symlink()]
                for name in [*dirs, *files]:
                    candidate = here / name
                    if needle not in name.casefold() or _is_ignored(candidate):
                        continue
                    try:
                        resolved = candidate.resolve()
                        key = str(resolved).casefold()
                        if key in seen:
                            continue
                        seen.add(key)
                        results.append(resolved)
                        if len(results) >= MAX_RESULTS:
                            return results
                    except OSError:
                        continue
        except OSError:
            continue
    return results


def open_file(path):
    try:
        target = _resolve(path)
        if not target.exists():
            return f"File not found: {target}"
        if os.name == "nt":
            os.startfile(str(target))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])
        return f"Opened: {target}"
    except (OSError, ValueError) as exc:
        return f"Failed to open '{path}': {exc}"


def read_file(path, start_line=None, end_line=None):
    try:
        target = _resolve(path)
        if _is_blocked(target):
            return f"Blocked: Cannot read system-protected path: {target}"
        text = _read_text(target)
        lines = text.splitlines()
        if start_line is not None and start_line < 1:
            return "Invalid start_line: use 1 or greater."
        if end_line is not None and end_line < 1:
            return "Invalid end_line: use 1 or greater."
        if start_line is not None and end_line is not None and end_line < start_line:
            return "Invalid line range: end_line must be >= start_line."
        first, last = start_line or 1, end_line or len(lines)
        selected = lines[first - 1:last]
        body = "\n".join(f"{n:>5} | {line}" for n, line in enumerate(selected, first))
        if len(body) > MAX_READ_CHARS:
            body = body[:MAX_READ_CHARS] + "\n...[truncated; request a smaller line range]"
        return (f"File: {target}\nSHA256: {_hash(text)}\nTotal lines: {len(lines)}\n"
                f"Showing lines: {first}-{min(last, len(lines))}\n---\n{body}")
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return f"Failed to read '{path}': {exc}"


def create_file(path, content=""):
    try:
        target = _resolve(path)
        if _is_blocked(target):
            return f"Blocked: Cannot create a file in a protected path: {target}"
        if target.exists():
            return f"Path already exists: {target}"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8", newline="") as handle:
            handle.write(content)
        return f"File created: {target}"
    except (OSError, ValueError) as exc:
        return f"Failed to create file '{path}': {exc}"


def create_folder(path):
    try:
        target = _resolve(path)
        if _is_blocked(target):
            return f"Blocked: Cannot create a folder in a protected path: {target}"
        if target.exists():
            return f"Folder already exists: {target}" if target.is_dir() else f"A file already exists at: {target}"
        target.mkdir(parents=True, exist_ok=False)
        return f"Folder created: {target}"
    except (OSError, ValueError) as exc:
        return f"Failed to create folder '{path}': {exc}"


def list_directory(path="~"):
    try:
        target = _resolve(path)
        if not target.is_dir():
            return f"Not a directory or path not found: {target}"
        if _is_blocked(target):
            return f"Blocked: Cannot list system-protected path: {target}"
        entries = []
        for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.casefold())):
            if not _is_ignored(item):
                entries.append(f"{'DIR ' if item.is_dir() else 'FILE'}  {item.name}")
        if not entries:
            return f"Directory is empty: {target}"
        extra = f"\n...and {len(entries)-MAX_RESULTS} more item(s)" if len(entries) > MAX_RESULTS else ""
        return f"Directory: {target}\n" + "\n".join(entries[:MAX_RESULTS]) + extra
    except (OSError, ValueError) as exc:
        return f"Failed to list directory '{path}': {exc}"


def edit_file(path, old_text, new_text, expected_hash):
    """Exact-match edit with stale-version check, backup, and atomic replacement."""
    try:
        target = _resolve(path)
        if _is_blocked(target):
            return f"Blocked: Cannot edit a system-protected path: {target}"
        if not target.exists() or not target.is_file():
            return f"File not found or not a regular file: {target}"
        if not expected_hash:
            return "Edit refused: expected_hash is required; call readfile first."
        if not old_text:
            return "Edit refused: old_text cannot be empty."
        if old_text == new_text:
            return "No changes made: old_text and new_text are identical."
        original = _read_text(target)
        actual_hash = _hash(original)
        if actual_hash.casefold() != expected_hash.strip().casefold():
            return (f"Edit refused: file changed since it was read. Current SHA256: {actual_hash}. "
                    "Read the file again and retry.")
        count = original.count(old_text)
        if count != 1:
            return f"Edit refused: old_text must match exactly once; found {count}. No changes made."
        updated = original.replace(old_text, new_text, 1)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup = BACKUP_DIR / f"{target.name}.{stamp}.bak"
        shutil.copy2(target, backup)
        fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
                handle.write(updated)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, target)
        except Exception:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise
        if target.read_text(encoding="utf-8") != updated:
            shutil.copy2(backup, target)
            return f"Verification failed; original restored. Backup: {backup}"
        return f"Edited: {target}\nOld SHA256: {actual_hash}\nNew SHA256: {_hash(updated)}\nBackup: {backup}"
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return f"Failed to edit '{path}': {exc}"


def delete_path(path):
    try:
        target = _resolve(path)
        if not target.exists():
            return f"Path not found: {target}"
        if _is_blocked(target):
            return f"Blocked: Cannot delete system-critical path: {target}"
        if target == Path(target.anchor):
            return f"Blocked: Refusing to delete filesystem root: {target}"
        send2trash(str(target))
        return f"Moved to Recycle Bin: {target}"
    except (OSError, ValueError) as exc:
        return f"Failed to delete '{path}': {exc}"
