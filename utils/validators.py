from typing import Tuple


def validate_price(price: float) -> bool:
    """Price must be positive number"""
    return isinstance(price, (int, float)) and price > 0


def validate_stock(stock: int) -> bool:
    """Stock must be non-negative integer"""
    return isinstance(stock, int) and stock >= 0


def validate_product_dict(product: dict) -> Tuple[bool, str]:
    """Validate product dict has required fields
    
    Returns:
        (is_valid, message)
    """
    required = ['product_id', 'name', 'base_price', 'current_price', 'stock']
    
    for field in required:
        if field not in product:
            return False, f"Missing field: {field}"
    
    if not validate_price(product['base_price']):
        return False, "Invalid base_price"
    
    if not validate_price(product['current_price']):
        return False, "Invalid current_price"
    
    if not validate_stock(product['stock']):
        return False, "Invalid stock"
    
    return True, "OK"