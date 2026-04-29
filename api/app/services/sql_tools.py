"""
Safe SQL query helpers for the agent.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from app.db import SessionLocal

class SQLTools:
    """Helper class for generating and executing safe SQL queries."""
    
    @staticmethod
    def get_table_schema(table_name: str) -> Dict[str, Any]:
        """Get schema information for a table."""
        from app.config import settings
        
        with SessionLocal() as db:
            # SQLite uses different schema queries
            if settings.USE_SQLITE:
                result = db.execute(text(f"""
                    SELECT name, type 
                    FROM pragma_table_info('{table_name}')
                """))
                return {row[0]: row[1] for row in result}
            else:
                # PostgreSQL
                result = db.execute(text(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                """))
                return {row[0]: row[1] for row in result}
    
    @staticmethod
    def execute_query(query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Execute a SQL query safely with a limit.
        
        Args:
            query: SQL query string
            limit: Maximum number of rows to return
        
        Returns:
            List of dictionaries representing rows
        """
        # Add safety checks
        query_lower = query.lower().strip()
        
        # Prevent dangerous operations
        dangerous_keywords = ["drop", "delete", "truncate", "alter", "create", "insert", "update"]
        if any(keyword in query_lower for keyword in dangerous_keywords):
            raise ValueError(f"Query contains dangerous keyword. Only SELECT queries are allowed.")
        
        # Ensure it's a SELECT query
        if not query_lower.startswith("select"):
            raise ValueError("Only SELECT queries are allowed.")
        
        # Add limit if not present
        if "limit" not in query_lower:
            query = f"{query.rstrip(';')} LIMIT {limit}"
        
        with SessionLocal() as db:
            result = db.execute(text(query))
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
    
    @staticmethod
    def get_sample_data(table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample data from a table."""
        return SQLTools.execute_query(f"SELECT * FROM {table_name}", limit=limit)

