import asyncio
import json
import sqlite3
from pathlib import Path
from fastmcp import FastMCP

DB_PATH = r"C:\TCS\GeminiStreamlit\netflixdb.sqlite"

def get_db_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    schema = {}
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [col[1] for col in cursor.fetchall()]
        schema[table] = cols
    conn.close()
    return schema

def execute_sql(query: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [d[0] for d in cursor.description] if cursor.description else []
        conn.close()
        if not rows:
            return "No results found."
        return json.dumps([dict(zip(columns, row)) for row in rows], indent=2)
    except Exception as e:
        conn.close()
        return f"SQL Error: {e}"

mcp = FastMCP("Netflix MCP Server")

@mcp.tool
async def query_netflix(query: str) -> str:
    """Query the Netflix database using natural language."""
    schema = get_db_schema()
    prompt = f"""
You are a SQLite SQL generator. Schema:
{json.dumps(schema, indent=2)}
User query: "{query}"
Convert the corresponding natural language text into SQLite compatibel query and return the result.
"""
    from subprocess import run, PIPE
    print("Converting to SQL")
    result = run(["gemini", "-p", prompt], stdout=PIPE, stderr=PIPE, text=True, shell=True)
    if result.returncode != 0:
        return f"[Gemini Error] {result.stderr.strip()}"

    sql = result.stdout.strip()
    print(sql)
    res = execute_sql(sql)
    return f"SQL:\n{sql}\n\nResult:\n{res}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
