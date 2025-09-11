# src/codegraphcontext/core/watcher.py
import logging
import threading
from pathlib import Path
import typing
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

if typing.TYPE_CHECKING:
    from codegraphcontext.tools.graph_builder import GraphBuilder
    from codegraphcontext.core.jobs import JobManager

logger = logging.getLogger(__name__)


# --- NEW, MORE POWERFUL EVENT HANDLER ---
class RepositoryEventHandler(FileSystemEventHandler):
    """
    An event handler that manages the state for a single repository.
    It performs an initial scan and uses cached data for efficient updates.
    """
    def __init__(self, graph_builder: "GraphBuilder", repo_path: Path, debounce_interval=2.0):
        super().__init__()
        self.graph_builder = graph_builder
        self.repo_path = repo_path
        self.debounce_interval = debounce_interval
        self.timers = {}
        
        # --- STATE CACHING ---
        self.all_file_data = []
        self.imports_map = {}
        
        # Perform the initial scan and linking when created
        self._initial_scan()

    def _initial_scan(self):
        """Scans the entire repository and builds the initial graph."""
        logger.info(f"Performing initial scan for watcher: {self.repo_path}")
        # Include both Python files and notebook files
        python_files = list(self.repo_path.rglob("*.py"))
        notebook_files = list(self.repo_path.rglob("*.ipynb"))
        all_files = python_files + notebook_files
        
        # 1. Pre-scan for the global import map
        self.imports_map = self.graph_builder._pre_scan_for_imports(all_files)
        
        # 2. Parse all files and cache their data
        for f in all_files:
            parsed_data = self.graph_builder.parse_python_file(self.repo_path, f, self.imports_map)
            if "error" not in parsed_data:
                self.all_file_data.append(parsed_data)
        
        # 3. Perform the initial linking of the entire graph
        self.graph_builder._create_all_function_calls(self.all_file_data, self.imports_map)
        logger.info(f"Initial scan and graph linking complete for: {self.repo_path}")

    def _debounce(self, event_path, action):
        """Schedules an action after a debounce interval to avoid rapid firing."""
        if event_path in self.timers:
            self.timers[event_path].cancel()
        timer = threading.Timer(self.debounce_interval, action)
        timer.start()
        self.timers[event_path] = timer

    def _handle_modification(self, event_path_str):
        """Orchestrates the complete and correct update cycle for a modified file."""
        logger.info(f"File change detected, starting full update for: {event_path_str}")
        modified_path = Path(event_path_str)

        # 1. Use the helper to update the file's nodes and get new data
        #    NOTE: You will need to modify `update_file_in_graph` to accept `repo_path`
        #    and `imports_map` as arguments and to return the new parsed data.
        new_file_data = self.graph_builder.update_file_in_graph(
            modified_path, self.repo_path, self.imports_map
        )

        if not new_file_data:
            logger.error(f"Update failed for {event_path_str}, skipping re-link.")
            return

        # 2. Update the cache
        self.all_file_data = [d for d in self.all_file_data if d.get("file_path") != event_path_str]
        if not new_file_data.get("deleted"):
            self.all_file_data.append(new_file_data)

        # 3. CRITICAL: Re-link the entire graph using the updated cache
        logger.info("Re-linking the call graph with updated information...")
        self.graph_builder._create_all_function_calls(self.all_file_data, self.imports_map)
        logger.info(f"Graph update for {event_path_str} complete! ✅")

    def _is_relevant_file(self, file_path):
        """Check if the file is a Python file or notebook file."""
        return file_path.endswith('.py') or file_path.endswith('.ipynb')

    def on_created(self, event):
        if not event.is_directory and self._is_relevant_file(event.src_path):
            self._debounce(event.src_path, lambda: self._handle_modification(event.src_path))

    def on_modified(self, event):
        if not event.is_directory and self._is_relevant_file(event.src_path):
            self._debounce(event.src_path, lambda: self._handle_modification(event.src_path))

    def on_deleted(self, event):
        if not event.is_directory and self._is_relevant_file(event.src_path):
            # Deletion is handled inside _handle_modification
            self._debounce(event.src_path, lambda: self._handle_modification(event.src_path))

    def on_moved(self, event):
        if not event.is_directory and self._is_relevant_file(event.src_path):
            # A move is a deletion from the old path and a creation at the new path
            self._debounce(event.src_path, lambda: self._handle_modification(event.src_path))
            self._debounce(event.dest_path, lambda: self._handle_modification(event.dest_path))


class CodeWatcher:
    """Manages file system watching in a background thread."""
    def __init__(self, graph_builder: "GraphBuilder", job_manager= "JobManager"):
        self.graph_builder = graph_builder
        self.observer = Observer()
        self.watched_paths = set()

    def watch_directory(self, path: str):
        path_obj = Path(path).resolve()
        path_str = str(path_obj)

        if path_str in self.watched_paths:
            logger.info(f"Path already being watched: {path_str}")
            return {"message": f"Path already being watched: {path_str}"}
        
        # --- Create a NEW, DEDICATED handler for this path ---
        event_handler = RepositoryEventHandler(self.graph_builder, path_obj)
        
        self.observer.schedule(event_handler, path_str, recursive=True)
        self.watched_paths.add(path_str)
        logger.info(f"Started watching for code changes in: {path_str}")
        
        return {"message": f"Started watching {path_str}. Initial scan is in progress."}

    def start(self):
        if not self.observer.is_alive():
            self.observer.start()
            logger.info("Code watcher observer thread started.")

    def stop(self):
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            logger.info("Code watcher observer thread stopped.")