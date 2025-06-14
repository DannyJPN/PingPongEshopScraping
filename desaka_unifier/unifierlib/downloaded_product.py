"""
DownloadedProduct class for desaka_unifier project.
Simple structural class representing a product loaded from CSV export.
"""

from typing import List
from unifierlib.variant import Variant


class DownloadedProduct:
    """
    Simple structural class for product loaded from CSV export.
    Contains only properties, no logic in constructor.
    """

    def __init__(self):
        """
        Initialize empty DownloadedProduct.
        Constructor doesn't fill any properties.
        """
        # Core product information based on your example
        self.name: str = ""
        self.short_description: str = ""
        self.description: str = ""
        self.main_photo_filepath: str = ""
        self.gallery_filepaths: str = ""
        self.variants: List[Variant] = []
        self.url: str = ""

    def __str__(self) -> str:
        """String representation of the product."""
        return f"DownloadedProduct(name='{self.name}', variants={len(self.variants)})"
