"""
OCR + parsing + extraction logic for IDP pipeline.
"""
import pytesseract
import pdfplumber
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    return text

def extract_text_with_ocr(image_path: str) -> str:
    """Extract text from image using OCR."""
    try:
        return pytesseract.image_to_string(image_path)
    except Exception as e:
        print(f"Error with OCR: {e}")
        return ""

def classify_document(text: str) -> str:
    """
    Classify document type based on text content.
    
    Returns:
        Document type: invoice, statement, form, receipt, etc.
    """
    text_lower = text.lower()
    
    # Invoice keywords
    if any(kw in text_lower for kw in ["invoice", "bill to", "amount due", "invoice number"]):
        return "invoice"
    
    # Bank statement keywords
    if any(kw in text_lower for kw in ["statement", "account balance", "transaction", "deposit", "withdrawal"]):
        return "statement"
    
    # Receipt keywords
    if any(kw in text_lower for kw in ["receipt", "thank you", "purchase", "total paid"]):
        return "receipt"
    
    # Form keywords
    if any(kw in text_lower for kw in ["form", "application", "please complete", "signature"]):
        return "form"
    
    return "unknown"

def extract_amounts(text: str) -> List[float]:
    """Extract monetary amounts from text."""
    # Handle both US format (14,367.76) and European format (14 367,76 or 14.367,76)
    # Also handle amounts with spaces as thousands separators
    
    amounts = []
    seen = set()  # Avoid duplicates
    
    # Pattern 1: US format with $ and commas: $ 14,367.76 or $14,367.76
    patterns_us = [
        r'\$\s*[\d\s,]+\.\d{2}',           # $ 14 367.76 or $ 14,367.76
        r'\$[\d,]+\.\d{2}',                # $14367.76 or $14,367.76
    ]
    
    # Pattern 2: European format with spaces and comma decimal: 14 367,76
    patterns_eu = [
        r'[\d\s]+,\d{2}',                  # 14 367,76 (space thousands, comma decimal)
        r'[\d\s]+,\d{2}',                  # 14.367,76 (dot thousands, comma decimal)
    ]
    
    # Pattern 3: US format without $: 14,367.76 or 14367.76
    patterns_plain = [
        r'[\d\s,]+\.\d{2}',                # 14 367.76 or 14,367.76 or 14367.76
        r'[\d]{3,}\.\d{2}',                  # 14367.76 (no separators, 3+ digits)
    ]
    
    # Pattern 4: With labels
    patterns_labeled = [
        r'Gross\s+worth[:\s]+[\$]?\s*([\d\s,]+[.,]\d{2})',  # Gross worth: $ 15 804,54 or 15 804.54
        r'Net\s+worth[:\s]+[\$]?\s*([\d\s,]+[.,]\d{2})',    # Net worth: $ 14 367,76
        r'Total[:\s]+[\$]?\s*([\d\s,]+[.,]\d{2})',          # Total: $ 15 804,54
        r'Amount[:\s]+[\$]?\s*([\d\s,]+[.,]\d{2})',         # Amount: $123.45
    ]
    
    all_patterns = patterns_labeled + patterns_us + patterns_eu + patterns_plain
    
    for pattern in all_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Extract the numeric part
            if match.groups():
                amount_str = match.group(1)  # Use captured group
            else:
                amount_str = match.group(0)  # Use full match
            
            # Normalize the amount string
            # Remove $ and text labels, keep numbers, spaces, commas, dots
            cleaned = re.sub(r'[^\d\s,.]', '', amount_str)
            cleaned = cleaned.strip()
            
            # Determine format and convert
            try:
                # Check if it's European format (comma as decimal)
                if ',' in cleaned and '.' in cleaned:
                    # Mixed: could be "14.367,76" (dot thousands, comma decimal)
                    # Remove dots (thousands), replace comma with dot (decimal)
                    cleaned = cleaned.replace('.', '').replace(',', '.')
                elif ',' in cleaned and cleaned.count(',') == 1:
                    # European: "14 367,76" or "14367,76"
                    # Check if comma is decimal (if there are 2 digits after)
                    parts = cleaned.split(',')
                    if len(parts) == 2 and len(parts[1]) == 2:
                        # Comma is decimal separator
                        cleaned = cleaned.replace(' ', '').replace(',', '.')
                    else:
                        # Comma might be thousands separator
                        cleaned = cleaned.replace(',', '')
                else:
                    # US format: remove spaces and commas (they're thousands separators)
                    cleaned = cleaned.replace(' ', '').replace(',', '')
                
                amount = float(cleaned)
                
                # Only add if it's a reasonable amount
                if 0.01 <= amount <= 1000000:
                    if amount not in seen:
                        amounts.append(amount)
                        seen.add(amount)
            except (ValueError, AttributeError):
                continue
    
    # Sort by amount (descending) to prioritize larger amounts
    amounts.sort(reverse=True)
    return amounts

def extract_dates(text: str) -> List[str]:
    """Extract dates from text."""
    # Common date patterns
    patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}',
        r'\d{4}-\d{2}-\d{2}',
        r'[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}',
    ]
    
    dates = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        dates.extend(matches)
    
    return dates

def extract_vendor(text: str) -> Optional[str]:
    """Extract vendor/merchant name from text."""
    lines = text.split('\n')
    
    # Skip patterns that are clearly not vendor names
    skip_patterns = [
        r'^invoice\s*no',
        r'^invoice\s*#',
        r'^date',
        r'^total',
        r'^amount',
        r'^\d+',  # Lines starting with numbers
        r'^page\s+\d+',
        r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # Dates
        r'^\$',  # Lines starting with $
        r'^qty',
        r'^description',
        r'^item',
    ]
    
    # Look for "Seller:" pattern and get the next line or same line
    for i, line in enumerate(lines[:20]):
        line = line.strip()
        # Check for "Seller:" pattern
        if re.search(r'^seller[:\s]+', line, re.IGNORECASE):
            # Try to get vendor from same line after "Seller:"
            match = re.search(r'^seller[:\s]+(.+)', line, re.IGNORECASE)
            if match:
                vendor = match.group(1).strip()
                # Clean up common suffixes
                vendor = re.sub(r'\s*(tax\s+id|address|iban).*$', '', vendor, flags=re.IGNORECASE)
                vendor = vendor.strip()
                if vendor and len(vendor) > 2:
                    return vendor
            
            # Or get from next line
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and len(next_line) > 2 and len(next_line) < 100:
                    # Check if it's not a skip pattern
                    should_skip = False
                    for pattern in skip_patterns:
                        if re.match(pattern, next_line, re.IGNORECASE):
                            should_skip = True
                            break
                    if not should_skip and re.search(r'[A-Za-z]', next_line):
                        return next_line
    
    # Fallback: Usually vendor name is in first few lines
    for line in lines[:15]:
        line = line.strip()
        # Check if line looks like a vendor name
        if len(line) > 3 and len(line) < 100:
            # Skip if matches any skip pattern
            should_skip = False
            for pattern in skip_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    should_skip = True
                    break
            
            if not should_skip:
                # Additional checks: should have letters, not just numbers/symbols
                if re.search(r'[A-Za-z]', line) and not re.match(r'^[\d\s\$\.,]+$', line):
                    # Clean up common prefixes
                    cleaned = re.sub(r'^(bill\s+to|sold\s+to|from|vendor|merchant|seller)[:\s]*', '', line, flags=re.IGNORECASE)
                    cleaned = cleaned.strip()
                    if cleaned and len(cleaned) > 3:
                        return cleaned
    
    return None

def extract_invoice_fields(text: str) -> Dict[str, Any]:
    """Extract structured fields from invoice."""
    amounts = extract_amounts(text)
    
    fields = {
        "invoice_number": None,
        "vendor": extract_vendor(text),
        "amounts": amounts,
        "dates": extract_dates(text),
        "total": None,
    }
    
    # Extract invoice number (improved patterns)
    invoice_patterns = [
        r'invoice\s*no[.:\s]*([A-Z0-9-]+)',
        r'invoice\s*#?\s*:?\s*([A-Z0-9-]+)',
        r'inv\s*#?\s*:?\s*([A-Z0-9-]+)',
        r'invoice\s+number[.:\s]*([A-Z0-9-]+)',
    ]
    for pattern in invoice_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            inv_num = match.group(1).strip()
            # Make sure it's not just "no" or too short
            if len(inv_num) > 2 and inv_num.lower() != "no":
                fields["invoice_number"] = inv_num
                break
    
    # Get total amount - try multiple strategies
    if amounts:
        # Strategy 1: Look for "Gross worth" or "Total" keyword followed by amount
        # Handle both US and European formats
        total_patterns = [
            r'gross\s+worth[:\s]+[\$]?\s*([\d\s,]+[.,]\d{2})',  # Gross worth: $ 15 804,54 or 15 804.54
            r'total[:\s]+[\$]?\s*([\d\s,]+[.,]\d{2})',          # Total: $ 15 804,54
            r'amount\s+due[:\s]+[\$]?\s*([\d\s,]+[.,]\d{2})',   # Amount due: $123.45
            r'grand\s+total[:\s]+[\$]?\s*([\d\s,]+[.,]\d{2})',  # Grand total: $123.45
        ]
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    total_str = match.group(1)
                    # Normalize: handle spaces and commas
                    if ',' in total_str and total_str.count(',') == 1:
                        # European format: "15 804,54"
                        total_str = total_str.replace(' ', '').replace(',', '.')
                    else:
                        # US format: remove spaces and commas
                        total_str = total_str.replace(' ', '').replace(',', '')
                    total = float(total_str)
                    if total in amounts:
                        fields["total"] = total
                        break
                except:
                    pass
        
        # Strategy 2: Look for amounts with $ and spaces (like "$ 15 804,54" or "$ 15 804.54")
        if not fields["total"]:
            dollar_patterns = [
                r'\$\s*([\d\s,]+[.,]\d{2})',  # $ 15 804,54 or $ 15 804.54
            ]
            for dollar_pattern in dollar_patterns:
                matches = list(re.finditer(dollar_pattern, text))
                if matches:
                    # Get the last one (usually the total)
                    last_match = matches[-1]
                    try:
                        total_str = last_match.group(1)
                        # Normalize
                        if ',' in total_str and total_str.count(',') == 1:
                            total_str = total_str.replace(' ', '').replace(',', '.')
                        else:
                            total_str = total_str.replace(' ', '').replace(',', '')
                        total = float(total_str)
                        if total in amounts:
                            fields["total"] = total
                            break
                    except:
                        pass
        
        # Strategy 3: Look for large amounts near "Total" or "Summary" keywords
        if not fields["total"]:
            large_amounts = [a for a in amounts if a >= 1000]
            if large_amounts:
                # Check if any large amount appears near "Total" or "Summary" keywords
                for amount in large_amounts:
                    # Try to find this amount in various formats near total keywords
                    # Format: "15 804,54" or "15 804.54" or "15804.54"
                    amount_str_variants = [
                        f"{amount:.2f}".replace('.', r'[.,]'),  # 15804.54 or 15804,54
                        f"{int(amount)}[\\s,]+{int((amount % 1) * 100):02d}",  # 15 804,54
                    ]
                    for variant in amount_str_variants:
                        pattern = rf'(total|summary|gross\s+worth)[^\d]*{variant}'
                        if re.search(pattern, text, re.IGNORECASE):
                            fields["total"] = amount
                            break
                    if fields["total"]:
                        break
        
        # Strategy 4: Use the largest amount (often the total)
        if not fields["total"]:
            # Prefer amounts > 1000, but fall back to largest if needed
            large_amounts = [a for a in amounts if a >= 1000]
            if large_amounts:
                fields["total"] = max(large_amounts)
            elif amounts:
                fields["total"] = max(amounts)
    
    # Extract line items if available
    line_items = extract_line_items(text, amounts)
    if line_items:
        fields["line_items"] = line_items
    
    return fields

def extract_line_items(text: str, all_amounts: List[float]) -> List[Dict[str, Any]]:
    """Extract line items from invoice with descriptions and amounts."""
    line_items = []
    
    # Find the ITEMS section and the section with Net price amounts
    items_match = re.search(r'ITEMS.*?(?:SUMMARY|TOTAL|GROSS)', text, re.DOTALL | re.IGNORECASE)
    if not items_match:
        return line_items
    
    items_section = items_match.group(0)
    all_lines = text.split('\n')
    items_lines = items_section.split('\n')
    
    # Find the "Net price" section - it's usually after the item descriptions
    # Look for amounts in the Net price column (these are the line item prices)
    net_price_amounts = []
    net_price_start_idx = None
    
    for i, line in enumerate(all_lines):
        if 'Net price' in line and net_price_start_idx is None:
            net_price_start_idx = i
            # Look for amounts in the next 20 lines (Net price column)
            for j in range(i + 1, min(i + 25, len(all_lines))):
                net_line = all_lines[j]
                # Match European format amounts: "13,76" or "2 999,00"
                matches = re.findall(r'(\d+(?:\s+\d+)*,\d{2})', net_line)
                for match in matches:
                    # Normalize: "2 999,00" -> 2999.00
                    cleaned = match.replace(' ', '').replace(',', '.')
                    try:
                        amount = float(cleaned)
                        # Filter: line item prices are usually > 1 and < 100000
                        # Exclude very small amounts (likely quantities) and very large (totals)
                        if 1.0 <= amount <= 100000.0:
                            net_price_amounts.append(amount)
                    except:
                        pass
            break
    
    # Extract item descriptions
    item_descriptions = []
    for i, line in enumerate(items_lines):
        # Check if line starts with item number
        item_match = re.match(r'^(\d+)[\.:\)]\s*(.+)', line.strip())
        if item_match:
            item_num = item_match.group(1)
            description = item_match.group(2).strip()
            # Clean up description (remove quantity if it's at the end)
            description = re.sub(r'\s+\d+[.,]\d{2}\s*$', '', description).strip()
            item_descriptions.append({
                "item_number": item_num,
                "description": description[:200]
            })
    
    # Match items with their amounts from Net price column
    # Assume they're in the same order
    for i, item in enumerate(item_descriptions):
        amount = None
        if i < len(net_price_amounts):
            amount = net_price_amounts[i]
        elif all_amounts:
            # Fallback: try to find a reasonable amount from all_amounts
            # Filter out totals and very small amounts
            reasonable_amounts = [a for a in all_amounts if 1.0 <= a <= 100000.0]
            if i < len(reasonable_amounts):
                amount = reasonable_amounts[i]
        
        if amount:
            line_items.append({
                "item_number": item["item_number"],
                "description": item["description"],
                "amount": amount,
                "quantity": None,
            })
    
    return line_items

def extract_statement_fields(text: str) -> Dict[str, Any]:
    """Extract structured fields from bank statement."""
    fields = {
        "account_number": None,
        "statement_date": None,
        "balance": None,
        "transactions": [],
    }
    
    # Extract account number
    account_patterns = [
        r'account\s*#?\s*:?\s*([\d-]+)',
        r'acct\s*#?\s*:?\s*([\d-]+)',
    ]
    for pattern in account_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields["account_number"] = match.group(1)
            break
    
    # Extract dates (statement date is usually first or last)
    dates = extract_dates(text)
    if dates:
        fields["statement_date"] = dates[0] if len(dates) == 1 else dates[-1]
    
    # Extract balance
    balance_patterns = [
        r'balance\s*:?\s*\$?([\d,]+\.?\d*)',
        r'ending\s+balance\s*:?\s*\$?([\d,]+\.?\d*)',
    ]
    for pattern in balance_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                fields["balance"] = float(re.sub(r'[^\d.]', '', match.group(1)))
            except ValueError:
                pass
            break
    
    return fields

def parse_document(file_path: str, document_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Parse document and extract structured data.
    
    Args:
        file_path: Path to the document
        document_type: Optional document type (will be auto-detected if not provided)
    
    Returns:
        Dictionary with extracted data
    """
    path = Path(file_path)
    extracted_data = {
        "filename": path.name,
        "file_path": str(path),
        "document_type": document_type,
        "raw_text": "",
        "extracted_data": {}
    }
    
    # Extract text based on file type
    if path.suffix.lower() == ".pdf":
        extracted_data["raw_text"] = extract_text_from_pdf(file_path)
    elif path.suffix.lower() in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        extracted_data["raw_text"] = extract_text_with_ocr(file_path)
    else:
        # Handle other file types
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                extracted_data["raw_text"] = f.read()
        except Exception:
            extracted_data["raw_text"] = ""
    
    # Auto-classify if not provided
    if not document_type:
        extracted_data["document_type"] = classify_document(extracted_data["raw_text"])
    
    # Extract structured fields based on document type
    doc_type = extracted_data["document_type"].lower()
    
    if doc_type == "invoice":
        extracted_data["extracted_data"] = extract_invoice_fields(extracted_data["raw_text"])
    elif doc_type == "statement":
        extracted_data["extracted_data"] = extract_statement_fields(extracted_data["raw_text"])
    else:
        # Generic extraction
        extracted_data["extracted_data"] = {
            "amounts": extract_amounts(extracted_data["raw_text"]),
            "dates": extract_dates(extracted_data["raw_text"]),
            "vendor": extract_vendor(extracted_data["raw_text"]),
        }
    
    return extracted_data

