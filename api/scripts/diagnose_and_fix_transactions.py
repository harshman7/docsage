"""
Diagnostic and fix script: Check transactions and re-extract from documents if needed.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db import SessionLocal
from app.models import Document, Transaction
from scripts.ingest_docs import extract_transactions_from_document, parse_date
from datetime import datetime

def diagnose_transactions():
    """Check current state of transactions in database."""
    db = SessionLocal()
    try:
        # Count documents and transactions
        doc_count = db.query(Document).count()
        txn_count = db.query(Transaction).count()
        
        # Count documents by type
        doc_types = {}
        for doc in db.query(Document).all():
            doc_type = doc.document_type or "unknown"
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        # Count transactions by vendor
        vendor_counts = {}
        for txn in db.query(Transaction).all():
            vendor = txn.vendor or "Unknown"
            vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1
        
        # Documents without transactions
        docs_without_txns = []
        for doc in db.query(Document).all():
            txn_count_for_doc = db.query(Transaction).filter(
                Transaction.document_id == doc.id
            ).count()
            if txn_count_for_doc == 0:
                docs_without_txns.append(doc)
        
        print("=" * 60)
        print("DIAGNOSTIC REPORT")
        print("=" * 60)
        print(f"\n📄 Documents: {doc_count}")
        print(f"   Types: {dict(doc_types)}")
        print(f"\n💰 Transactions: {txn_count}")
        
        if vendor_counts:
            print(f"   Top vendors: {dict(list(vendor_counts.items())[:5])}")
        
        print(f"\n⚠️  Documents without transactions: {len(docs_without_txns)}")
        
        if docs_without_txns:
            print("\n   Documents missing transactions:")
            for doc in docs_without_txns[:10]:  # Show first 10
                print(f"     - {doc.filename} ({doc.document_type})")
            if len(docs_without_txns) > 10:
                print(f"     ... and {len(docs_without_txns) - 10} more")
        
        print("\n" + "=" * 60)
        
        return {
            "doc_count": doc_count,
            "txn_count": txn_count,
            "docs_without_txns": docs_without_txns,
            "doc_types": doc_types
        }
    finally:
        db.close()

def check_extraction_quality(doc: Document):
    """Check what data was extracted from a document."""
    extracted = doc.extracted_data or {}
    
    print(f"\n📋 Document: {doc.filename}")
    print(f"   Type: {doc.document_type}")
    print(f"   Extracted fields:")
    
    if extracted:
        if "vendor" in extracted:
            print(f"     ✓ Vendor: {extracted.get('vendor')}")
        if "total" in extracted:
            print(f"     ✓ Total: ${extracted.get('total')}")
        if "amounts" in extracted:
            amounts = extracted.get("amounts", [])
            print(f"     ✓ Amounts found: {len(amounts)}")
            if amounts:
                print(f"       {amounts[:5]}")  # Show first 5
        if "dates" in extracted:
            dates = extracted.get("dates", [])
            print(f"     ✓ Dates found: {len(dates)}")
            if dates:
                print(f"       {dates[:3]}")  # Show first 3
        if "invoice_number" in extracted:
            print(f"     ✓ Invoice #: {extracted.get('invoice_number')}")
    else:
        print("     ⚠️  No extracted data found")
    
    # Check if transactions exist
    db = SessionLocal()
    try:
        txn_count = db.query(Transaction).filter(
            Transaction.document_id == doc.id
        ).count()
        print(f"   Transactions in DB: {txn_count}")
    finally:
        db.close()

def fix_missing_transactions(dry_run: bool = False):
    """Re-process documents to extract missing transactions."""
    db = SessionLocal()
    try:
        # Find documents without transactions
        all_docs = db.query(Document).all()
        docs_to_fix = []
        
        for doc in all_docs:
            txn_count = db.query(Transaction).filter(
                Transaction.document_id == doc.id
            ).count()
            if txn_count == 0:
                docs_to_fix.append(doc)
        
        if not docs_to_fix:
            print("✅ All documents already have transactions!")
            return
        
        print(f"\n🔧 Found {len(docs_to_fix)} documents without transactions")
        
        if dry_run:
            print("🔍 DRY RUN MODE - No changes will be made\n")
        
        fixed_count = 0
        skipped_count = 0
        
        for doc in docs_to_fix:
            print(f"\nProcessing: {doc.filename} ({doc.document_type})")
            
            # Check extracted data
            extracted_data = doc.extracted_data or {}
            
            if not extracted_data:
                print("  ⚠️  No extracted data - skipping")
                skipped_count += 1
                continue
            
            # Try to extract transactions
            transactions = extract_transactions_from_document(doc, extracted_data)
            
            if not transactions:
                print("  ⚠️  Could not extract transactions from data")
                print(f"     Extracted data keys: {list(extracted_data.keys())}")
                
                # Show what we have
                if "total" in extracted_data:
                    print(f"     Total found: {extracted_data['total']}")
                if "amounts" in extracted_data:
                    print(f"     Amounts found: {extracted_data['amounts']}")
                
                skipped_count += 1
                continue
            
            if dry_run:
                print(f"  ✓ Would create {len(transactions)} transaction(s)")
                for txn in transactions:
                    print(f"     - {txn.get('vendor')}: ${txn.get('amount')}")
            else:
                # Create transactions
                for txn_data in transactions:
                    # Check if transaction already exists (by document_id and amount)
                    existing = db.query(Transaction).filter(
                        Transaction.document_id == doc.id,
                        Transaction.amount == txn_data.get("amount")
                    ).first()
                    
                    if not existing:
                        txn = Transaction(**txn_data)
                        db.add(txn)
                
                db.commit()
                print(f"  ✓ Created {len(transactions)} transaction(s)")
                fixed_count += 1
        
        print("\n" + "=" * 60)
        if dry_run:
            print(f"🔍 DRY RUN COMPLETE")
            print(f"   Would fix: {fixed_count} documents")
            print(f"   Would skip: {skipped_count} documents")
        else:
            print(f"✅ FIX COMPLETE")
            print(f"   Fixed: {fixed_count} documents")
            print(f"   Skipped: {skipped_count} documents")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {str(e)}")
        raise
    finally:
        db.close()

def improve_extraction_for_doc(doc: Document, debug: bool = False):
    """Try to improve extraction for a single document."""
    from app.services.idp_pipeline import parse_document, extract_amounts
    
    print(f"\n🔄 Re-processing: {doc.filename}")
    
    # Re-parse the document with improved extraction
    extracted_data = parse_document(doc.file_path)
    
    # Update document with new extracted data
    db = SessionLocal()
    try:
        new_extracted = extracted_data.get("extracted_data", {})
        raw_text = extracted_data.get("raw_text", "")
        doc.extracted_data = new_extracted
        doc.raw_text = raw_text
        db.commit()
        
        # Debug: Show OCR text sample if requested
        if debug:
            print(f"  🔍 OCR Text sample (first 1000 chars):")
            print(f"     {raw_text[:1000]}")
            print(f"\n  🔍 Amounts found in text:")
            amounts_found = extract_amounts(raw_text)
            print(f"     {amounts_found[:10]}")  # Show first 10
        
        # Show what was extracted
        print("  📊 Extracted data:")
        if new_extracted.get("vendor"):
            print(f"     Vendor: {new_extracted.get('vendor')}")
        if new_extracted.get("total"):
            print(f"     Total: ${new_extracted.get('total')}")
        amounts_list = new_extracted.get("amounts", [])
        if amounts_list:
            print(f"     Amounts: {len(amounts_list)} found")
            print(f"       Top amounts: {amounts_list[:5]}")
        else:
            print(f"     ⚠️  No amounts found!")
        if new_extracted.get("invoice_number"):
            print(f"     Invoice #: {new_extracted.get('invoice_number')}")
        
        # Try to extract transactions
        transactions = extract_transactions_from_document(doc, new_extracted)
        if transactions:
            # Delete old transactions for this doc
            db.query(Transaction).filter(
                Transaction.document_id == doc.id
            ).delete()
            
            # Add new transactions
            for txn_data in transactions:
                txn = Transaction(**txn_data)
                db.add(txn)
            
            db.commit()
            print(f"  ✓ Created {len(transactions)} transaction(s)")
            for txn in transactions:
                print(f"     - {txn.get('vendor')}: ${txn.get('amount')}")
        else:
            print("  ⚠️  Still no transactions extracted")
            print(f"     Check: vendor={new_extracted.get('vendor')}, total={new_extracted.get('total')}")
            if not amounts_list:
                print(f"     ⚠️  No amounts were extracted from OCR text!")
    except Exception as e:
        db.rollback()
        print(f"  ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Diagnose and fix transaction extraction issues"
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Run diagnostic report only"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Fix missing transactions"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes"
    )
    parser.add_argument(
        "--check-doc",
        type=int,
        help="Check extraction quality for a specific document ID"
    )
    parser.add_argument(
        "--improve-doc",
        type=int,
        help="Re-process and improve extraction for a specific document ID"
    )
    parser.add_argument(
        "--improve-all",
        action="store_true",
        help="Re-process all documents to improve extraction"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show debug information (OCR text, extracted amounts)"
    )
    
    args = parser.parse_args()
    
    # Run diagnostic
    if args.diagnose or not any([args.fix, args.check_doc, args.improve_doc, args.improve_all]):
        results = diagnose_transactions()
        
        # Show sample extraction quality
        if args.check_doc:
            db = SessionLocal()
            try:
                doc = db.query(Document).filter(Document.id == args.check_doc).first()
                if doc:
                    check_extraction_quality(doc)
                else:
                    print(f"Document ID {args.check_doc} not found")
            finally:
                db.close()
        elif results["docs_without_txns"]:
            print("\n📊 Sample extraction quality check:")
            for doc in results["docs_without_txns"][:3]:
                check_extraction_quality(doc)
    
    # Fix missing transactions
    if args.fix:
        fix_missing_transactions(dry_run=args.dry_run)
    
    # Improve specific document
    if args.improve_doc:
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == args.improve_doc).first()
            if doc:
                improve_extraction_for_doc(doc, debug=args.debug)
            else:
                print(f"Document ID {args.improve_doc} not found")
        finally:
            db.close()
    
    # Improve all documents
    if args.improve_all:
        db = SessionLocal()
        try:
            all_docs = db.query(Document).all()
            print(f"Re-processing {len(all_docs)} documents...")
            for doc in all_docs:
                improve_extraction_for_doc(doc, debug=args.debug)
        finally:
            db.close()

if __name__ == "__main__":
    main()

