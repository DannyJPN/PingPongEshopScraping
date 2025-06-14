"""
Variant class for desaka_unifier project.
Simple structural class representing a product variant.
"""

from typing import Dict, Any


class Variant:
    """
    Simple structural class for product variant.
    Contains only the properties from the example data.
    """

    def __init__(self):
        """
        Initialize empty Variant.
        Constructor doesn't fill any properties.
        """
        self.key_value_pairs: Dict[str, Any] = {}
        self.current_price: float = 0.0
        self.basic_price: float = 0.0
        self.stock_status: str = ""
        self.variantcode: str = ""

    def __str__(self) -> str:
        """String representation of the variant."""
        return f"Variant(price={self.current_price}, attributes={self.key_value_pairs})"
