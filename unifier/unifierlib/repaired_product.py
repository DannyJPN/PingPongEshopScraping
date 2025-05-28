﻿import logging
from .downloaded_product import DownloadedProduct


class RepairedProduct:
    def __init__(self):
        self.original_name = ""
        self.category = ""
        self.brand = ""
        self.category_ids = []
        self.code = ""
        self.desc = ""
        self.glami_category = ""
        self.google_category = ""
        self.google_keywords = []
        self.heureka_category = ""
        self.name = ""
        self.price = 0.0
        self.price_standard = 0.0
        self.shortdesc = ""
        self.variantcode = ""
        self.variants = []
        self.zbozi_category = ""
        self.zbozi_keywords = []

        # Original attributes from DownloadedProduct
        self.url = None
        self.main_photo_filepath = None
        self.gallery_photo_filepaths = None

    def fill_from_downloaded(self, downloaded_product: DownloadedProduct):
        """Fill attributes from a DownloadedProduct instance"""
        if not downloaded_product:
            return

        self.original_name = downloaded_product.name
        self.desc = downloaded_product.description
        self.shortdesc = downloaded_product.short_description
        self.url = downloaded_product.url
        self.main_photo_filepath = downloaded_product.main_photo_filepath
        self.gallery_photo_filepaths = downloaded_product.gallery_photo_filepaths
