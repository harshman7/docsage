"""
Pydantic schemas for API input/output validation.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class DocumentCreate(BaseModel):
    filename: str
    file_path: str
    document_type: str
    raw_text: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    document_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TransactionCreate(BaseModel):
    document_id: int
    date: datetime
    amount: float
    vendor: str
    category: Optional[str] = None
    description: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None

class TransactionResponse(BaseModel):
    id: int
    document_id: int
    date: datetime
    amount: float
    vendor: str
    category: Optional[str]
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class QueryRequest(BaseModel):
    query: str
    use_rag: bool = True
    use_sql: bool = True

class QueryResponse(BaseModel):
    answer: str
    sources: Optional[list] = None
    sql_query: Optional[str] = None
    steps: Optional[list] = None
    tool_calls: Optional[list] = None


class DashboardSummary(BaseModel):
    total_transactions: int
    total_spend: float
    avg_transaction: float
    document_count: int


class DocumentUpdateBody(BaseModel):
    extracted_data: Dict[str, Any]


class CompareBody(BaseModel):
    document_id_1: int
    document_id_2: int

