"""
SQLAlchemy models for Documents, Transactions, etc.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.db import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_path = Column(String)
    document_type = Column(String)  # invoice, statement, form, etc.
    raw_text = Column(Text)
    extracted_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True)
    date = Column(DateTime)
    amount = Column(Float)
    vendor = Column(String, index=True)
    category = Column(String, index=True)
    description = Column(Text)
    meta_data = Column("metadata", JSON)  # DB column: "metadata", Python attr: "meta_data" to avoid SQLAlchemy conflict
    confidence_score = Column(Float, nullable=True)  # Extraction confidence (0-100)
    is_corrected = Column(Integer, default=0, nullable=True)  # 1 if user corrected, 0 otherwise
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DocumentCorrection(Base):
    """Track user corrections to extracted data."""
    __tablename__ = "document_corrections"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True)
    field_name = Column(String)  # vendor, total, invoice_number, etc.
    original_value = Column(Text)
    corrected_value = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

