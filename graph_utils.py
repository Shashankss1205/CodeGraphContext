from neo4j import GraphDatabase

class GraphUtils:
    def _init_(self, uri: str, user: str, password: str):
        self._uri = uri
        self._user = user
        self._password = password
        self._driver = None
        self._session = None

    def connect(self):
        """Establish a connection to the Neo4j database."""
        self._driver = GraphDatabase.driver(self._uri, auth=(self._user, self._password))
        self._session = self._driver.session()

    def close(self):
        """Close the connection to the Neo4j database."""
        if self._session:
            self._session.close()
        if self._driver:
            self._driver.close()

    def add_node(self, label: str, properties: dict):
        """Add a node to the graph."""
        query = f"CREATE (n:{label} {properties})"
        self._session.run(query)

    def add_relationship(self, node1_label: str, node1_id: str, rel_type: str, node2_label: str, node2_id: str):
        """Create a relationship between two nodes."""
        query = f"""
        MATCH (a:{node1_label} {{id: '{node1_id}'}}), (b:{node2_label} {{id: '{node2_id}'}})
        CREATE (a)-[:{rel_type}]->(b)
        """
        self._session.run(query)

    def query_node(self, label: str, properties: dict):
        """Query nodes based on properties."""
        query = f"MATCH (n:{label} {properties}) RETURN n"
        result = self._session.run(query)
        return [record["n"] for record in result]

    def update_node(self, label: str, node_id: str, properties: dict):
        """Update properties of a node."""
        set_clause = ", ".join([f"n.{key} = '{value}'" for key, value in properties.items()])
        query = f"""
        MATCH (n:{label} {{id: '{node_id}'}})
        SET {set_clause}
        """
        self._session.run(query)

    def delete_node(self, label: str, node_id: str):
        """Delete a node and its relationships."""
        query = f"""
        MATCH (n:{label} {{id: '{node_id}'}})
        DETACH DELETE n
        """
        self._session.run(query)
