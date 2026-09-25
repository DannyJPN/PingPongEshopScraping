"""
RepairedProduct class for desaka_unifier project.

This module contains the RepairedProduct class which represents a product
after repair/unification process with all required fields.
"""

from typing import List, Optional, Any


class RepairedProduct:
    """
    Represents a product after the repair/unification process.

    This class contains all the fields needed for the final unified product
    with proper categorization, pricing, and metadata.
    """

    def __init__(self,**kwargs):
        """Initialize RepairedProduct with default values."""
        self.original_name: str = ""
        self.category: str = ""
        self.brand: str = ""
        self.type: str = ""  # Typ produktu
        self.model: str = ""  # Model produktu
        self.category_ids: str = ""
        self.code: str = ""
        self.desc: str = ""
        self.glami_category: str = ""
        self.google_category: str = ""
        self.google_keywords: str = ""
        self.heureka_category: str = ""
        self.name: str = ""
        self.price: str = ""
        self.price_standard: str = ""
        self.shortdesc: str = ""
        self.url: str = ""
        self.Variants: List[Any] = []
        self.zbozi_category: str = ""
        self.zbozi_keywords: str = ""
        allowed = set(self.__dict__.keys())
        unknown = [k for k in kwargs.keys() if k not in allowed]
        if unknown:
            raise TypeError(f"Unknown Parameters: {', '.join(unknown)}")

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self) -> str:
        """Return string representation of RepairedProduct."""
        return (f"RepairedProduct(name='{self.name}', code='{self.code}', "
                f"brand='{self.brand}', type='{self.type}', model='{self.model}', "
                f"category='{self.category}', price='{self.price}', variants={len(self.Variants)})")
