from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


PROJECT_ROOT = Path(r"F:\AI_Electrical_BIM")
SETTINGS_FILE = PROJECT_ROOT / "knowledge-engine" / "config" / "settings.json"

def load_settings() -> dict:
    return json.loads(SETTINGS_FILE.read_text(encoding="utf-8-sig"))

SETTINGS = load_settings()

LIBRARY_ROOT = Path(SETTINGS["library_path"])
PROCESSED_ROOT = Path(SETTINGS["processed_path"])
ENGINE = PROJECT_ROOT / "knowledge-engine"
STUDY_ENGINE = ENGINE / "app" / "study_engine.py"
LOG_ROOT = ENGINE / "logs"

SUPPORTED_EXTENSIONS = {
    str(ext).lower()
    for ext in SETTINGS.get(
        "supported_extensions",
        [".pdf", ".docx", ".pptx", ".xlsx", ".txt", ".md"],
    )
}

EXCLUDED_ROOTS = {"09_processed", "10_metadata"}

DEBOUNCE_SECONDS = 2.0
FILE_STABLE_CHECK_SECONDS = 0.5
FILE_STABLE_TIMEOUT_SECONDS = 120.0


def log(message: str) -> None:
    print(message, flush=True)


def is_source_file(path: Path) -> bool:
    try:
        if not path.is_file():
            return False

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return False

        relative = path.resolve().relative_to(LIBRARY_ROOT.resolve())
        if not relative.parts:
            return False
        if relative.parts[0].lower() in EXCLUDED_ROOTS:
            return False
        return True
    except (OSError, ValueError):
        return False

def get_manifest(source: Path) -> Path:
    return (
        PROCESSED_ROOT
        / source.stem
        / f"{source.stem}.manifest.json"
    )


def is_processed(source: Path) -> bool:
    manifest = get_manifest(source)

    if not manifest.exists():
        return False

    try:
        return manifest.stat().st_mtime_ns >= source.stat().st_mtime_ns
    except OSError:
        return False


def discover_books() -> list[Path]:
    return sorted(
        (
            path
            for path in LIBRARY_ROOT.rglob("*")
            if is_source_file(path)
        ),
        key=lambda p: str(p).lower(),
    )

def wait_until_file_is_stable(book: Path) -> bool:
    deadline = time.monotonic() + FILE_STABLE_TIMEOUT_SECONDS
    previous_state = None

    while time.monotonic() < deadline:
        try:
            stat = book.stat()
            current_state = (stat.st_size, stat.st_mtime_ns)

            if (
                previous_state == current_state
                and stat.st_size > 0
            ):
                return True

            previous_state = current_state

        except OSError:
            pass

        time.sleep(FILE_STABLE_CHECK_SECONDS)

    try:
        return book.exists() and book.is_file() and book.stat().st_size > 0
    except OSError:
        return False


def process_book(book: Path) -> int:
    if not book.exists() or not is_source_file(book):
        return 0

    log("")
    log("=" * 70)
    log(f"[BOOK] {book.name}")
    log("=" * 70)

    if is_processed(book):
        log("[SKIP] Already processed and up to date.")
        return 0

    if not wait_until_file_is_stable(book):
        log("[FAILED] File did not become stable in time.")
        return 1

    log("[START] Study Engine")
    log(f"[SOURCE] {book}")

    result = subprocess.run(
        [
            sys.executable,
            str(STUDY_ENGINE),
            str(book),
        ],
        check=False,
    )

    if result.returncode == 0:
        log(f"[DONE] {book.name}")
    else:
        log(
            f"[FAILED] Study Engine returned code "
            f"{result.returncode}"
        )

    return result.returncode


def scan_once() -> None:
    books = discover_books()

    if not books:
        log("[INFO] No PDF/DOCX books found.")
        return

    pending = [
        book for book in books
        if not is_processed(book)
    ]

    if not pending:
        log("[OK] Library is up to date.")
        return

    log(f"[INFO] Pending books: {len(pending)}")

    for book in pending:
        process_book(book)


class LibraryEventHandler(FileSystemEventHandler):

    def __init__(self, schedule_change):
        super().__init__()
        self.schedule_change = schedule_change

    def check_path(self, raw_path: str) -> None:
        path = Path(raw_path)

        if is_source_file(path):
            self.schedule_change(path)

    def on_created(self, event):
        if not event.is_directory:
            self.check_path(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.check_path(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.check_path(event.dest_path)


class LibraryWatcher:

    def __init__(self):
        self.event_queue = queue.Queue()
        self.timers = {}
        self.lock = threading.Lock()

        self.observer = Observer()

        self.worker = threading.Thread(
            target=self.worker_loop,
            name="LibraryProcessor",
            daemon=True,
        )

    def schedule_change(self, book: Path) -> None:
        with self.lock:
            existing_timer = self.timers.get(book)

            if existing_timer is not None:
                existing_timer.cancel()

            timer = threading.Timer(
                DEBOUNCE_SECONDS,
                self.enqueue,
                args=(book,),
            )

            timer.daemon = True
            self.timers[book] = timer
            timer.start()

    def enqueue(self, book: Path) -> None:
        with self.lock:
            self.timers.pop(book, None)

        self.event_queue.put(book)

    def worker_loop(self) -> None:
        while True:
            book = self.event_queue.get()

            try:
                if book is None:
                    return

                process_book(book)

            finally:
                self.event_queue.task_done()

    def start(self) -> None:
        handler = LibraryEventHandler(self.schedule_change)

        self.observer.schedule(
            handler,
            str(LIBRARY_ROOT),
            recursive=False,
        )

        self.worker.start()
        self.observer.start()

    def stop(self) -> None:
        self.observer.stop()
        self.observer.join()

        with self.lock:
            timers = list(self.timers.values())
            self.timers.clear()

        for timer in timers:
            timer.cancel()

        self.event_queue.put(None)
        self.worker.join()


def watch() -> None:
    log("=" * 70)
    log("AI Electrical BIM - Library Manager")
    log("EVENT-DRIVEN WATCH MODE")
    log("=" * 70)
    log(f"Watching: {LIBRARY_ROOT}")
    log("Watching PDF/DOCX create, modify, and move events.")
    log("No periodic full-library scan.")
    log("")

    # One startup scan only.
    scan_once()

    watcher = LibraryWatcher()
    watcher.start()

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        log("")
        log("[STOP] Watch mode stopped by user.")

    finally:
        watcher.stop()


def main() -> int:

    if not LIBRARY_ROOT.exists():
        print(f"[ERROR] Library not found: {LIBRARY_ROOT}")
        return 1

    if not STUDY_ENGINE.exists():
        print(f"[ERROR] Study Engine not found: {STUDY_ENGINE}")
        return 1

    PROCESSED_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    LOG_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    if len(sys.argv) > 1 and sys.argv[1].lower() == "--watch":
        watch()
        return 0

    log("=" * 70)
    log("AI Electrical BIM - Library Manager")
    log("ONE-TIME SCAN")
    log("=" * 70)

    scan_once()

    log("=" * 70)
    log("SCAN COMPLETE")
    log("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
