"""
CLI script: create tables, insert sample transactions for testing.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db import engine, Base, SessionLocal
from app.models import Document, Transaction

def seed_database(num_transactions: int = 50):
    """Create tables and insert sample data."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create sample documents
        vendors = ["Acme Corp", "Tech Solutions", "Office Supplies Co", "Utilities Inc", "Cloud Services Ltd"]
        categories = ["Software", "Hardware", "Office", "Utilities", "Services"]
        
        documents = []
        for i, vendor in enumerate(vendors):
            doc = Document(
                filename=f"sample_invoice_{i+1}.pdf",
                file_path=f"data/raw_docs/sample_invoice_{i+1}.pdf",
                document_type="invoice",
                raw_text=f"Invoice from {vendor}\nAmount: ${random.randint(500, 5000)}\nDate: {datetime.now().strftime('%Y-%m-%d')}",
                extracted_data={
                    "vendor": vendor,
                    "amount": random.randint(500, 5000),
                    "invoice_number": f"INV-{1000+i}"
                }
            )
            db.add(doc)
            documents.append(doc)
        
        db.flush()
        
        # Create sample transactions
        base_date = datetime.now() - timedelta(days=90)  # Last 3 months
        
        for i in range(num_transactions):
            vendor = random.choice(vendors)
            category = random.choice(categories)
            date = base_date + timedelta(days=random.randint(0, 90))
            
            # Some transactions linked to documents
            doc_id = documents[random.randint(0, len(documents)-1)].id if random.random() > 0.5 else None
            
            transaction = Transaction(
                document_id=doc_id,
                date=date,
                amount=round(random.uniform(50.0, 2000.0), 2),
                vendor=vendor,
                category=category,
                description=f"Payment to {vendor} for {category.lower()}",
                meta_data={"source": "sample", "generated": True}
            )
            db.add(transaction)
        
        db.commit()
        print("✓ Database seeded with sample data")
        print(f"  - Created {len(documents)} sample documents")
        print(f"  - Created {num_transactions} sample transactions")
        print(f"  - Date range: {base_date.date()} to {datetime.now().date()}")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    num_txns = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 50
    seed_database(num_transactions=num_txns)

