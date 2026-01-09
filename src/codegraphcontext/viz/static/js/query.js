// Query execution and API communication
class QueryExecutor {
    constructor() {
        this.baseUrl = '';
    }

    async executeQuery(cypher) {
        try {
            const response = await fetch(`/api/query?cypher=${encodeURIComponent(cypher)}`);
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error);
            }

            return data;
        } catch (error) {
            console.error('Query execution failed:', error);
            throw error;
        }
    }

    async getSchema() {
        try {
            const response = await fetch('/api/schema');
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error);
            }

            return data;
        } catch (error) {
            console.error('Schema fetch failed:', error);
            throw error;
        }
    }
}

window.queryExecutor = new QueryExecutor();
