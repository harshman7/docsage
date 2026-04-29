"""
CLI script: load PDFs from data/raw_docs into DB and extract transactions.
"""
import sys
import re
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db import engine, Base, SessionLocal
from app.models import Document, Transaction
from app.services.idp_pipeline import parse_document

def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object."""
    if not date_str:
        return datetime.now()
    
    # Try common date formats
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%d/%m/%Y",
        "%B %d, %Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return datetime.now()

def extract_transactions_from_document(doc: Document, extracted_data: dict) -> list:
    """Extract transaction records from document."""
    transactions = []
    
    if not extracted_data:
        return transactions
    
    doc_type = doc.document_type.lower()
    
    if doc_type == "invoice":
        vendor = extracted_data.get("vendor")
        total = extracted_data.get("total")
        dates = extracted_data.get("dates", [])
        date = parse_date(dates[0] if dates else None)
        line_items = extracted_data.get("line_items", [])
        
        # Create transactions for each line item
        if line_items:
            for item in line_items:
                transactions.append({
                    "document_id": doc.id,
                    "date": date,
                    "amount": float(item.get("amount", 0)),
                    "vendor": vendor or "Unknown",
                    "category": "Invoice Line Item",
                    "description": f"{item.get('description', 'Item')} (Qty: {item.get('quantity', 'N/A')})",
                    "meta_data": {
                        "item_number": item.get("item_number"),
                        "invoice_number": extracted_data.get("invoice_number"),
                        **extracted_data
                    }
                })
        
        # Also add the total transaction if different from line items
        if total:
            total_from_items = sum(item.get("amount", 0) for item in line_items)
            # Only add total transaction if it's different from sum of line items
            # or if no line items were extracted
            if not line_items or abs(total - total_from_items) > 0.01:
                transactions.append({
                    "document_id": doc.id,
                    "date": date,
                    "amount": float(total),
                    "vendor": vendor or "Unknown",
                    "category": "Invoice Total",
                    "description": f"Invoice Total: {extracted_data.get('invoice_number', doc.filename)}",
                    "meta_data": extracted_data
                })
    
    elif doc_type == "statement":
        # Extract statement transactions
        amounts = extracted_data.get("amounts", [])
        dates = extracted_data.get("dates", [])
        
        # Create transactions for each amount found
        for i, amount in enumerate(amounts[:10]):  # Limit to 10 transactions per statement
            date = parse_date(dates[i] if i < len(dates) else None)
            transactions.append({
                "document_id": doc.id,
                "date": date,
                "amount": float(amount),
                "vendor": "Bank Transaction",
                "category": "Banking",
                "description": f"Transaction from {doc.filename}",
                "meta_data": extracted_data
            })
    
    return transactions

def ingest_documents(data_dir: str = "data/raw_docs", extract_transactions: bool = True):
    """Ingest documents from data directory into database."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"Directory {data_dir} does not exist. Creating it...")
        data_path.mkdir(parents=True, exist_ok=True)
        print(f"Please add PDF files to {data_dir} and run this script again.")
        return
    
    db = SessionLocal()
    try:
        # Get list of supported file extensions
        supported_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
        
        files = [f for f in data_path.glob("*") 
                if f.is_file() and f.suffix.lower() in supported_extensions]
        
        if not files:
            print(f"No supported files found in {data_dir}")
            print(f"Supported formats: {', '.join(supported_extensions)}")
            return
        
        print(f"Found {len(files)} file(s) to process...")
        
        for file_path in files:
            # Check if document already exists
            existing = db.query(Document).filter(Document.file_path == str(file_path)).first()
            if existing:
                print(f"  ⊘ Skipping {file_path.name} (already in database)")
                continue
            
            print(f"Processing {file_path.name}...")
            
            try:
                # Parse document
                extracted_data = parse_document(str(file_path))
                
                # Save to database
                doc = Document(
                    filename=extracted_data["filename"],
                    file_path=extracted_data["file_path"],
                    document_type=extracted_data.get("document_type", "unknown"),
                    raw_text=extracted_data.get("raw_text", ""),
                    extracted_data=extracted_data.get("extracted_data", {})
                )
                db.add(doc)
                db.flush()  # Get the doc.id
                
                # Extract transactions if requested
                if extract_transactions:
                    transactions = extract_transactions_from_document(doc, extracted_data.get("extracted_data", {}))
                    for txn_data in transactions:
                        txn = Transaction(**txn_data)
                        db.add(txn)
                
                db.commit()
                print(f"  ✓ Ingested {file_path.name} ({doc.document_type})")
                if extract_transactions and transactions:
                    print(f"    → Extracted {len(transactions)} transaction(s)")
            except Exception as e:
                db.rollback()
                print(f"  ✗ Error processing {file_path.name}: {str(e)}")
                continue
        
        print(f"\n✓ Ingestion complete!")
        
    finally:
        db.close()

if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data/raw_docs"
    extract_txns = "--no-transactions" not in sys.argv
    ingest_documents(data_dir, extract_transactions=extract_txns)

