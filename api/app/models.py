"""
SQLAlchemy models for Documents, Transactions, etc.
"""
from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # nullable for OAuth-only accounts
    name = Column(String, nullable=True)
    oauth_provider = Column(String, nullable=True)  # "google" or null
    oauth_sub = Column(String, nullable=True)  # provider subject id
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=True)
    filename = Column(String, index=True)
    file_path = Column(String)
    document_type = Column(String)
    raw_text = Column(Text)
    extracted_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=True)
    document_id = Column(Integer, index=True)
    date = Column(DateTime)
    amount = Column(Float)
    vendor = Column(String, index=True)
    category = Column(String, index=True)
    description = Column(Text)
    meta_data = Column("metadata", JSON)
    confidence_score = Column(Float, nullable=True)
    is_corrected = Column(Integer, default=0, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DocumentCorrection(Base):
    """Track user corrections to extracted data."""
    __tablename__ = "document_corrections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=True)
    document_id = Column(Integer, index=True)
    field_name = Column(String)
    original_value = Column(Text)
    corrected_value = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    title = Column(String, default="New conversation")
    messages = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

