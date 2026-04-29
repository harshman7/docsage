"""
Tool definitions for the insight agent.
These tools are used by the LLM to interact with the system.
"""
from typing import List, Dict, Any, Optional
import json
from app.services.sql_tools import SQLTools
from app.services.insights import InsightsService
from app.services.rag import RAGService

class Tool:
    """Simple tool class for agent use."""
    def __init__(self, name: str, description: str, func):
        self.name = name
        self.description = description
        self.func = func
    
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

def create_sql_query_tool() -> Tool:
    """Create a tool for executing SQL queries."""
    def execute_sql(query: str) -> str:
        """Execute a SQL SELECT query safely."""
        try:
            results = SQLTools.execute_query(query)
            return json.dumps(results, default=str)
        except Exception as e:
            return f"Error: {str(e)}"
    
    return Tool(
        name="sql_query",
        description="Execute a SQL SELECT query on the database. Use this to query transactions, documents, or other tables. Input should be a valid SQL SELECT statement. Example: 'SELECT * FROM transactions WHERE amount > 1000 LIMIT 10'",
        func=execute_sql
    )

def create_metrics_tool() -> Tool:
    """Create a tool for getting precomputed metrics."""
    def get_metrics(metric_type: str, **kwargs) -> str:
        """Get metrics based on type."""
        try:
            if metric_type == "vendor_stats":
                limit = kwargs.get("limit", 10)
                return json.dumps(InsightsService.get_vendor_stats(limit=limit), default=str)
            elif metric_type == "category_breakdown":
                return json.dumps(InsightsService.get_category_breakdown(), default=str)
            elif metric_type == "monthly_spend":
                year = kwargs.get("year")
                month = kwargs.get("month")
                if year and month:
                    return json.dumps(InsightsService.get_monthly_spend(year, month), default=str)
                else:
                    return "Error: monthly_spend requires 'year' and 'month' parameters"
            else:
                return f"Unknown metric type: {metric_type}. Available: vendor_stats, category_breakdown, monthly_spend"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def metrics_wrapper(input_str: str) -> str:
        """Wrapper to handle different input formats for metrics tool."""
        try:
            if isinstance(input_str, str):
                # Try to parse as JSON first
                try:
                    params = json.loads(input_str)
                    return get_metrics(**params)
                except json.JSONDecodeError:
                    # If not JSON, treat as metric_type string
                    return get_metrics(metric_type=input_str)
            else:
                return get_metrics(metric_type=str(input_str))
        except Exception as e:
            return f"Error: {str(e)}"
    
    return Tool(
        name="get_metrics",
        description="Get precomputed metrics and insights. Available types: 'vendor_stats' (returns top vendors by spend), 'category_breakdown' (spending by category), 'monthly_spend' (requires year and month parameters). Input should be JSON with 'metric_type' and optional parameters, or just a metric_type string.",
        func=metrics_wrapper
    )

def create_rag_tool(rag_service: RAGService) -> Tool:
    """Create a tool for RAG document search."""
    def search_documents(query: str, k: int = 5) -> str:
        """Search for relevant documents using RAG."""
        try:
            results = rag_service.search(query, k=k)
            # Format results for the LLM
            formatted = []
            for r in results:
                doc = r.get("document", {})
                formatted.append({
                    "filename": doc.get("filename", "unknown"),
                    "document_type": doc.get("document_type", "unknown"),
                    "text_snippet": doc.get("text", "")[:500],  # First 500 chars
                    "score": r.get("score", 0)
                })
            return json.dumps(formatted, default=str)
        except Exception as e:
            return f"Error: {str(e)}"
    
    return Tool(
        name="search_documents",
        description="Search for relevant documents using semantic search. Use this to find supporting documents or context for answers. Input should be a search query string.",
        func=search_documents
    )

def get_all_tools(rag_service: Optional[RAGService] = None) -> List[Tool]:
    """Get all available tools for the agent."""
    tools = [
        create_sql_query_tool(),
        create_metrics_tool(),
    ]
    
    if rag_service:
        tools.append(create_rag_tool(rag_service))
    
    return tools

