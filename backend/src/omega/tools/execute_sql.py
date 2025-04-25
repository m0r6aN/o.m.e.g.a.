# tools/research/execute_sql.py
import sqlite3
from typing import Dict, Any

def execute_sql_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    sql = input_data.get("sql", "")
    try:
        conn = sqlite3.connect("database.db")
        rows = conn.execute(sql).fetchall()
        result = [dict(zip([col[0] for col in conn.execute(sql).description], row)) for row in rows]
        return {"rows": result}
    except Exception as e:
        return {"error": str(e)}
