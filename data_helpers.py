import pandas as pd
import numpy as np

def safe_float_convert(value):
    """Safely convert a value to float, handling various formats and errors."""
    if pd.isna(value):
        return 0.0
    
    if isinstance(value, (int, float)):
        return float(value)
    
    try:
        # Remove currency symbols, commas, and other non-numeric chars (except decimal point)
        clean_value = str(value).replace('$', '').replace(',', '').strip()
        if clean_value == '' or clean_value.lower() == 'nan':
            return 0.0
        return float(clean_value)
    except (ValueError, TypeError):
        print(f"Warning: Could not convert value to float: {value}")
        return 0.0

def format_date(date_val):
    """Safely format a date, handling NaT values."""
    if pd.isna(date_val) or date_val is None:
        return "N/A"
    try:
        return date_val.strftime('%m/%d/%Y')
    except:
        return "Invalid Date"

def is_valid_customer(name):
    """Check if a customer name is valid (not nan, empty, etc.)"""
    if pd.isna(name):
        return False
    
    name_str = str(name).strip().lower()
    if name_str == '' or name_str == 'nan' or name_str == 'none' or name_str == 'null':
        return False
        
    # Check if it's just a number
    try:
        float(name_str)
        return False  # It's just a number, not a valid customer name
    except:
        pass
        
    return True

def is_shipping_item(item):
    """Check if an item is shipping-related."""
    if pd.isna(item):
        return False
    
    item_str = str(item).strip().lower()
    return 'shipping' in item_str or 'ship' in item_str or 'postage' in item_str or 'delivery' in item_str

def is_total_row(row, customer_col, type_col=None):
    """Check if a row is a 'Total' summary row for a customer."""
    if type_col is not None and type_col in row and not pd.isna(row[type_col]):
        return False  # If it has a transaction type, it's not a total row
    
    # Check if customer name starts with 'Total'
    if customer_col in row and not pd.isna(row[customer_col]):
        customer_str = str(row[customer_col]).strip()
        return customer_str.startswith('Total ')
    
    return False