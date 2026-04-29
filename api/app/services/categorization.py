"""
Smart expense categorization using LLM.
"""
import json
from typing import Optional, Dict, Any
from app.services.llm_service import call_llm

# Common expense categories
EXPENSE_CATEGORIES = [
    "Office Supplies",
    "Software & Subscriptions",
    "Travel & Accommodation",
    "Meals & Entertainment",
    "Professional Services",
    "Utilities",
    "Equipment & Hardware",
    "Marketing & Advertising",
    "Training & Education",
    "Insurance",
    "Rent & Facilities",
    "Other"
]

def categorize_expense(vendor: str, description: str, amount: float) -> str:
    """
    Use LLM to intelligently categorize an expense.
    
    Args:
        vendor: Vendor name
        description: Transaction description
        amount: Transaction amount
        
    Returns:
        Category string
    """
    # Build prompt for categorization
    prompt = f"""Categorize this business expense into one of these categories:
{', '.join(EXPENSE_CATEGORIES)}

Vendor: {vendor}
Description: {description}
Amount: ${amount:.2f}

Respond with ONLY the category name, nothing else."""

    try:
        # Call LLM (supports Ollama, Groq, Hugging Face)
        category = call_llm(prompt, timeout=10).strip()
        
        # Clean up the response (remove quotes, extra text)
        category = category.strip('"').strip("'").strip()
        category = category.split('\n')[0].strip()  # Take first line only
        
        # Validate category
        if category in EXPENSE_CATEGORIES:
            return category
        
        # Try fuzzy matching
        category_lower = category.lower()
        for cat in EXPENSE_CATEGORIES:
            if cat.lower() in category_lower or category_lower in cat.lower():
                return cat
        
        # Default fallback
        return "Other"
        
    except Exception as e:
        print(f"Error categorizing expense: {e}")
        # Fallback: simple keyword-based categorization
        return _fallback_categorize(vendor, description)

def _fallback_categorize(vendor: str, description: str) -> str:
    """Fallback categorization using keywords."""
    text = f"{vendor} {description}".lower()
    
    if any(kw in text for kw in ["office", "supplies", "stationery", "paper", "pen"]):
        return "Office Supplies"
    elif any(kw in text for kw in ["software", "saas", "subscription", "license", "cloud"]):
        return "Software & Subscriptions"
    elif any(kw in text for kw in ["travel", "hotel", "flight", "uber", "taxi", "airline"]):
        return "Travel & Accommodation"
    elif any(kw in text for kw in ["restaurant", "food", "meal", "cafe", "dining"]):
        return "Meals & Entertainment"
    elif any(kw in text for kw in ["legal", "consulting", "accounting", "service", "professional"]):
        return "Professional Services"
    elif any(kw in text for kw in ["electric", "water", "gas", "utility", "internet", "phone"]):
        return "Utilities"
    elif any(kw in text for kw in ["equipment", "computer", "hardware", "device"]):
        return "Equipment & Hardware"
    elif any(kw in text for kw in ["marketing", "advertising", "ad", "promotion"]):
        return "Marketing & Advertising"
    else:
        return "Other"

def batch_categorize_transactions(transactions: list) -> Dict[int, str]:
    """
    Categorize multiple transactions efficiently.
    Returns dict mapping transaction_id -> category
    """
    results = {}
    for txn in transactions:
        category = categorize_expense(
            vendor=txn.get("vendor", ""),
            description=txn.get("description", ""),
            amount=txn.get("amount", 0)
        )
        results[txn.get("id")] = category
    return results

