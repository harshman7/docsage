"""
Database migration script to add new columns and tables.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from app.db import engine, Base
from app.models import Document, Transaction, DocumentCorrection

def migrate_database():
    """Run database migrations."""
    print("🔄 Running database migrations...")
    
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        # Check if new columns exist
        columns = inspector.get_columns("transactions")
        existing_columns = [col["name"] for col in columns]
        
        # Add confidence_score column if it doesn't exist
        if "confidence_score" not in existing_columns:
            print("  ➕ Adding confidence_score column to transactions...")
            conn.execute(text("ALTER TABLE transactions ADD COLUMN confidence_score REAL"))
            conn.commit()
        
        # Add is_corrected column if it doesn't exist
        if "is_corrected" not in existing_columns:
            print("  ➕ Adding is_corrected column to transactions...")
            conn.execute(text("ALTER TABLE transactions ADD COLUMN is_corrected INTEGER DEFAULT 0"))
            conn.commit()
        
        # Create document_corrections table if it doesn't exist
        try:
            conn.execute(text("SELECT 1 FROM document_corrections LIMIT 1"))
            print("  ✓ document_corrections table already exists")
        except:
            print("  ➕ Creating document_corrections table...")
            Base.metadata.create_all(bind=engine, tables=[DocumentCorrection.__table__])
            conn.commit()
        
        # Add index on category if it doesn't exist
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category)"))
            conn.commit()
            print("  ✓ Index on category created")
        except Exception as e:
            print(f"  ⚠️  Could not create index: {e}")
    
    print("✅ Migration complete!")

if __name__ == "__main__":
    migrate_database()

