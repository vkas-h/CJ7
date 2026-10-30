import json
from pathlib import Path
from threading import Thread , Lock
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config.settings import config
from utils.logger import logger
# ---------------- CONFIG ----------------

SEARCH_PATHS = [
    Path(path).expanduser()
        for path in config["search_paths"]
]

INDEX_FILE = Path(config["index_file"])

IGNORE = config["ignore"]

MAX_RESULTS = config["max_result"]

# ---------------- GLOBAL ----------------

index_lock = Lock()

index = []              # list of dictionaries
path_set = set()        # fast path lookup
dirty = False           # True when RAM index has unsaved changes
is_rebuilding = False

# ---------------- UTILS ----------------

def should_ignore(path):
    p = str(path).lower()
    return any(x in p for x in IGNORE)


def make_entry(path: Path):
    return {
        "path": str(path),
        "name": path.name.lower(),
        "type": "dir" if path.is_dir() else "file"
    }

# ---------------- INDEX CORE ----------------

def add_path(path):
    global dirty

    p = Path(path)

    if should_ignore(p):
        return

    entry = make_entry(p)

    with index_lock:
        if entry["path"] not in path_set:
            index.append(entry)
            path_set.add(entry["path"])
            dirty = True


def remove_path(path):
    global dirty

    p = str(path)

    with index_lock:
        if p in path_set:
            path_set.remove(p)

            for i, item in enumerate(index):
                if item["path"] == p:
                    index.pop(i)
                    break

            dirty = True

# ---------------- BUILD ----------------

def rebuild_index():
    global index, path_set, is_rebuilding, dirty

    if is_rebuilding:
        return

    is_rebuilding = True

    logger.info("[INDEX] Rebuilding...")

    new_index = []
    new_set = set()

    for base in SEARCH_PATHS:

        if not base.exists():
            continue

        for path in base.rglob("*"):

            try:
                if should_ignore(path):
                    continue

                entry = make_entry(path)

                new_index.append(entry)
                new_set.add(entry["path"])

            except Exception:
                continue

    with index_lock:
        index = new_index
        path_set = new_set
        dirty = False


    save_index()

    is_rebuilding = False

    logger.info(f"[INDEX] Done ({len(index)} items)")

# ---------------- SAVE / LOAD ----------------

def save_index():
    try:
        with index_lock:
            index_snapshot = list(index)

        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index_snapshot, f)

        logger.info(
            f"[INDEX] Saved ({len(index_snapshot)} items)"
        )

    except Exception:
        logger.exception("[INDEX] Save failed")


def load_index():
    global index, path_set

    if not INDEX_FILE.exists():
        print("[INDEX] No index → building in background")

        Thread(
            target=rebuild_index,
            daemon=True
        ).start()

        return

    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            loaded_index = json.load(f)

        with index_lock:
            index = loaded_index
            path_set = {
                item["path"]
                for item in loaded_index
            }

        logger.info(f"[INDEX] Loaded ({len(index)} items)")

    except Exception:
        logger.warning("[INDEX] Corrupt → rebuilding in background")

        Thread(
            target=rebuild_index,
            daemon=True
        ).start()

# ---------------- SEARCH ----------------

def search_index(query):
    query = query.lower()

    with index_lock:
        current_index = list(index)

    exact = []
    starts = []
    contains = []

    for item in current_index:
        name = item["name"]
        full = item["path"].lower()

        if query == name:
            exact.append(item)

        elif name.startswith(query):
            starts.append(item)

        elif query in name:
            contains.append(item)

        elif query in full:
            contains.append(item)

    results = exact + starts + contains

    if not results:
        results = fallback_scan(query)

    return [
        r["path"]
        for r in results[:MAX_RESULTS]
    ]


# ---------------- FALLBACK ----------------

def fallback_scan(query):
    logger.info("[FALLBACK] scanning real filesystem...")

    results = []

    for base in SEARCH_PATHS:

        if not base.exists():
            continue

        try:

            for path in base.rglob("*"):

                if query in path.name.lower():

                    entry = make_entry(path)

                    results.append(entry)

                    add_path(path)

                if len(results) >= MAX_RESULTS:
                    return [
                        r["path"]
                        for r in results
                    ]

        except Exception:
            logger.exception("Fallback filesystem scan failed")
            continue

    return [
        r["path"]
        for r in results
    ]

# ---------------- WATCHER ----------------

class Handler(FileSystemEventHandler):

    def on_created(self, event):

        if event.is_directory:
            add_path(event.src_path)
        else:
            add_path(event.src_path)


    def on_deleted(self, event):

        remove_path(event.src_path)


    def on_moved(self, event):

        remove_path(event.src_path)
        add_path(event.dest_path)

# ---------------- START WATCHER ----------------

def start_watcher():

    observer = Observer()
    handler = Handler()

    for path in SEARCH_PATHS:

        try:

            if not path.exists():

                print(
                    f"[WATCHER] Skipped: {path}"
                )

                continue

            observer.schedule(
                handler,
                str(path),
                recursive=True
            )

            print(
                f"[WATCHER] Watching: {path}"
            )

        except Exception as e:

            print(
                f"[WATCHER] Failed: {e}"
            )

    observer.start()

    print("[WATCHER] Running")

    return observer

# ---------------- INITIALIZE ----------------

def initialize_indexer():

    load_index()

    # If an index already exists,
    # synchronize it in the background.
    if INDEX_FILE.exists() and not is_rebuilding:

        logger.info("[INDEX] Background sync...")

        Thread(
            target=rebuild_index,
            daemon=True
        ).start()

    observer = start_watcher()

    return observer

# ---------------- SHUTDOWN ----------------

def shutdown_indexer():

    global dirty

    if dirty:

        logger.info("[INDEX] Saving final changes...")

        save_index()

        dirty = False

    logger.info("[INDEX] Shutdown complete")