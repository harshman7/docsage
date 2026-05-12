"""
Database migration script to add new columns and tables.
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from app.db import engine, Base
from app.models import Document, Transaction, DocumentCorrection, User, ChatSession


def _has_column(inspector, table: str, column: str) -> bool:
    try:
        columns = inspector.get_columns(table)
        return column in [c["name"] for c in columns]
    except Exception:
        return False


def _table_exists(inspector, table: str) -> bool:
    return table in inspector.get_table_names()


def migrate_database():
    """Run database migrations."""
    print("Running database migrations...")

    inspector = inspect(engine)

    with engine.connect() as conn:
        # --- Transactions: legacy columns ---
        if _has_column(inspector, "transactions", "id"):
            txn_cols = [c["name"] for c in inspector.get_columns("transactions")]
            if "confidence_score" not in txn_cols:
                print("  Adding confidence_score to transactions")
                conn.execute(text("ALTER TABLE transactions ADD COLUMN confidence_score REAL"))
                conn.commit()
            if "is_corrected" not in txn_cols:
                print("  Adding is_corrected to transactions")
                conn.execute(text("ALTER TABLE transactions ADD COLUMN is_corrected INTEGER DEFAULT 0"))
                conn.commit()
            if "user_id" not in txn_cols:
                print("  Adding user_id to transactions")
                conn.execute(text("ALTER TABLE transactions ADD COLUMN user_id INTEGER"))
                conn.commit()

        # --- Documents: user_id ---
        if _has_column(inspector, "documents", "id"):
            doc_cols = [c["name"] for c in inspector.get_columns("documents")]
            if "user_id" not in doc_cols:
                print("  Adding user_id to documents")
                conn.execute(text("ALTER TABLE documents ADD COLUMN user_id INTEGER"))
                conn.commit()

        # --- DocumentCorrections: user_id ---
        if _table_exists(inspector, "document_corrections"):
            dc_cols = [c["name"] for c in inspector.get_columns("document_corrections")]
            if "user_id" not in dc_cols:
                print("  Adding user_id to document_corrections")
                conn.execute(text("ALTER TABLE document_corrections ADD COLUMN user_id INTEGER"))
                conn.commit()
        else:
            print("  Creating document_corrections table")
            Base.metadata.create_all(bind=engine, tables=[DocumentCorrection.__table__])

        # --- Users table ---
        if not _table_exists(inspector, "users"):
            print("  Creating users table")
            Base.metadata.create_all(bind=engine, tables=[User.__table__])

        # --- ChatSessions table ---
        if not _table_exists(inspector, "chat_sessions"):
            print("  Creating chat_sessions table")
            Base.metadata.create_all(bind=engine, tables=[ChatSession.__table__])

        # --- Indexes ---
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id)"))
            conn.commit()
        except Exception as e:
            print(f"  Index creation note: {e}")

    print("Migration complete!")


if __name__ == "__main__":
    migrate_database()

