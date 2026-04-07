from datetime import datetime


class InventoryService:
    def __init__(self):
        pass

    def restock_if_low(self, product: dict, threshold: int, amount: int) -> dict:
        current_stock = product.get('stock', 0)
        old_stock = current_stock

        if current_stock <= threshold:
            new_stock = current_stock + amount
            product['stock'] = new_stock
            return {
                'product_id': product.get('product_id'),
                'product_name': product.get('name', f"Product #{product.get('product_id')}"),
                'old_stock': old_stock,
                'new_stock': new_stock,
                'amount_added': amount,
                'threshold': threshold
            }
        return None

    def bulk_restock(self, products: list, threshold: int = 10, amount: int = 20) -> list:
        restocked = []
        for product in products:
            result = self.restock_if_low(product, threshold, amount)
            if result:
                restocked.append(result)
        return restocked

    def check_low_stock(self, products: list, threshold: int = 10) -> list:
        low_stock = []
        for product in products:
            if product.get('stock', 0) <= threshold:
                low_stock.append({
                    'product_id': product.get('product_id'),
                    'name': product.get('name', f"Product #{product.get('product_id')}"),
                    'stock': product.get('stock', 0),
                    'threshold': threshold
                })
        return low_stock


inventory_service = InventoryService()