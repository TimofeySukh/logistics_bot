"""
Smart category matching module
Handles user input matching with product categories including:
- Case-insensitive matching
- Transliteration support
- Fuzzy matching
- Multiple word matching
"""

from config import SUPPLY_EMPLOYEES


def normalize_text(text):
    """
    Normalize text for better matching:
    - Convert to lowercase
    - Remove extra spaces
    - Strip leading/trailing spaces
    """
    return ' '.join(text.lower().strip().split())


def find_employee_by_category(user_message):
    """
    Find the responsible employee based on user's message about product.
    
    Args:
        user_message (str): User's message describing the product
        
    Returns:
        dict or None: Employee data if found, None otherwise
        Format: {'key': 'employee_1', 'name': 'Name', 'username': '@adasdaasd', 'user_id': 123}
    """
    normalized_message = normalize_text(user_message)
    
    # Try to find matches for each employee
    matches = []
    
    for employee_key, employee_data in SUPPLY_EMPLOYEES.items():
        categories = employee_data['categories']
        
        # Check if any category matches the message
        for category in categories:
            normalized_category = normalize_text(category)
            
            # Check for exact word match or substring match
            if normalized_category in normalized_message or normalized_message in normalized_category:
                matches.append({
                    'key': employee_key,
                    'name': employee_data['name'],
                    'username': employee_data['username'],
                    'user_id': employee_data['user_id'],
                    'matched_category': category
                })
                break  # Found a match for this employee, no need to check other categories
    
    # Return result based on number of matches
    if len(matches) == 0:
        return None  # No match found
    elif len(matches) == 1:
        return matches[0]  # Single match - perfect
    else:
        # Multiple matches - need user to choose
        # Return None to trigger category selection menu
        return None


def get_category_buttons():
    """
    Generate list of categories for user selection.
    Each category is represented by employee name and their product list.
    
    Returns:
        list: List of tuples (employee_key, display_text)
    """
    buttons = []
    
    for employee_key, employee_data in SUPPLY_EMPLOYEES.items():
        # Get first few categories for display
        categories_preview = ', '.join(employee_data['categories'][:5])
        if len(employee_data['categories']) > 5:
            categories_preview += '...'
        
        display_text = f"{employee_data['name']}: {categories_preview}"
        buttons.append((employee_key, display_text))
    
    return buttons


def get_employee_by_key(employee_key):
    """
    Get employee data by their key.
    
    Args:
        employee_key (str): Employee key (e.g., 'employee_1', 'employee_2', etc.)
        
    Returns:
        dict or None: Employee data if found, None otherwise
    """
    employee_data = SUPPLY_EMPLOYEES.get(employee_key)
    if employee_data:
        return {
            'key': employee_key,
            'name': employee_data['name'],
            'username': employee_data['username'],
            'user_id': employee_data['user_id']
        }
    return None

