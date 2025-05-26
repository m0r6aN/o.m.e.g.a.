# D:/Repos/o.m.e.g.a/backend/src/omega/tools/nlp_to_sql/tool.py

from omega.core.registerable_mcp_tool import RegisterableMCPTool

def nlp_to_sql(natural_language: str, schema: str = None) -> str:
    """
    Convert natural language to SQL based on the provided database schema.
    
    Args:
        natural_language: The natural language query to convert
        schema: Optional database schema information
        
    Returns:
        Generated SQL query as string
    """
    # In a real implementation, we would:
    # 1. Use an LLM call to generate SQL from the natural language and schema
    # 2. Validate the generated SQL for syntax and safety
    # 3. Return the properly formatted SQL
    
    # For now, we'll use a simple mapping for demonstration purposes
    if "first quarter" in natural_language.lower() and "2025" in natural_language:
        return "SELECT * FROM customers WHERE purchase_date >= '2025-01-01' AND purchase_date <= '2025-03-31';"
    elif "customers" in natural_language.lower() and "new york" in natural_language.lower():
        return "SELECT * FROM customers WHERE state = 'NY';"
    elif "total sales" in natural_language.lower():
        return "SELECT SUM(amount) AS total_sales FROM orders;"
    elif "top" in natural_language.lower() and "products" in natural_language.lower():
        return "SELECT product_name, COUNT(*) as count FROM orders GROUP BY product_name ORDER BY count DESC LIMIT 10;"
    else:
        # Default query if we can't match the input
        return "SELECT * FROM customers LIMIT 10;"

# Create the tool
tool = RegisterableMCPTool(
    tool_id="nlp_to_sql",
    name="Natural Language to SQL Converter",
    description="Converts natural language queries into SQL based on database schema",
    version="1.0.0",
    tags=["database", "sql", "nlp", "query-generation"]
)

# Add the NLP to SQL function
tool.add_tool(
    name="convert",
    description="Convert natural language to SQL query",
    func=nlp_to_sql,
    parameters={
        "natural_language": {
            "type": "string", 
            "description": "Natural language query to convert to SQL"
        },
        "schema": {
            "type": "string", 
            "description": "Optional database schema information",
            "required": False
        }
    }
)

# Run the tool server
if __name__ == "__main__":
    tool.run()