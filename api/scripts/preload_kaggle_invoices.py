"""
Download cankatsrc/invoices from Kaggle (tabular CSV) and seed Document + Transaction rows.

The dataset is synthetic invoice line items (no PDF/images). This bypasses OCR and fills
the DB so dashboards, analytics, and chat have data.

Prerequisites:
  pip install 'kagglehub[pandas-datasets]'  # also in api/requirements.txt
  ~/.kaggle/kaggle.json (or Kaggle env vars) and dataset rules accepted on Kaggle.

Usage (from repo root, API venv active):
  cd api && python scripts/preload_kaggle_invoices.py              # first 50 rows (default)
  cd api && python scripts/preload_kaggle_invoices.py --all       # entire CSV (~10k)
  cd api && python scripts/preload_kaggle_invoices.py --clear-kaggle  # remove prior Kaggle rows, then load default 50
  cd api && python scripts/preload_kaggle_invoices.py --amount-mode line_total
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# project root = api/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import kagglehub  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.models import Document, Transaction  # noqa: E402

DEFAULT_DATASET = "cankatsrc/invoices"
DEFAULT_CSV = "invoices.csv"
SEED_SOURCE = "kaggle_cankatsrc_invoices"


def category_from_row(row: pd.Series) -> str:
    j = row.get("job")
    if j is None or (isinstance(j, float) and pd.isna(j)):
        return "Invoice line"
    s = str(j).strip()
    if not s:
        return "Invoice line"
    return s[:60]


def vendor_from_row(row: pd.Series) -> str:
    email = row.get("email")
    if email is not None and not (isinstance(email, float) and pd.isna(email)):
        e = str(email).strip()
        if e:
            return e
    name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
    return name if name else "Unknown"


def parse_invoice_date(val) -> datetime:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return datetime.utcnow()
    s = str(val).strip()
    if not s:
        return datetime.utcnow()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime.utcnow()


def row_amount(row: pd.Series, amount_mode: str) -> float:
    qty = float(row.get("qty") or 0) or 1.0
    amt = float(row.get("amount") or 0)
    if amount_mode == "unit":
        return round(qty * amt, 2)
    return round(amt, 2)


def build_extracted_data(row: pd.Series, amount_mode: str) -> dict:
    """Shape similar to idp invoice extraction for UI/compare."""
    line_amt = row_amount(row, amount_mode)
    v = vendor_from_row(row)
    return {
        "vendor": v,
        "invoice_number": str(row.get("stock_code", "")),
        "amounts": [float(row.get("amount") or 0)],
        "dates": [str(row.get("invoice_date", ""))],
        "line_items": [
            {
                "description": str(row.get("job", "line item")),
                "quantity": int(row.get("qty") or 0),
                "amount": float(row.get("amount") or 0),
                "item_number": str(row.get("product_id", "")),
            }
        ],
        "total": line_amt,
        "meta": {
            "email": row.get("email"),
            "address": row.get("address"),
            "city": row.get("city"),
            "stock_code": row.get("stock_code"),
            "product_id": row.get("product_id"),
            "source": SEED_SOURCE,
            "seed_source": SEED_SOURCE,
            "synthetic": True,
        },
    }


def build_raw_text(row: pd.Series) -> str:
    parts = [
        f"Invoice date: {row.get('invoice_date', '')}",
        f"Customer: {row.get('first_name', '')} {row.get('last_name', '')}",
        f"Email: {row.get('email', '')}",
        f"Address: {row.get('address', '')}, {row.get('city', '')}",
        f"Product: {row.get('product_id', '')} x {row.get('qty', '')} @ {row.get('amount', '')}",
        f"Role: {row.get('job', '')}",
        f"Stock code: {row.get('stock_code', '')}",
    ]
    return "\n".join(str(p) for p in parts if p)


def clear_kaggle_documents(db) -> int:
    """Remove documents seeded from this dataset (and their transactions). Returns rows deleted."""
    prefix = f"kaggle://{DEFAULT_DATASET}"
    ids = [
        r[0]
        for r in db.query(Document.id)
        .filter(Document.file_path.like(prefix + "%"))
        .all()
    ]
    if not ids:
        return 0
    n_txn = db.query(Transaction).filter(Transaction.document_id.in_(ids)).delete(synchronize_session=False)
    n_doc = db.query(Document).filter(Document.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    print(f"Cleared prior Kaggle seed: {n_doc} documents, {n_txn} transactions.")
    return n_doc


def preload(
    *,
    csv_path: Path | None,
    max_rows: int | None,
    amount_mode: str,
    dry_run: bool,
    clear_kaggle: bool,
) -> None:
    if csv_path is None:
        print(f"Downloading {DEFAULT_DATASET} via kagglehub…")
        root = Path(kagglehub.dataset_download(DEFAULT_DATASET))
        csv_path = root / DEFAULT_CSV
        if not csv_path.is_file():
            raise FileNotFoundError(f"Expected {DEFAULT_CSV} under {root}, found: {list(root.iterdir())}")

    df = pd.read_csv(csv_path)
    if max_rows is not None:
        df = df.head(max_rows)

    print(f"Rows to import: {len(df)} from {csv_path}")

    if dry_run:
        print(df.head(3).to_string())
        return

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if clear_kaggle:
            clear_kaggle_documents(db)

        added_docs = 0
        added_txn = 0
        for idx, row in df.iterrows():
            vendor = vendor_from_row(row)
            inv_num = str(row.get("stock_code", idx))
            fname = f"kaggle_invoice_{idx:05d}_{inv_num}.synthetic"
            synthetic_path = f"kaggle://{DEFAULT_DATASET}#{idx}"

            existing = db.query(Document).filter(Document.file_path == synthetic_path).first()
            if existing:
                continue

            ed = build_extracted_data(row, amount_mode)
            amt = row_amount(row, amount_mode)
            dt = parse_invoice_date(row.get("invoice_date"))

            doc = Document(
                filename=fname,
                file_path=synthetic_path,
                document_type="invoice",
                raw_text=build_raw_text(row),
                extracted_data=ed,
            )
            db.add(doc)
            db.flush()

            cat = category_from_row(row)

            txn = Transaction(
                document_id=doc.id,
                date=dt,
                amount=amt,
                vendor=vendor[:500] if vendor else "Unknown",
                category=cat,
                description=f"Product {row.get('product_id', '')} — {row.get('job', '')}"[:2000],
                meta_data={
                    **(ed.get("meta") or {}),
                    "qty": int(row.get("qty") or 0),
                    "unit_amount": float(row.get("amount") or 0),
                    "synthetic": True,
                    "seed_source": SEED_SOURCE,
                },
            )
            db.add(txn)
            added_docs += 1
            added_txn += 1

            if added_docs > 0 and added_docs % 500 == 0:
                db.commit()
                print(f"  committed {added_docs} documents…")

        db.commit()
        print(f"Done. Added {added_docs} documents, {added_txn} transactions.")
        print("Optional: python scripts/build_embeddings.py  # index raw_text for RAG")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Preload cankatsrc/invoices CSV into DocSage DB")
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Use this invoices.csv instead of downloading via Kaggle",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=50,
        help="Import only first N rows (default: 50)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Import every row in the CSV (~10k); overrides --max-rows",
    )
    parser.add_argument(
        "--clear-kaggle",
        action="store_true",
        help="Delete existing rows seeded from this Kaggle dataset, then import",
    )
    parser.add_argument(
        "--amount-mode",
        choices=("unit", "line_total"),
        default="unit",
        help="unit: amount * qty; line_total: use amount column as full line total",
    )
    parser.add_argument("--dry-run", action="store_true", help="Only show sample rows, no DB writes")
    args = parser.parse_args()

    max_rows = None if args.all else args.max_rows

    preload(
        csv_path=args.csv,
        max_rows=max_rows,
        amount_mode=args.amount_mode,
        dry_run=args.dry_run,
        clear_kaggle=args.clear_kaggle,
    )


if __name__ == "__main__":
    main()
