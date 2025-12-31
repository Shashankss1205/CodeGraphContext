# Core Concepts

The core of CodeGraphContext is built upon a few key components that manage the database connection, handle background tasks, and watch for file system changes.

## `DatabaseManager`

The `DatabaseManager` class in `database.py` is a thread-safe singleton responsible for managing the connection to the Neo4j database. This ensures that only one connection pool is created and shared across the application, which is crucial for performance and resource management.

### Key Methods

-   `get_driver()`: Returns the active Neo4j Driver instance, creating it if it doesn't exist.
-   `close_driver()`: Closes the Neo4j driver connection.
-   `is_connected()`: Checks if the database connection is currently active.

## `JobManager`

The `JobManager` class in `jobs.py` handles long-running, background jobs, such as code indexing. It stores job information in memory and provides a thread-safe way to create, update, and retrieve information about these jobs.

### `JobStatus`

An enumeration for the possible statuses of a background job:
- `PENDING`
- `RUNNING`
- `COMPLETED`
- `FAILED`
- `CANCELLED`

### `JobInfo`

A data class that holds all information about a single background job, including its ID, status, start/end times, progress, and any errors.

### Key Methods

-   `create_job()`: Creates a new job with a unique ID.
-   `update_job()`: Updates the information for a specific job.
-   `get_job()`: Retrieves the information for a single job.
-   `list_jobs()`: Returns a list of all jobs.
-   `cleanup_old_jobs()`: Removes old, completed jobs from memory.

## `CodeWatcher`

The `CodeWatcher` class in `watcher.py` implements the live file-watching functionality using the `watchdog` library. It observes directories for changes and triggers updates to the code graph.

## FalkorDB (embedded)

FalkorDB Lite is an optional embedded backend powered by `redislite`. Note that `redislite` is not supported on Windows; to use FalkorDB on Windows, run CodeGraphContext inside WSL or on Linux. Install the optional Falkor backend with `pip install codegraphcontext[falkor]`.

### `RepositoryEventHandler`

A dedicated event handler for a single repository. It performs an initial scan and then uses a debouncing mechanism to efficiently handle file changes, creations, or deletions.

### Key Methods

-   `watch_directory()`: Schedules a directory to be watched for changes.
-   `unwatch_directory()`: Stops watching a directory.
-   `list_watched_paths()`: Returns a list of all currently watched directory paths.
-   `start()`: Starts the observer thread.
-   `stop()`: Stops the observer thread gracefully.