# graph_utils.py
import urllib.parse

# Dictionary to keep track of watched directories
watched_directories = set()

def visualize_graph_query(cypher_query: str, db_uri: str = "neo4j://localhost:7687") -> str:
    """
    Generates a URL to visualize the results of a Cypher query in the Neo4j Browser.
    Example output: https://browser.neo4j.io/?db=neo4j://localhost:7687&cmd=play+MATCH+(n)-[r]->(m)+RETURN+n,r,m
    """
    encoded_query = urllib.parse.quote_plus(cypher_query)
    browser_url = f"https://browser.neo4j.io/?db={urllib.parse.quote_plus(db_uri)}&cmd=play+{encoded_query}"
    return browser_url


def list_watched_paths() -> list:
    """
    Returns a list of all directories currently being watched.
    """
    return list(watched_directories)


def unwatch_directory(path: str) -> bool:
    """
    Stops watching a directory for live file changes.
    Returns True if successful, False if directory was not being watched.
    """
    if path in watched_directories:
        watched_directories.remove(path)
        return True
    return False


# Example usage (can remove before committing)
if __name__ == "__main__":
    watched_directories.update({"src", "data", "logs"})
    print("Watched Paths:", list_watched_paths())
    print("Unwatch 'data':", unwatch_directory("data"))
    print("Watched after unwatch:", list_watched_paths())
    print("Neo4j URL:", visualize_graph_query("MATCH (n)-[r]->(m) RETURN n,r,m"))
