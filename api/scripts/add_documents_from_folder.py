"""
Add documents from any folder (with option to force re-process).
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db import SessionLocal, Base, engine
from app.models import Document, Transaction
from app.services.idp_pipeline import parse_document
from scripts.ingest_docs import extract_transactions_from_document

def add_documents_from_folder(folder_path: str, force_reprocess: bool = False):
    """
    Add documents from a folder to the database.
    
    Args:
        folder_path: Path to folder containing documents
        force_reprocess: If True, re-process documents even if they exist
    """
    Base.metadata.create_all(bind=engine)
    
    data_path = Path(folder_path)
    if not data_path.exists():
        print(f"❌ Directory {folder_path} does not exist.")
        return
    
    supported_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
    files = [f for f in data_path.glob("*") 
            if f.is_file() and f.suffix.lower() in supported_extensions]
    
    if not files:
        print(f"❌ No supported files found in {folder_path}")
        print(f"Supported formats: {', '.join(supported_extensions)}")
        return
    
    print(f"📁 Found {len(files)} file(s) to process...")
    
    db = SessionLocal()
    try:
        processed = 0
        skipped = 0
        errors = 0
        
        for file_path in files:
            # Check if document already exists
            existing = db.query(Document).filter(Document.file_path == str(file_path)).first()
            
            if existing and not force_reprocess:
                print(f"  ⊘ Skipping {file_path.name} (already in database)")
                skipped += 1
                continue
            
            if existing and force_reprocess:
                print(f"  🔄 Re-processing {file_path.name}...")
                # Delete old transactions
                db.query(Transaction).filter(Transaction.document_id == existing.id).delete()
                db.delete(existing)
                db.flush()
            else:
                print(f"  📄 Processing {file_path.name}...")
            
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
                db.flush()
                
                # Extract transactions
                transactions = extract_transactions_from_document(doc, extracted_data.get("extracted_data", {}))
                for txn_data in transactions:
                    txn = Transaction(**txn_data)
                    db.add(txn)
                
                db.commit()
                processed += 1
                print(f"    ✅ Ingested {file_path.name} ({doc.document_type}) - {len(transactions)} transactions")
                
            except Exception as e:
                db.rollback()
                errors += 1
                print(f"    ❌ Error processing {file_path.name}: {str(e)}")
                continue
        
        print(f"\n✅ Ingestion complete!")
        print(f"   - Processed: {processed}")
        print(f"   - Skipped: {skipped}")
        print(f"   - Errors: {errors}")
        
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Add documents from a folder")
    parser.add_argument("folder", help="Path to folder containing documents")
    parser.add_argument("--force", action="store_true", help="Force re-process existing documents")
    args = parser.parse_args()
    
    add_documents_from_folder(args.folder, force_reprocess=args.force)

