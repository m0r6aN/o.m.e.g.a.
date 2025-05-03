# tools/execute_sql/tool.py
import sqlite3
from typing import Dict, Any
from omega.core.registerable_mcp_tool import RegisterableMCPTool

def execute_sql_query(sql: str) -> str:
    """Execute an SQL query and return the results as formatted text"""
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(sql)
        
        # Get column names
        columns = [description[0] for description in cursor.description] if cursor.description else []
        
        # Fetch all rows
        rows = cursor.fetchall()
        
        # Format the results as a string
        if not rows:
            return "Query executed successfully. No rows returned."
        
        result = "Results:\n"
        result += " | ".join(columns) + "\n"
        result += "-" * (sum(len(col) for col in columns) + 3 * (len(columns) - 1)) + "\n"
        
        for row in rows:
            result += " | ".join(str(value) for value in row) + "\n"
        
        return result
    except Exception as e:
        return f"Error executing SQL query: {str(e)}"

# Create the tool
tool = RegisterableMCPTool(
    tool_id="execute_sql",
    name="SQL Query Executor",
    description="Executes SQL queries against a database and returns the results",
    version="1.0.0",
    tags=["database", "sql", "query"]
)

# Add the SQL execution function
tool.add_tool(
    name="execute_sql",
    description="Execute an SQL query against the database",
    func=execute_sql_query,
    parameters={
        "sql": {
            "type": "string", 
            "description": "SQL query to execute"
        }
    }
)

# Run the tool server
if __name__ == "__main__":
    tool.run()