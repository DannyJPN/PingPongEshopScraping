"""
Parser module for desaka_unifier project.
Contains logic for converting pincesobchod JSON to ExportProduct array.
"""

from typing import Dict, Any, List, Optional
import time
import json
import logging
import os
import re
from datetime import datetime
from difflib import SequenceMatcher
from tqdm import tqdm
from unifierlib.export_product import ExportProduct, ExportMainProduct, ExportProductVariant
from unifierlib.downloaded_product import DownloadedProduct
from unifierlib.repaired_product import RepairedProduct
from unifierlib.openai_unifier import OpenAIUnifier
from unifierlib.variant import Variant
from unifierlib.constants import (
    MEMORY_KEY_BRAND_CODE_LIST, MEMORY_KEY_CATEGORY_CODE_LIST, MEMORY_KEY_CATEGORY_ID_LIST,
    MEMORY_KEY_CATEGORY_LIST, MEMORY_KEY_CATEGORY_SUB_CODE_LIST, MEMORY_KEY_CATEGORY_MEMORY,
    MEMORY_KEY_CATEGORY_NAME_MEMORY, MEMORY_KEY_DESC_MEMORY, MEMORY_KEY_KEYWORDS_GOOGLE, MEMORY_KEY_KEYWORDS_ZBOZI,
    MEMORY_KEY_NAME_MEMORY, MEMORY_KEY_PRODUCT_BRAND_MEMORY, MEMORY_KEY_PRODUCT_MODEL_MEMORY,
    MEMORY_KEY_PRODUCT_TYPE_MEMORY, MEMORY_KEY_SHORT_DESC_MEMORY, MEMORY_KEY_VARIANT_NAME_MEMORY,
    MEMORY_KEY_VARIANT_VALUE_MEMORY, MEMORY_KEY_CATEGORY_MAPPING_GLAMI, MEMORY_KEY_CATEGORY_MAPPING_GOOGLE,
    MEMORY_KEY_CATEGORY_MAPPING_HEUREKA, MEMORY_KEY_CATEGORY_MAPPING_ZBOZI, MEMORY_KEY_DEFAULT_EXPORT_PRODUCT_VALUES
)


class ProductParser:
    """
    Universal parser for all product conversions.
    Handles JSON->ExportProduct, CSV->DownloadedProduct, and DownloadedProduct->RepairedProduct.
    """

    def __init__(self, memory_data: Optional[Dict[str, Any]] = None, language: Optional[str] = None,
                 export_products: Optional[List[Any]] = None, repaired_products: Optional[List[Any]] = None,
                 confirm_ai_results: bool = False, use_fine_tuned_models: bool = False,
                 fine_tuned_models: Optional[Dict[str, str]] = None, supported_languages_data: Optional[list] = None,
                 skip_ai: bool = False):
        """
        Initialize parser with optional memory data, language, export products and AI confirmation setting.

        Args:
            memory_data (Optional[Dict[str, Any]]): Dictionary containing all loaded memory files
            language (Optional[str]): Current language code (e.g., 'CS', 'SK')
            export_products (Optional[List[Any]]): List of existing ExportProduct objects
            repaired_products (Optional[List[Any]]): List of existing RepairedProduct objects
            confirm_ai_results (bool): Whether to automatically confirm AI results (default: False)
            use_fine_tuned_models (bool): Whether to use fine-tuned models (default: False)
            fine_tuned_models (Optional[Dict[str, str]]): Dictionary mapping task types to model IDs
            supported_languages_data (Optional[list]): Pre-loaded supported languages data
            skip_ai (bool): Whether to skip using AI for property evaluation (default: False)
        """
        self.memory = memory_data or {}
        self.language = language or 'CS'
        self.export_products = export_products or []
        self.repaired_products = repaired_products or []
        self.confirm_ai_results = confirm_ai_results
        self.supported_languages_data = supported_languages_data

        # Track assigned codes to avoid duplicates
        self.assigned_codes = set()
        self.assigned_variant_codes = set()

        # Initialize assigned codes from existing products
        self._initialize_assigned_codes()

        # Initialize OpenAI only if memory data is provided, API key is available, and AI is not skipped
        self.openai = None
        if memory_data and not skip_ai:
            try:
                self.openai = OpenAIUnifier(use_fine_tuned_models, fine_tuned_models, supported_languages_data)
            except (ValueError, ImportError) as e:
                logging.warning(f"OpenAI not available: {str(e)}")
                self.openai = None
        elif skip_ai:
            logging.info("AI usage is disabled by the --SkipAI flag.")

    def _initialize_assigned_codes(self):
        """Initialize assigned codes from existing export and repaired products."""
        # Initialize from export products
        for product in self.export_products:
            if hasattr(product, 'kod') and product.kod:
                self.assigned_codes.add(product.kod)
            if hasattr(product, 'variantcode') and product.variantcode:
                self.assigned_variant_codes.add(product.variantcode)

        # Initialize from repaired products
        for product in self.repaired_products:
            if hasattr(product, 'code') and product.code:
                self.assigned_codes.add(product.code)
            if hasattr(product, 'variantcode') and product.variantcode:
                self.assigned_variant_codes.add(product.variantcode)
            # Also check variant codes in Variants
            if hasattr(product, 'Variants') and product.Variants:
                for variant in product.Variants:
                    if hasattr(variant, 'variantcode') and variant.variantcode:
                        self.assigned_variant_codes.add(variant.variantcode)

    def json_to_export_products(self, data: Dict[str, Any]) -> List[ExportProduct]:
        """
        Convert pincesobchod JSON data to ExportProduct array.
        One JSON object returns array where first is main product and rest are variants.

        Args:
            data (Dict[str, Any]): Pincesobchod product data

        Returns:
            List[ExportProduct]: Array of ExportProducts (main + variants)
        """
        mappings = []

        # Create main product
        main_product = ExportMainProduct()

        # Fill main product data
        main_product.id = data['id']
        main_product.zobrazit = int(data.get('visibility', 1))
        main_product.archiv = int(data.get('archive', 0))
        main_product.kod = data.get('catalogNumber', "")
        main_product.kod_vyrobku = data.get('mpn', "")
        main_product.ean = data.get('ean', "")
        main_product.isbn = data.get('isbn', "")
        main_product.nazev = data['translations']['cs']['name']
        main_product.privlastek = data['translations']['cs'].get('nameext', "")
        main_product.vyrobce = data.get('manufacturer', {}).get('name', "") if data.get('manufacturer') else ""
        main_product.dodavatel_id = data.get('supplier_id', "")
        main_product.cena = data.get('price', 0)
        main_product.cena_bezna = data.get('standardPrice', 0)
        main_product.cena_nakupni = data.get('purchasePrice', "")
        main_product.recyklacni_poplatek = data.get('recycle_fee', "")
        main_product.dph = data.get('vat', {}).get('rate', 21) if data.get('vat') else 21
        main_product.sleva = data.get('discount', 0)
        main_product.sleva_od = data.get('discount_from', "")
        main_product.sleva_do = data.get('discount_to', "")
        main_product.popis = data['translations']['cs'].get('description', "")
        main_product.popis_strucny = data['translations']['cs'].get('annotation', "")
        main_product.kosik = int(data.get('sales', 1))
        main_product.home = int(data.get('homepage', 0))
        main_product.dostupnost = data.get('availability', "#")
        main_product.doprava_zdarma = int(data.get('deliveryFree', 0))
        main_product.dodaci_doba = data.get('deliveryTime', "#")
        main_product.dodaci_doba_auto = data.get('deliveryTimeAuto', "#")
        main_product.sklad = data.get('stock', "#")
        main_product.na_sklade = data.get('inStock', "#")
        main_product.hmotnost = data.get('weight', "")
        main_product.delka = data.get('length', "")
        main_product.jednotka = data.get('unit', "ks")
        main_product.odber_po = data.get('limitMultiple', 1)
        main_product.odber_min = data.get('limitMin', 1)
        main_product.odber_max = data.get('limitMax', "")
        main_product.pocet = data.get('quantityPack', 1)
        main_product.zaruka = data.get('guarantee', {}).get('name', "") if data.get('guarantee') else ""
        main_product.marze_dodavatel = data.get('margin', "")
        main_product.seo_titulek = data['translations']['cs'].get('metaTitle', "")
        main_product.seo_popis = data['translations']['cs'].get('metaDescription', "")
        main_product.eroticke = int(data.get('erotic', 0))
        main_product.pro_dospele = int(data.get('adult', 0))
        main_product.slevovy_kupon = int(data.get('voucherDiscount', 1))
        main_product.darek_objednavka = int(data.get('gift_free', 1))
        main_product.priorita = data.get('priority', 0)
        main_product.poznamka = data.get('comment', "")
        main_product.stitky = ",".join([str(tag['name']) for tag in data.get('tags', [])])
        main_product.kategorie_id = ",".join([str(cat['id']) for cat in data.get('categories', [])])
        main_product.podobne = ",".join([str(rel['id']) for rel in data.get('related', [])])
        main_product.prislusenstvi = ",".join([str(acc['id']) for acc in data.get('accessory', [])])
        main_product.variantove = ",".join([str(var['id']) for var in data.get('variants', [])])
        main_product.zdarma = ",".join([str(fr['id']) for fr in data.get('free', [])])
        main_product.sluzby = ",".join([str(serv['id']) for serv in data.get('services', [])])
        main_product.rozsirujici_obsah = ",".join([str(ext['id']) for ext in data.get('extended_content', [])])

        # Zbozi.cz
        zbozi_feeds = data.get('feeds', {}).get('zbozi', {}) if data.get('feeds') else {}
        main_product.zbozicz_skryt = int(zbozi_feeds.get('hidden', 0))
        main_product.zbozicz_productname = zbozi_feeds.get('productname', "")
        main_product.zbozicz_product = zbozi_feeds.get('product', "")
        main_product.zbozicz_cpc = zbozi_feeds.get('cpc', 5)
        main_product.zbozicz_cpc_search = zbozi_feeds.get('cpc_search', 5)
        main_product.zbozicz_kategorie = zbozi_feeds.get('category', "")
        main_product.zbozicz_stitek_0 = zbozi_feeds.get('customeLabel0', "")
        main_product.zbozicz_stitek_1 = zbozi_feeds.get('customeLabel1', "")
        main_product.zbozicz_extra = zbozi_feeds.get('extraMessage', "")

        # Heureka.cz
        heureka_feeds = data.get('feeds', {}).get('heurekacs', {}) if data.get('feeds') else {}
        main_product.heurekacz_skryt = int(heureka_feeds.get('hidden', 0))
        main_product.heurekacz_productname = heureka_feeds.get('productname', "")
        main_product.heurekacz_product = heureka_feeds.get('product', "")
        main_product.heurekacz_cpc = heureka_feeds.get('cpc', 1)
        main_product.heurekacz_kategorie = heureka_feeds.get('category', "")

        # Google
        google_feeds = data.get('feeds', {}).get('google', {}) if data.get('feeds') else {}
        main_product.google_skryt = int(google_feeds.get('hidden', 0))
        main_product.google_kategorie = google_feeds.get('category', "")
        main_product.google_stitek_0 = google_feeds.get('customeLabel0', "")
        main_product.google_stitek_1 = google_feeds.get('customeLabel1', "")
        main_product.google_stitek_2 = google_feeds.get('customeLabel2', "")
        main_product.google_stitek_3 = google_feeds.get('customeLabel3', "")
        main_product.google_stitek_4 = google_feeds.get('customeLabel4', "")

        # Glami
        glami_feeds = data.get('feeds', {}).get('glami', {}) if data.get('feeds') else {}
        main_product.glami_skryt = int(glami_feeds.get('hidden', 0))
        main_product.glami_kategorie = glami_feeds.get('category', "")
        main_product.glami_cpc = glami_feeds.get('cpc', 1)
        main_product.glami_voucher = glami_feeds.get('promotionId', "")
        main_product.glami_material = glami_feeds.get('material', "")
        main_product.glamisk_material = glami_feeds.get('material', "")

        # Warehouse
        warehouse_data = data.get('warehouse', {}) if data.get('warehouse') else {}
        main_product.sklad_umisteni = warehouse_data.get('location', "#")
        main_product.sklad_minimalni = warehouse_data.get('stockMinimum', "#")
        main_product.sklad_optimalni = warehouse_data.get('stockOptimal', "#")
        main_product.sklad_maximalni = warehouse_data.get('stockMaximum', "#")

        # Add main product to array
        mappings.append(main_product)

        # Process variants
        for variant in data.get('variants', []):
            variant_product = ExportProductVariant()

            # Fill variant data
            variant_product.id = data['id']
            variant_product.varianta_id = variant['id']
            variant_product.kod = variant.get('catalogNumber', "")
            variant_product.kod_vyrobku = variant.get('mpn', "")
            variant_product.ean = variant.get('ean', "")
            variant_product.cena = variant.get('price', 0)
            variant_product.cena_bezna = variant.get('standardPrice', 0)
            variant_product.cena_nakupni = variant.get('purchasePrice', "")
            variant_product.hmotnost = variant.get('weight', "")
            variant_product.delka = variant.get('length', "")
            variant_product.sklad_umisteni = variant.get('warehouse', {}).get('location', "")
            variant_product.sklad_minimalni = variant.get('warehouse', {}).get('stockMinimum', "")
            variant_product.sklad_optimalni = variant.get('warehouse', {}).get('stockOptimal', "")
            variant_product.sklad_maximalni = variant.get('warehouse', {}).get('stockMaximum', "")

            # Process variant options
            if variant.get('options'):
                for i, option in enumerate(variant['options'], 1):
                    if i <= 3:  # Maximum 3 variants
                        if i == 1:
                            variant_product.varianta1_nazev = option.get('name', "").strip()
                            variant_product.varianta1_hodnota = option.get('value', "").strip()
                        elif i == 2:
                            variant_product.varianta2_nazev = option.get('name', "").strip()
                            variant_product.varianta2_hodnota = option.get('value', "").strip()
                        elif i == 3:
                            variant_product.varianta3_nazev = option.get('name', "").strip()
                            variant_product.varianta3_hodnota = option.get('value', "").strip()

            mappings.append(variant_product)

        return mappings

    def csv_to_downloaded_products(self, csv_data: List[Dict[str, Any]]) -> List[DownloadedProduct]:
        """
        Convert CSV data to DownloadedProduct array, skipping entries without a name.

        Args:
            csv_data (List[Dict[str, Any]]): List of CSV rows as dictionaries

        Returns:
            List[DownloadedProduct]: Array of DownloadedProducts
        """
        products = []

        for row in tqdm(csv_data, desc="Converting CSV to DownloadedProducts", unit="product"):
            name = row.get('Name', '').strip()

            # Skip if name is missing or empty
            if not name:
                continue

            # Create DownloadedProduct and fill properties explicitly
            product = DownloadedProduct()
            product.name = name
            product.short_description = row.get('Short Description', '')
            product.description = row.get('Description', '')
            product.main_photo_filepath = row.get('Main Photo Filepath', '')
            product.gallery_filepaths = row.get('Gallery Filepaths', '')
            product.url = row.get('URL', '')

            # Parse variants if present
            variants_data = row.get('Variants', '')
            if variants_data:
                product.variants = self._parse_variants_from_string(variants_data)

            products.append(product)

        return products

    def _parse_variants_from_string(self, variants_string: str) -> List:
        """
        Parse variants from pipe-separated JSON string.

        Args:
            variants_string (str): Pipe-separated JSON variants

        Returns:
            List: List of parsed variants
        """
        variants = []

        if not variants_string.strip():
            return variants

        try:
            # Handle pipe-separated JSON objects
            if '|' in variants_string:
                variant_strings = variants_string.split('|')
                for variant_str in variant_strings:
                    variant_str = variant_str.strip()
                    if variant_str:
                        try:
                            from unifierlib.variant import Variant
                            variant = Variant()
                            variant_dict = json.loads(variant_str)

                            # Fill variant properties
                            variant.key_value_pairs = variant_dict.get('key_value_pairs', {})
                            # Ensure prices are set to 0.0 if missing or empty
                            current_price = variant_dict.get('current_price', 0.0)
                            variant.current_price = float(current_price) if current_price not in [None, '', 0] else 0.0
                            basic_price = variant_dict.get('basic_price', 0.0)
                            variant.basic_price = float(basic_price) if basic_price not in [None, '', 0] else 0.0
                            variant.stock_status = variant_dict.get('stock_status', '')

                            variants.append(variant)
                        except json.JSONDecodeError:
                            logging.warning(f"Could not parse variant JSON: {variant_str}")
            else:
                # Single JSON string
                try:
                    variant_data = json.loads(variants_string)
                    if isinstance(variant_data, list):
                        for item in variant_data:
                            from unifierlib.variant import Variant
                            variant = Variant()
                            variant.key_value_pairs = item.get('key_value_pairs', {})
                            # Ensure prices are set to 0.0 if missing or empty
                            current_price = item.get('current_price', 0.0)
                            variant.current_price = float(current_price) if current_price not in [None, '', 0] else 0.0
                            basic_price = item.get('basic_price', 0.0)
                            variant.basic_price = float(basic_price) if basic_price not in [None, '', 0] else 0.0
                            variant.stock_status = item.get('stock_status', '')
                            variants.append(variant)
                    elif isinstance(variant_data, dict):
                        from unifierlib.variant import Variant
                        variant = Variant()
                        variant.key_value_pairs = variant_data.get('key_value_pairs', {})
                        # Ensure prices are set to 0.0 if missing or empty
                        current_price = variant_data.get('current_price', 0.0)
                        variant.current_price = float(current_price) if current_price not in [None, '', 0] else 0.0
                        basic_price = variant_data.get('basic_price', 0.0)
                        variant.basic_price = float(basic_price) if basic_price not in [None, '', 0] else 0.0
                        variant.stock_status = variant_data.get('stock_status', '')
                        variants.append(variant)
                except json.JSONDecodeError:
                    logging.warning(f"Could not parse variants JSON: {variants_string}")

        except Exception as e:
            logging.error(f"Error parsing variants: {str(e)}")

        return variants


    def downloaded_to_repaired_product(self, downloaded: DownloadedProduct) -> RepairedProduct:
        """
        Convert DownloadedProduct to RepairedProduct with complex logic.

        Args:
            downloaded (DownloadedProduct): Source product

        Returns:
            RepairedProduct: Converted product
        """
        if not self.memory:
            raise ValueError("Memory data is required for DownloadedProduct to RepairedProduct conversion")

        repaired = RepairedProduct()

        # original_name = DownloadedProduct.name (direct access)
        repaired.original_name = downloaded.name

        # url = DownloadedProduct.url (direct access)
        repaired.url = downloaded.url

        # desc = from DescMemory or OpenAI
        #repaired.desc = self._get_description(downloaded)

        # shortdesc = from ShortDescMemory or OpenAI
        #repaired.shortdesc = self._get_short_description(downloaded)

        # name = from NameMemory or OpenAI
        #repaired.name = self._get_product_name(downloaded)
        # category = from CategoryMemory or OpenAI (needed for code generation)
       # repaired.category = self._get_category(downloaded)

        # brand = from ProductBrandMemory or OpenAI (needed for code generation)
        repaired.brand = self._get_brand(downloaded)


        # category_ids = derived from category using CategoryIDList
       # repaired.category_ids = self._get_category_ids(repaired.category, downloaded)



        # code = complex code generation (needs brand and category)
       # repaired.code = self._generate_code(repaired.brand, repaired.category, downloaded.name)

        # Variants = complex variant processing (needs code for variant codes)
        repaired.Variants = self._process_variants(downloaded, repaired.code)
        # price and price_standard = from variants
      #  repaired.price, repaired.price_standard = self._get_prices(downloaded)

        # glami_category = from CategoryMappingGlami or user input
       # repaired.glami_category = self._get_category_mapping(repaired.category, 'Glami', downloaded)

        # google_category = from CategoryMappingGoogle or user input
       # repaired.google_category = self._get_category_mapping(repaired.category, 'Google', downloaded)

        # google_keywords = from KeywordsGoogle or OpenAI
 #       repaired.google_keywords = self._get_google_keywords(downloaded)

        # heureka_category = from CategoryMappingHeureka or user input
      #  repaired.heureka_category = self._get_category_mapping(repaired.category, 'Heureka', downloaded)

        # zbozi_category = from CategoryMappingZbozi or user input
       # repaired.zbozi_category = self._get_category_mapping(repaired.category, 'Zbozi', downloaded)

        # zbozi_keywords = from KeywordsZbozi or OpenAI
 #       repaired.zbozi_keywords = self._get_zbozi_keywords(downloaded)

        return repaired

    def _find_exact_matches_in_text(self, text: str, values: List[str]) -> List[str]:
        """
        Find exact matches of values in text as whole words only.

        Args:
            text (str): Text to search in
            values (List[str]): List of values to search for

        Returns:
            List[str]: List of found values
        """
        if not text or not values:
            return []

        import re
        
        # Normalize text for searching (convert to lowercase)
        normalized_text = text.lower()

        # Find exact matches (case insensitive, whole words only)
        matches = []
        for value in values:
            if value and value.strip():
                # Escape special regex characters in the value
                escaped_value = re.escape(value.lower().strip())
                # Use word boundaries to match whole words only
                pattern = r'\b' + escaped_value + r'\b'
                
                if re.search(pattern, normalized_text):
                    matches.append(value)

        return matches

    def _heuristic_similarity_search(self, downloaded: DownloadedProduct, values: List[str], threshold: float = 0.8) -> tuple:
        """
        Perform similarity-based heuristic search on downloaded product.
        Uses fuzzy matching (SequenceMatcher) to find similar values.
        This method is called when exact matching finds no results.

        Args:
            downloaded (DownloadedProduct): Product to extract from
            values (List[str]): List of values to search for
            threshold (float): Minimum similarity threshold (0.0-1.0, default: 0.8)

        Returns:
            tuple: (Single match if exactly one found or None, List of all matches)
        """
        if not values:
            return None, []

        # Collect all texts to search in (same as _heuristic_extraction)
        texts = []

        # Add original_name if available
        if downloaded.name:
            texts.append(downloaded.name)

        # Add URL if available
        if downloaded.url:
            texts.append(downloaded.url)

        # Add desc if available
        if hasattr(downloaded, 'desc') and downloaded.desc:
            texts.append(downloaded.desc)
        elif hasattr(downloaded, 'description') and downloaded.description:
            texts.append(downloaded.description)

        # Add shortdesc if available
        if hasattr(downloaded, 'shortdesc') and downloaded.shortdesc:
            texts.append(downloaded.shortdesc)
        elif hasattr(downloaded, 'short_description') and downloaded.short_description:
            texts.append(downloaded.short_description)

        # Normalize texts for comparison
        def normalize_text(text: str) -> str:
            """Normalize text for similarity comparison."""
            return ' '.join(text.lower().split())

        normalized_texts = [normalize_text(text) for text in texts if text]

        # Find similar matches using fuzzy matching
        similarity_scores = {}  # value -> max_similarity

        for value in values:
            if not value or not value.strip():
                continue

            normalized_value = normalize_text(value)
            max_similarity = 0.0

            # Check similarity against all product texts
            for text in normalized_texts:
                # Calculate similarity ratio
                similarity = SequenceMatcher(None, normalized_value, text).ratio()
                max_similarity = max(max_similarity, similarity)

                # Also check if the value appears as a substring (partial match)
                if normalized_value in text or text in normalized_value:
                    # Boost similarity for substring matches
                    substring_similarity = len(normalized_value) / max(len(text), len(normalized_value))
                    max_similarity = max(max_similarity, substring_similarity)

            # Store the maximum similarity for this value
            if max_similarity >= threshold:
                similarity_scores[value] = max_similarity

        # Sort matches by similarity (highest first)
        sorted_matches = sorted(similarity_scores.items(), key=lambda x: x[1], reverse=True)
        all_matches_list = [match[0] for match in sorted_matches]

        # Return single match if exactly one found, otherwise None and list of all matches
        if len(all_matches_list) == 1:
            return all_matches_list[0], all_matches_list
        else:
            return None, all_matches_list

    def _find_similar_memory_keys(self, product_name: str, memory_dict: Dict[str, str], threshold: float = 0.8) -> List[tuple]:
        """
        Find similar keys in memory dictionary using fuzzy matching.
        This is called when exact key match is not found in memory.

        Args:
            product_name (str): The product name to search for (KEY)
            memory_dict (Dict[str, str]): Memory dictionary (KEY -> VALUE)
            threshold (float): Minimum similarity threshold (0.0-1.0, default: 0.8)

        Returns:
            List[tuple]: List of (key, value, similarity) tuples sorted by similarity (highest first)
        """
        if not product_name or not memory_dict:
            return []

        def normalize_text(text: str) -> str:
            """Normalize text for similarity comparison."""
            return ' '.join(text.lower().split())

        normalized_product_name = normalize_text(product_name)
        similar_keys = []

        # Search for similar keys in memory
        for key, value in memory_dict.items():
            normalized_key = normalize_text(key)

            # Calculate similarity ratio
            similarity = SequenceMatcher(None, normalized_product_name, normalized_key).ratio()

            # Store if similarity meets threshold
            if similarity >= threshold:
                similar_keys.append((key, value, similarity))

        # Sort by similarity (highest first)
        similar_keys.sort(key=lambda x: x[2], reverse=True)

        return similar_keys

    def _ask_user_for_similar_key_selection(self, property_name: str, product_name: str, similar_keys: List[tuple]) -> Optional[str]:
        """
        Ask user to select a value from similar memory keys.

        Args:
            property_name (str): Name of the property (e.g., "Brand", "Product Type")
            product_name (str): The product name being processed
            similar_keys (List[tuple]): List of (key, value, similarity) tuples

        Returns:
            Optional[str]: Selected value or None if user rejects all options
        """
        if not similar_keys:
            return None

        print("\n" + "=" * 80)
        print(f"🔍 SIMILAR MEMORY KEYS FOUND FOR {property_name.upper()}")
        print("=" * 80)
        print(f"Product: {product_name}")
        print(f"\nFound {len(similar_keys)} similar key(s) in memory:")
        print()

        # Display options with numbering
        for i, (key, value, similarity) in enumerate(similar_keys, 1):
            similarity_pct = similarity * 100
            print(f"  {i}. Key: {key}")
            print(f"     Value: {value}")
            print(f"     Similarity: {similarity_pct:.1f}%")
            print()

        print("=" * 80)
        print("Options:")
        print("  [1-N]  - Use value from selected key")
        print("  'none' - Skip all options and continue to heuristic search")
        print("=" * 80)

        while True:
            response = input(f"\nSelect option for {property_name}: ").strip()

            if response.lower() == 'none':
                return None

            try:
                selection = int(response)
                if 1 <= selection <= len(similar_keys):
                    selected_key, selected_value, similarity = similar_keys[selection - 1]
                    print(f"\n✓ Selected: {selected_value} (from key: {selected_key})")
                    return selected_value
                else:
                    print(f"❌ Invalid selection. Please enter a number between 1 and {len(similar_keys)} or 'none'")
            except ValueError:
                print(f"❌ Invalid input. Please enter a number between 1 and {len(similar_keys)} or 'none'")

    def _heuristic_extraction(self, downloaded: DownloadedProduct, values: List[str]) -> tuple:
        """
        Perform heuristic extraction on downloaded product.

        Args:
            downloaded (DownloadedProduct): Product to extract from
            values (List[str]): List of values to search for

        Returns:
            tuple: (Single match if exactly one found or None, List of all matches)
        """
        if not values:
            return None, []

        # Collect all texts to search in
        texts = []

        # Add original_name if available
        if downloaded.name:
            texts.append(downloaded.name)

        # Add URL if available
        if downloaded.url:
            texts.append(downloaded.url)

        # Add desc if available
        # For RepairProduct, use desc attribute; for DownloadedProduct, use description
        if hasattr(downloaded, 'desc') and downloaded.desc:
            texts.append(downloaded.desc)
        elif hasattr(downloaded, 'description') and downloaded.description:
            texts.append(downloaded.description)

        # Add shortdesc if available
        # For RepairProduct, use shortdesc attribute; for DownloadedProduct, use short_description
        if hasattr(downloaded, 'shortdesc') and downloaded.shortdesc:
            texts.append(downloaded.shortdesc)
        elif hasattr(downloaded, 'short_description') and downloaded.short_description:
            texts.append(downloaded.short_description)

        # Perform matching on all texts
        all_matches = set()
        for text in texts:
            if text:  # Check if text is not None or empty
                matches = self._find_exact_matches_in_text(text, values)
                all_matches.update(matches)

        # Convert set back to list for consistent ordering
        all_matches_list = list(all_matches)

        # If no exact matches found, try similarity-based search
        if len(all_matches_list) == 0:
            return self._heuristic_similarity_search(downloaded, values, threshold=0.8)

        # Return single match if exactly one found, otherwise None and list of all matches
        if len(all_matches_list) == 1:
            return all_matches_list[0], all_matches_list
        else:
            return None, all_matches_list

    def _get_category(self, downloaded: DownloadedProduct) -> str:
        """Get category from memory, heuristics, or OpenAI with user confirmation."""
        memory_key = MEMORY_KEY_CATEGORY_MEMORY.format(language=self.language)
        if memory_key in self.memory:
            category_memory = self.memory[memory_key]
            if downloaded.name in category_memory:
                category_key = category_memory[downloaded.name]
                # First standardize the category key, then translate
                standardized_key = self._standardize_category_by_key(category_key)
                return self._get_translated_category_name(standardized_key)

        # Try to find similar keys in memory
        if memory_key in self.memory:
            category_memory = self.memory[memory_key]
            similar_keys = self._find_similar_memory_keys(downloaded.name, category_memory, threshold=0.8)

            if similar_keys:
                # For categories, we need to convert keys to translated category names for display
                similar_keys_with_translated_names = []
                for key, category_key_value, similarity in similar_keys:
                    standardized_key = self._standardize_category_by_key(category_key_value)
                    translated_name = self._get_translated_category_name(standardized_key)
                    # Store original category_key_value for saving later
                    similar_keys_with_translated_names.append((key, translated_name, similarity, category_key_value))

                # Show user the translated category names
                display_keys = [(key, translated_name, sim) for key, translated_name, sim, _ in similar_keys_with_translated_names]
                selected_category_name = self._ask_user_for_similar_key_selection("Category", downloaded.name, display_keys)

                if selected_category_name:
                    # Find the original category_key_value for saving
                    selected_category_key_value = None
                    for key, translated_name, similarity, category_key_value in similar_keys_with_translated_names:
                        if translated_name == selected_category_name:
                            selected_category_key_value = category_key_value
                            break

                    if selected_category_key_value:
                        # Save to memory with current product name as key
                        self.memory[memory_key][downloaded.name] = selected_category_key_value
                        self._save_memory_file(memory_key)
                        # Return the translated category name
                        return selected_category_name

        # Get available category names (translated values from CategoryNameMemory)
        category_name_memory_key = MEMORY_KEY_CATEGORY_NAME_MEMORY.format(language=self.language)
        category_name_memory = self.memory.get(category_name_memory_key, {})
        available_categories = list(category_name_memory.values()) if category_name_memory else []

        # Try heuristic extraction
        single_match = None
        all_matches = []
        if available_categories:
            single_match, all_matches = self._heuristic_extraction(downloaded, available_categories)

            # Use OpenAI with CategoryNameMemory (translated category names) even if memory is empty
        if not single_match and self.openai:
            # Include information about heuristic matches in the AI prompt if any were found
            heuristic_info = ""
            if all_matches:
                heuristic_info = f"Heuristic analysis found these potential categories in the text: {', '.join(all_matches)}. Please evaluate these candidates in your decision."
            else:
                heuristic_info = "Heuristic analysis did not find any matching categories in the text."

            category = self.openai.find_category(downloaded, available_categories, self.language, heuristic_info)
            if category:
                # Confirm with user if needed
                confirmed_category = self._confirm_ai_result(
                    "Category", "", category, downloaded.name, downloaded.url, all_matches
                )
                if confirmed_category:
                    # Find the key for this category value
                    category_key = self._find_category_key_by_value(confirmed_category)
                    if category_key:
                        # First standardize the category key
                        standardized_key = self._standardize_category_by_key(category_key)
                        # Save the standardized category key to memory
                        if memory_key not in self.memory:
                            self.memory[memory_key] = {}
                        self.memory[memory_key][downloaded.name] = standardized_key
                        self._save_memory_file(memory_key)
                        # Return the translated category name for this language
                        return self._get_translated_category_name(standardized_key)

        # Ask user directly if AI not available or failed
        print("\n🔍 HEURISTIC ANALYSIS RESULTS FOR CATEGORY:")
        if all_matches:
            print(f"  Found potential matches: {', '.join(all_matches)}")
        else:
            print("  No matches found in product text")

        user_category = self._ask_user_for_value(f"Enter category for product '{downloaded.name}'")
        if user_category:
            # Find the key for this category value
            category_key = self._find_category_key_by_value(user_category)
            if category_key:
                # First standardize the category key
                standardized_key = self._standardize_category_by_key(category_key)
                # Save the standardized category key to memory
                if memory_key not in self.memory:
                    self.memory[memory_key] = {}
                self.memory[memory_key][downloaded.name] = standardized_key
                self._save_memory_file(memory_key)
                # Return the translated category name for this language
                return self._get_translated_category_name(standardized_key)
            else:
                # If category key not found, try old standardization for backward compatibility
                standardized_category = self._standardize_category(user_category)
                if standardized_category:
                    # Save to memory
                    if memory_key not in self.memory:
                        self.memory[memory_key] = {}
                    self.memory[memory_key][downloaded.name] = standardized_category
                    self._save_memory_file(memory_key)
                    return standardized_category

        return ""

    def _get_brand(self, downloaded: DownloadedProduct, for_name_composition: bool = False) -> str:
        """
        Get brand from memory, heuristics, or OpenAI with user confirmation.

        Args:
            downloaded: The product to get the brand for
            for_name_composition: If True, returns empty string for Desaka brand and formats the brand name
        """
        memory_key = MEMORY_KEY_PRODUCT_BRAND_MEMORY.format(language=self.language)
        if memory_key in self.memory:
            brand_memory = self.memory[memory_key]
            if downloaded.name in brand_memory:
                brand = brand_memory[downloaded.name]
                # Handle Desaka brand based on for_name_composition parameter
                if for_name_composition and brand and self._is_desaka_brand(brand):
                    return ""
                return brand if not for_name_composition else self._format_brand_name(brand)

        # Try to find similar keys in memory
        if memory_key in self.memory:
            brand_memory = self.memory[memory_key]
            similar_keys = self._find_similar_memory_keys(downloaded.name, brand_memory, threshold=0.8)

            if similar_keys:
                selected_brand = self._ask_user_for_similar_key_selection("Brand", downloaded.name, similar_keys)
                if selected_brand:
                    # Save to memory with current product name as key
                    self.memory[memory_key][downloaded.name] = selected_brand
                    self._save_memory_file(memory_key)
                    # Handle return based on for_name_composition
                    if for_name_composition and self._is_desaka_brand(selected_brand):
                        return ""
                    return selected_brand if not for_name_composition else self._format_brand_name(selected_brand)

        # Try heuristic extraction
        brand_list = list(self.memory.get(MEMORY_KEY_BRAND_CODE_LIST, {}).keys())

        single_match = None
        all_matches = []
        if brand_list:
            single_match, all_matches = self._heuristic_extraction(downloaded, brand_list)

            # Use OpenAI even if memory is empty or product not found
        if not single_match and self.openai:
            # Include information about heuristic matches in the AI prompt if any were found
            heuristic_info = ""
            if all_matches:
                heuristic_info = f"Heuristic analysis found these potential brands in the text: {', '.join(all_matches)}. Please evaluate these candidates in your decision."
            else:
                heuristic_info = "Heuristic analysis did not find any matching brands in the text."

            brand = self.openai.find_brand(downloaded, brand_list if brand_list else [], self.language, heuristic_info)
            if brand:
                # Confirm with user if needed
                confirmed_brand = self._confirm_ai_result(
                    "Brand", "", brand, downloaded.name, downloaded.url, all_matches
                )
                if confirmed_brand:
                    # Save to memory
                    if memory_key not in self.memory:
                        self.memory[memory_key] = {}
                    self.memory[memory_key][downloaded.name] = confirmed_brand
                    self._save_memory_file(memory_key)
                    # Handle return based on for_name_composition
                    if for_name_composition and self._is_desaka_brand(confirmed_brand):
                        return ""
                    return confirmed_brand if not for_name_composition else self._format_brand_name(confirmed_brand)

        # Ask user directly if AI not available or failed
        print("\n🔍 HEURISTIC ANALYSIS RESULTS FOR BRAND:")
        if all_matches:
            print(f"  Found potential matches: {', '.join(all_matches)}")
        else:
            print("  No matches found in product text")

        user_brand = self._ask_user_for_product_value("Brand", downloaded)
        if user_brand:
            # Save to memory
            if memory_key not in self.memory:
                self.memory[memory_key] = {}
            self.memory[memory_key][downloaded.name] = user_brand
            self._save_memory_file(memory_key)
            # Handle return based on for_name_composition
            if for_name_composition and self._is_desaka_brand(user_brand):
                return ""
            return user_brand if not for_name_composition else self._format_brand_name(user_brand)

        return "" if for_name_composition else "Unknown"  # Default fallback

    def _get_product_brand_for_name(self, downloaded: DownloadedProduct) -> str:
        """Get product brand for name composition from memory, heuristics, or AI."""
        # Use the unified _get_brand method with for_name_composition=True
        return self._get_brand(downloaded, for_name_composition=True)

    def _get_product_type(self, downloaded: DownloadedProduct) -> str:
        """Get product type from memory, heuristics, or AI."""
        memory_key = MEMORY_KEY_PRODUCT_TYPE_MEMORY.format(language=self.language)
        if memory_key in self.memory:
            type_memory = self.memory[memory_key]
            if downloaded.name in type_memory:
                return type_memory[downloaded.name]

        # Try to find similar keys in memory
        if memory_key in self.memory:
            type_memory = self.memory[memory_key]
            similar_keys = self._find_similar_memory_keys(downloaded.name, type_memory, threshold=0.8)

            if similar_keys:
                selected_type = self._ask_user_for_similar_key_selection("Product Type", downloaded.name, similar_keys)
                if selected_type:
                    # Save to memory with current product name as key
                    self.memory[memory_key][downloaded.name] = selected_type
                    self._save_memory_file(memory_key)
                    return selected_type

        # Try heuristic extraction
        # Get all existing product types from memory
        all_types = set()
        if memory_key in self.memory:
            all_types.update(self.memory[memory_key].values())

        type_list = list(all_types)
        single_match = None
        all_matches = []
        if type_list:
            single_match, all_matches = self._heuristic_extraction(downloaded, type_list)

            # Use OpenAI if memory is empty or product not found
        if not single_match and self.openai:
            # Include information about heuristic matches in the AI prompt if any were found
            heuristic_info = ""
            if all_matches:
                heuristic_info = f"Heuristic analysis found these potential product types in the text: {', '.join(all_matches)}. Please evaluate these candidates in your decision."
            else:
                heuristic_info = "Heuristic analysis did not find any matching product types in the text."

            product_type = self.openai.get_product_type(downloaded, self.language, heuristic_info)
            if product_type:
                # Confirm with user if needed
                confirmed_type = self._confirm_ai_result(
                    "Product Type", "", product_type, downloaded.name, downloaded.url, all_matches
                )
                if confirmed_type:
                    # Save to memory
                    if memory_key not in self.memory:
                        self.memory[memory_key] = {}
                    self.memory[memory_key][downloaded.name] = confirmed_type
                    self._save_memory_file(memory_key)
                    return confirmed_type

        # Ask user directly if AI not available or failed
        print("\n🔍 HEURISTIC ANALYSIS RESULTS FOR PRODUCT TYPE:")
        if all_matches:
            print(f"  Found potential matches: {', '.join(all_matches)}")
        else:
            print("  No matches found in product text")

        user_type = self._ask_user_for_product_value("Product Type", downloaded)
        if user_type:
            # Save to memory
            if memory_key not in self.memory:
                self.memory[memory_key] = {}
            self.memory[memory_key][downloaded.name] = user_type
            self._save_memory_file(memory_key)
            return user_type

        return "Product"  # Default fallback

    def _get_product_model(self, downloaded: DownloadedProduct) -> str:
        """Get product model from memory, heuristics, or AI."""
        memory_key = MEMORY_KEY_PRODUCT_MODEL_MEMORY.format(language=self.language)
        if memory_key in self.memory:
            model_memory = self.memory[memory_key]
            if downloaded.name in model_memory:
                return model_memory[downloaded.name]

        # Try to find similar keys in memory
        if memory_key in self.memory:
            model_memory = self.memory[memory_key]
            similar_keys = self._find_similar_memory_keys(downloaded.name, model_memory, threshold=0.8)

            if similar_keys:
                selected_model = self._ask_user_for_similar_key_selection("Product Model", downloaded.name, similar_keys)
                if selected_model:
                    # Save to memory with current product name as key
                    self.memory[memory_key][downloaded.name] = selected_model
                    self._save_memory_file(memory_key)
                    return self._format_model_name(selected_model)

        # Try heuristic extraction
        # Get all existing product models from memory
        all_models = set()
        if memory_key in self.memory:
            all_models.update(self.memory[memory_key].values())

        model_list = list(all_models)
        single_match = None
        all_matches = []
        if model_list:
            single_match, all_matches = self._heuristic_extraction(downloaded, model_list)

            # Use OpenAI if memory is empty or product not found
        if not single_match and self.openai:
            # Include information about heuristic matches in the AI prompt if any were found
            heuristic_info = ""
            if all_matches:
                heuristic_info = f"Heuristic analysis found these potential product models in the text: {', '.join(all_matches)}. Please evaluate these candidates in your decision."
            else:
                heuristic_info = "Heuristic analysis did not find any matching product models in the text."

            product_model = self.openai.get_product_model(downloaded, self.language, heuristic_info)
            if product_model:
                # Confirm with user if needed
                confirmed_model = self._confirm_ai_result(
                    "Product Model", "", product_model, downloaded.name, downloaded.url, all_matches
                )
                if confirmed_model:
                    # Save to memory
                    if memory_key not in self.memory:
                        self.memory[memory_key] = {}
                    self.memory[memory_key][downloaded.name] = confirmed_model
                    self._save_memory_file(memory_key)
                    return self._format_model_name(confirmed_model)

        # Ask user directly if AI not available or failed
        print("\n🔍 HEURISTIC ANALYSIS RESULTS FOR PRODUCT MODEL:")
        if all_matches:
            print(f"  Found potential matches: {', '.join(all_matches)}")
        else:
            print("  No matches found in product text")

        user_model = self._ask_user_for_product_value("Product Model", downloaded)
        if user_model:
            # Save to memory
            if memory_key not in self.memory:
                self.memory[memory_key] = {}
            self.memory[memory_key][downloaded.name] = user_model
            self._save_memory_file(memory_key)
            return self._format_model_name(user_model)

        return "Standard"  # Default fallback

    def _get_product_brand_for_name(self, downloaded: DownloadedProduct) -> str:
        """Get product brand for name composition from memory, heuristics, or AI."""
        # Use the unified _get_brand method with for_name_composition=True
        return self._get_brand(downloaded, for_name_composition=True)

    def _find_category_key_by_value(self, category_value: str) -> Optional[str]:
        """Find category key by its translated value in CategoryNameMemory."""
        category_name_memory_key = MEMORY_KEY_CATEGORY_NAME_MEMORY.format(language=self.language)
        category_name_memory = self.memory.get(category_name_memory_key, {})

        # Find key where value matches the category_value
        for key, value in category_name_memory.items():
            if value == category_value:
                return key

        # If not found, check if the value itself is a key in CategoryList
        category_list = self.memory.get(MEMORY_KEY_CATEGORY_LIST, [])
        if category_value in category_list:
            return category_value

        return None

    def _get_translated_category_name(self, category_key: str) -> str:
        """Get translated category name from CategoryNameMemory for the current language."""
        if not category_key:
            return ""

        # First check if the category key exists in CategoryList (validation)
        category_list = self.memory.get(MEMORY_KEY_CATEGORY_LIST, [])
        if category_key not in category_list:
            logging.warning(f"Category key '{category_key}' not found in CategoryList, returning empty category")
            return ""

        # Get translated name from CategoryNameMemory
        category_name_memory_key = MEMORY_KEY_CATEGORY_NAME_MEMORY.format(language=self.language)
        category_name_memory = self.memory.get(category_name_memory_key, {})

        if category_key in category_name_memory:
            return category_name_memory[category_key]
        else:
            # If translation not found, return the key itself as fallback
            logging.warning(f"Translation for category key '{category_key}' not found in CategoryNameMemory_{self.language}, using key as fallback")
            return category_key

    def _standardize_category_by_key(self, category_key: str) -> str:
        """
        Standardize category using the key from CategoryList.
        This replaces the old _standardize_category method for the new key-based system.
        """
        if not category_key or not category_key.strip():
            return category_key

        # Get CategoryList from memory (it's loaded as list of lines)
        category_list = self.memory.get(MEMORY_KEY_CATEGORY_LIST, [])
        if not category_list:
            logging.warning("CategoryList not found in memory, returning category key as-is")
            return category_key

        # Filter out empty lines and strip whitespace
        category_list = [line.strip() for line in category_list if line.strip()]

        # If the key exists in CategoryList, return it as-is (it's already standardized)
        if category_key in category_list:
            return category_key

        # If not found, try to find a match using the old standardization logic
        # This is for backward compatibility
        return self._standardize_category(category_key)

    def _get_category_ids(self, category: str, downloaded: DownloadedProduct) -> str:
        """Get category IDs from category path using the new key-based system."""
        if not category:
            return ""

        # For the new system, we need to find the category key first
        # If category is already a key from CategoryList, use it directly
        category_list = self.memory.get(MEMORY_KEY_CATEGORY_LIST, [])
        if category in category_list:
            category_key = category
        else:
            # Try to find the key by looking up the value in CategoryNameMemory
            category_key = self._find_category_key_by_value(category)
            if not category_key:
                # Fallback to using the category as-is for backward compatibility
                category_key = category

        # Split by >, reverse order, map to IDs
        category_parts = [part.strip() for part in category_key.split('>')]
        category_parts.reverse()

        category_id_list = self.memory.get(MEMORY_KEY_CATEGORY_ID_LIST, {})
        ids = []

        for part in category_parts:
            if part in category_id_list:
                ids.append(str(category_id_list[part]))
            else:
                # Ask user for missing category ID
                category_id = self._ask_user_for_category_id(part, downloaded)
                if category_id:
                    category_id_list[part] = category_id
                    self._save_memory_file(MEMORY_KEY_CATEGORY_ID_LIST)
                    ids.append(str(category_id))

        return ','.join(ids)

    def _generate_code(self, brand: str, category: str, product_name: str) -> str:
        """Generate complex product code using the new key-based system."""
        # 3 chars BrandCode - readonly, default DES if not found
        # Special handling for Desaka brand - always use DES code
        brand_code_list = self.memory.get(MEMORY_KEY_BRAND_CODE_LIST, {})
        if brand and self._is_desaka_brand(brand):
            brand_code = "DES"  # Desaka brand always uses DES code
        elif brand and brand in brand_code_list:
            brand_code = brand_code_list[brand]
        else:
            brand_code = "DES"  # Default brand code

        # For the new system, we need to find the category key first
        # If category is already a key from CategoryList, use it directly
        category_list = self.memory.get(MEMORY_KEY_CATEGORY_LIST, [])
        if category in category_list:
            category_key = category
        else:
            # Try to find the key by looking up the value in CategoryNameMemory
            category_key = self._find_category_key_by_value(category)
            if not category_key:
                # Fallback to using the category as-is for backward compatibility
                category_key = category

        # 2 digits CategoryCode (first part of category key) - readonly, default 00 if not found
        category_parts = [part.strip() for part in category_key.split('>')]
        first_category = category_parts[0] if category_parts else ""

        category_code_list = self.memory.get(MEMORY_KEY_CATEGORY_CODE_LIST, {})
        if first_category in category_code_list:
            category_code = f"{int(category_code_list[first_category]):02d}"
        else:
            category_code = "00"  # Default category code

        # 2 digits CategorySubCode (second part of category key) - readonly, default 00 if not found
        second_category = category_parts[1] if len(category_parts) > 1 else ""

        category_sub_code_list = self.memory.get(MEMORY_KEY_CATEGORY_SUB_CODE_LIST, {})
        if second_category and second_category in category_sub_code_list:
            sub_code = f"{int(category_sub_code_list[second_category]):02d}"
        else:
            sub_code = "00"  # Default subcategory code

        # 4 digits product index
        base_code = brand_code + category_code + sub_code
        product_index = self._get_next_product_index(base_code, product_name)

        final_code = base_code + f"{product_index:04d}"

        # Remember this code
        self.assigned_codes.add(final_code)

        return final_code

    def _get_next_product_index(self, base_code: str, product_name: str) -> int:
        """Get next available product index efficiently."""
        # First check if this exact product already exists
        for product in self.export_products:
            if (hasattr(product, 'nazev') and product.nazev == product_name and
                hasattr(product, 'kod') and product.kod and
                product.kod.startswith(base_code) and len(product.kod) >= len(base_code) + 4):
                try:
                    return int(product.kod[-4:])
                except (ValueError, TypeError):
                    pass

        # Collect all used indices efficiently using a set
        used_indices = set()

        # Check assigned codes
        for code in self.assigned_codes:
            if code and code.startswith(base_code) and len(code) >= len(base_code) + 4:
                try:
                    index = int(code[-4:])
                    used_indices.add(index)
                except (ValueError, TypeError):
                    pass

        # Check existing export products
        for product in self.export_products:
            if (hasattr(product, 'kod') and product.kod and
                product.kod.startswith(base_code) and len(product.kod) >= len(base_code) + 4):
                try:
                    index = int(product.kod[-4:])
                    used_indices.add(index)
                except (ValueError, TypeError):
                    pass

        # Find first unused index starting from 1
        next_index = 1
        while next_index in used_indices:
            next_index += 1

        return next_index

    def _ask_user_for_category_id(self, category: str, downloaded: DownloadedProduct) -> Optional[int]:
        """Ask user for category ID."""
        try:
            print("\n" + "=" * 80)
            print("👤 USER INPUT REQUIRED FOR: Category ID")
            print("=" * 80)
            print(f"📦 Product: {downloaded.name}")
            if downloaded.url:
                print(f"🔗 URL: {downloaded.url}")
            print("-" * 80)
            response = input(f"✏️  Enter category ID for '{category}': ")
            return int(response.strip())
        except (ValueError, KeyboardInterrupt):
            return None

    def _ask_user_for_brand_code(self, brand: str) -> Optional[str]:
        """Ask user for brand code."""
        try:
            response = input(f"Enter 3-character brand code for '{brand}': ")
            code = response.strip().upper()
            if len(code) == 3:
                return code
        except KeyboardInterrupt:
            pass
        return None

    def _ask_user_for_category_code(self, category: str) -> Optional[int]:
        """Ask user for category code."""
        try:
            response = input(f"Enter category code (number) for '{category}': ")
            return int(response.strip())
        except (ValueError, KeyboardInterrupt):
            return None

    def _ask_user_for_category_mapping(self, category: str, platform: str, downloaded: DownloadedProduct) -> Optional[str]:
        """Ask user for category mapping."""
        try:
            print("\n" + "=" * 80)
            print(f"👤 USER INPUT REQUIRED FOR: {platform} Category Mapping")
            print("=" * 80)
            print(f"📦 Product: {downloaded.name}")
            if downloaded.url:
                print(f"🔗 URL: {downloaded.url}")
            print("-" * 80)
            print(f"📄 Category to map: {category}")
            print("=" * 80)
            response = input(f"✏️  Enter {platform} category mapping for '{category}': ")
            return response.strip()
        except KeyboardInterrupt:
            return None

    def _confirm_ai_result(self, property_name: str, current_value: str, ai_suggestion: str, product_name: str, product_url: str = "", heuristic_matches: List[str] = None) -> str:
        """Confirm AI result with user or return suggestion if auto-confirm is enabled."""
        if self.confirm_ai_results:
            return ai_suggestion.strip() if ai_suggestion else ""

        try:
            # Create a more readable display format
            print("\n" + "=" * 80)
            print(f"🤖 AI SUGGESTION FOR: {property_name}")
            print("=" * 80)
            print(f"📦 Product: {product_name}")
            if product_url:
                print(f"🔗 URL: {product_url}")
            print("-" * 80)

            # Display heuristic results if available
            print(f"🔍 HEURISTIC ANALYSIS RESULTS:")
            if heuristic_matches:
                print(f"   Found potential {property_name.lower()} candidates in product text:")
                for match in heuristic_matches:
                    print(f"   • {match}")
            else:
                print(f"   No potential {property_name.lower()} matches found in product text")
            print("-" * 80)

            # Display current value
            if current_value:
                print(f"📄 Current Value:")
                if property_name == "Description" and "<" in current_value:
                    # Format HTML for better readability (display only)
                    formatted_current = self._format_html_for_display(current_value)
                    print(f"   {formatted_current}")
                else:
                    print(f"   {current_value}")
            else:
                print(f"📄 Current Value: (empty)")

            print("-" * 80)

            # Display AI suggestion
            print(f"🎯 AI Suggests:")
            if property_name == "Description" and ai_suggestion and "<" in ai_suggestion:
                # Format HTML for better readability (display only)
                formatted_suggestion = self._format_html_for_display(ai_suggestion)
                print(f"   {formatted_suggestion}")
                print("-----------")
                print(f" {ai_suggestion} ")
            else:
                print(f"   {ai_suggestion}")

            print("=" * 80)
            response = input(f"✅ Press Enter to confirm AI suggestion or type new value: ").strip()
            return response if response else ai_suggestion.strip() if ai_suggestion else ""
        except KeyboardInterrupt:
            return ai_suggestion.strip() if ai_suggestion else ""

    def _ask_user_for_product_value(self, property_name: str, downloaded: DownloadedProduct, current_value: str = "") -> str:
        """Ask user for product property value with detailed product information display."""
        try:
            # Create a more readable display format similar to AI confirmation
            print("\n" + "=" * 80)
            print(f"👤 USER INPUT REQUIRED FOR: {property_name}")
            print("=" * 80)
            print(f"📦 Product: {downloaded.name}")
            if downloaded.url:
                print(f"🔗 URL: {downloaded.url}")
            print("-" * 80)

            # Display current product properties for context
            print(f"📄 Current Product Properties:")
            if downloaded.description:
                if property_name == "Description" and "<" in downloaded.description:
                    # Format HTML for better readability (display only)
                    formatted_desc = self._format_html_for_display(downloaded.description)
                    print(f"   Description: {formatted_desc}")
                else:
                    desc_preview = downloaded.description[:200] + "..." if len(downloaded.description) > 200 else downloaded.description
                    print(f"   Description: {desc_preview}")
            else:
                print(f"   Description: (empty)")

            if downloaded.short_description:
                print(f"   Short Description: {downloaded.short_description}")
            else:
                print(f"   Short Description: (empty)")

            # Display current value if provided
            if current_value:
                print(f"   Current {property_name}: {current_value}")
            else:
                print(f"   Current {property_name}: (empty)")

            print("=" * 80)
            response = input(f"✏️  Please enter {property_name}: ").strip()
            return response if response else ""
        except KeyboardInterrupt:
            return ""

    def _ask_user_for_variant_value(self, property_name: str, original_value: str, downloaded: DownloadedProduct, context_info: str = "") -> str:
        """Ask user for variant property value with context information display."""
        try:
            # Create a more readable display format similar to AI confirmation
            print("\n" + "=" * 80)
            print(f"👤 USER INPUT REQUIRED FOR: {property_name}")
            print("=" * 80)
            print(f"📦 Product: {downloaded.name}")
            if downloaded.url:
                print(f"🔗 URL: {downloaded.url}")
            print("-" * 80)
            if context_info:
                print(f"📄 Context: {context_info}")
                print("-" * 80)

            # Display original value
            print(f"📄 Original Value: {original_value}")

            print("=" * 80)
            response = input(f"✏️  Please enter standardized {property_name}: ").strip()
            return response if response else ""
        except KeyboardInterrupt:
            return ""

    def _save_memory_file(self, memory_key: str):
        """Save memory file using memory manager."""
        from unifierlib.memory_manager import save_memory_file
        # Get default memory directory from script location
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        memory_dir = os.path.join(script_dir, "Memory")
        save_memory_file(memory_key, self.memory.get(memory_key, {}), self.language, memory_dir)

    def _get_description(self, downloaded: DownloadedProduct) -> str:
        """Get description from memory or OpenAI translation/validation."""
        memory_key = f"DescMemory_{self.language}"
        if memory_key in self.memory:
            desc_memory = self.memory[memory_key]
            if downloaded.name in desc_memory:
                return desc_memory[downloaded.name]

        # Try to find similar keys in memory
        if memory_key in self.memory:
            desc_memory = self.memory[memory_key]
            similar_keys = self._find_similar_memory_keys(downloaded.name, desc_memory, threshold=0.8)

            if similar_keys:
                selected_desc = self._ask_user_for_similar_key_selection("Description", downloaded.name, similar_keys)
                if selected_desc:
                    # Save to memory with current product name as key
                    self.memory[memory_key][downloaded.name] = selected_desc
                    self._save_memory_file(memory_key)
                    return selected_desc

        # Use OpenAI for translation and validation (not generation)
        if self.openai and downloaded.description:
            description = self.openai.translate_and_validate_description(downloaded.description, self.language)
            if description:
                # Confirm with user if needed
                confirmed_description = self._confirm_ai_result(
                    "Description", downloaded.description, description, downloaded.name, downloaded.url
                )
                if confirmed_description:
                    # Save to memory
                    if memory_key not in self.memory:
                        self.memory[memory_key] = {}
                    self.memory[memory_key][downloaded.name] = confirmed_description
                    self._save_memory_file(memory_key)
                    return confirmed_description

        # Ask user directly if AI not available or failed
        if not downloaded.description:
            user_description = self._ask_user_for_product_value("Description", downloaded)
            if user_description:
                # Save to memory
                if memory_key not in self.memory:
                    self.memory[memory_key] = {}
                self.memory[memory_key][downloaded.name] = user_description
                self._save_memory_file(memory_key)
                return user_description

        return downloaded.description

    def _get_category_mapping(self, category: str, platform: str, downloaded: DownloadedProduct) -> str:
        """Get category mapping for specific platform using AI or user input."""
        memory_key = f"CategoryMapping{platform}_{self.language}"
        if memory_key in self.memory:
            mapping = self.memory[memory_key]
            if category in mapping:
                return mapping[category]

        # Use OpenAI with memory content
        if self.openai:
            # Get current memory content to include in prompt
            memory_content = self.memory.get(memory_key, {})
            suggested_mapping = self.openai.suggest_category_mapping(category, platform, self.language, memory_content)
            if suggested_mapping:
                # Confirm with user if needed
                confirmed_mapping = self._confirm_ai_result(
                    f"{platform} Category Mapping", "", suggested_mapping, downloaded.name, downloaded.url
                )
                if confirmed_mapping:
                    # Save to memory only after confirmation
                    if memory_key not in self.memory:
                        self.memory[memory_key] = {}
                    self.memory[memory_key][category] = confirmed_mapping
                    self._save_memory_file(memory_key)
                    return confirmed_mapping

        # Ask user directly if AI not available or failed
        mapped_category = self._ask_user_for_category_mapping(category, platform, downloaded)
        if mapped_category:
            if memory_key not in self.memory:
                self.memory[memory_key] = {}
            self.memory[memory_key][category] = mapped_category
            self._save_memory_file(memory_key)
            return mapped_category

        return ""

    def _get_google_keywords(self, downloaded: DownloadedProduct) -> str:
        """Get Google keywords from memory or OpenAI with confirmation."""
        memory_key = f"KeywordsGoogle_{self.language}"
        if memory_key in self.memory:
            keywords_memory = self.memory[memory_key]
            if downloaded.name in keywords_memory:
                return keywords_memory[downloaded.name]

        # Try to find similar keys in memory
        if memory_key in self.memory:
            keywords_memory = self.memory[memory_key]
            similar_keys = self._find_similar_memory_keys(downloaded.name, keywords_memory, threshold=0.8)

            if similar_keys:
                selected_keywords = self._ask_user_for_similar_key_selection("Google Keywords", downloaded.name, similar_keys)
                if selected_keywords:
                    # Save to memory with current product name as key
                    self.memory[memory_key][downloaded.name] = selected_keywords
                    self._save_memory_file(memory_key)
                    return selected_keywords

        # Use OpenAI with memory content
        if self.openai:
            # Get current memory content to include in prompt
            memory_content = self.memory.get(memory_key, {})
            keywords = self.openai.generate_google_keywords(downloaded, memory_content, self.language)
            if keywords:
                # Confirm with user if needed
                confirmed_keywords = self._confirm_ai_result(
                    "Google Keywords", "", keywords, downloaded.name, downloaded.url
                )
                if confirmed_keywords:
                    # Save to memory only after confirmation
                    if memory_key not in self.memory:
                        self.memory[memory_key] = {}
                    self.memory[memory_key][downloaded.name] = confirmed_keywords
                    self._save_memory_file(memory_key)
                    return confirmed_keywords

        # Ask user directly if AI not available or failed
        user_keywords = self._ask_user_for_product_value("Google Keywords", downloaded)
        if user_keywords:
            # Save to memory
            if memory_key not in self.memory:
                self.memory[memory_key] = {}
            self.memory[memory_key][downloaded.name] = user_keywords
            self._save_memory_file(memory_key)
            return user_keywords

        return ""

    def _get_product_name(self, downloaded: DownloadedProduct) -> str:
        """Get product name composed of type, brand, and model from memory or AI."""
        memory_key = MEMORY_KEY_NAME_MEMORY.format(language=self.language)
        if memory_key in self.memory:
            name_memory = self.memory[memory_key]
            if downloaded.name in name_memory:
                return name_memory[downloaded.name]

        # Try to find similar keys in memory
        if memory_key in self.memory:
            name_memory = self.memory[memory_key]
            similar_keys = self._find_similar_memory_keys(downloaded.name, name_memory, threshold=0.8)

            if similar_keys:
                selected_name = self._ask_user_for_similar_key_selection("Product Name", downloaded.name, similar_keys)
                if selected_name:
                    # Save to memory with current product name as key
                    self.memory[memory_key][downloaded.name] = selected_name
                    self._save_memory_file(memory_key)
                    return selected_name

        # Get individual components
        product_type = self._get_product_type(downloaded)
        product_brand = self._get_brand(downloaded, for_name_composition=True)  # Use unified method with parameter
        product_model = self._get_product_model(downloaded)

        # Format: type brand model (skip brand if empty)
        if product_brand and product_brand.strip():
            formatted_name = f"{product_type} {product_brand} {product_model}".strip()
        else:
            formatted_name = f"{product_type} {product_model}".strip()

        # Save to memory
        if memory_key not in self.memory:
            self.memory[memory_key] = {}
        self.memory[memory_key][downloaded.name] = formatted_name
        self._save_memory_file(memory_key)

        return formatted_name

    def _format_brand_name(self, brand: str) -> str:
        """Format brand name with proper capitalization."""
        words = brand.split()
        formatted_words = []
        for word in words:
            if word.isupper() and len(word) <= 4:  # Acronyms stay uppercase
                formatted_words.append(word)
            else:
                formatted_words.append(word.capitalize())
        return ' '.join(formatted_words)

    def _format_model_name(self, model: str) -> str:
        """Format model name with proper capitalization."""
        words = model.split()
        formatted_words = []
        for word in words:
            if word.isupper() and len(word) <= 4:  # Acronyms stay uppercase
                formatted_words.append(word)
            else:
                formatted_words.append(word.capitalize())
        return ' '.join(formatted_words)

    def _is_desaka_brand(self, brand: str) -> bool:
        """Check if brand is Desaka (including variations like 'Desaka s.r.o.')."""
        if not brand:
            return False

        # Normalize brand name for comparison
        normalized_brand = brand.strip().lower()

        # Check for Desaka variations
        desaka_patterns = [
            'desaka',
            'desaka s.r.o.',
            'desaka s.r.o',
            'desaka spol. s r.o.',
            'desaka spol. s r.o'
        ]

        return normalized_brand in desaka_patterns

    def _get_prices(self, downloaded: DownloadedProduct) -> tuple:
        """Get price and price_standard from variants."""
        if not downloaded.variants:
            return "0", "0"

        basic_prices = []
        for variant in downloaded.variants:
            if hasattr(variant, 'basic_price') and variant.basic_price:
                try:
                    basic_prices.append(float(variant.basic_price))
                except (ValueError, TypeError):
                    pass

        if not basic_prices:
            return "0", "0"

        max_price = max(basic_prices)

        # Get VAT rate from ExportProduct (default 21%)
        vat_rate = 0.21  # Default VAT rate
        export_product_data = self.memory.get('ExportProduct', {})
        if 'dph' in export_product_data:
            try:
                vat_rate = float(export_product_data['dph']) / 100
            except (ValueError, TypeError):
                pass

        # price = without VAT, price_standard = with VAT
        price_without_vat = max_price / (1 + vat_rate)
        price_with_vat = max_price

        return f"{price_without_vat:.2f}", f"{price_with_vat:.2f}"

    def _get_short_description(self, downloaded: DownloadedProduct) -> str:
        """Get short description from memory or OpenAI translation/validation."""
        memory_key = f"ShortDescMemory_{self.language}"
        if memory_key in self.memory:
            shortdesc_memory = self.memory[memory_key]
            if downloaded.name in shortdesc_memory:
                return shortdesc_memory[downloaded.name]

        # Try to find similar keys in memory
        if memory_key in self.memory:
            shortdesc_memory = self.memory[memory_key]
            similar_keys = self._find_similar_memory_keys(downloaded.name, shortdesc_memory, threshold=0.8)

            if similar_keys:
                selected_shortdesc = self._ask_user_for_similar_key_selection("Short Description", downloaded.name, similar_keys)
                if selected_shortdesc:
                    # Save to memory with current product name as key
                    self.memory[memory_key][downloaded.name] = selected_shortdesc
                    self._save_memory_file(memory_key)
                    return selected_shortdesc

        # Use OpenAI for translation and validation (or generation from description)
        if self.openai:
            shortdesc = self.openai.translate_and_validate_short_description(downloaded.short_description, self.language, downloaded.description)
            if shortdesc:
                # Determine current value for confirmation display
                current_value = downloaded.short_description if downloaded.short_description else "(generated from description)"

                # Confirm with user if needed
                confirmed_shortdesc = self._confirm_ai_result(
                    "Short Description", current_value, shortdesc, downloaded.name, downloaded.url
                )
                if confirmed_shortdesc:
                    # Save to memory
                    if memory_key not in self.memory:
                        self.memory[memory_key] = {}
                    self.memory[memory_key][downloaded.name] = confirmed_shortdesc
                    self._save_memory_file(memory_key)
                    return confirmed_shortdesc

        # Ask user directly if AI not available or failed
        # Try to ask user even if short description is empty (they can generate it manually)
        user_shortdesc = self._ask_user_for_product_value("Short Description", downloaded)
        if user_shortdesc:
            # Save to memory
            if memory_key not in self.memory:
                self.memory[memory_key] = {}
            self.memory[memory_key][downloaded.name] = user_shortdesc
            self._save_memory_file(memory_key)
            return user_shortdesc

        return downloaded.short_description[:150] if downloaded.short_description else ""

    def _generate_variant_code(self, base_code: str, downloaded: DownloadedProduct) -> str:
        """Generate variant code: code + '-' + 2 digits."""
        if not downloaded.variants:
            return base_code + "-01"

        # Find existing variant with same key_value_pairs
        existing_variants = self.memory.get('ExistingProductVariants', [])

        for variant in downloaded.variants:
            if hasattr(variant, 'key_value_pairs'):
                for existing_variant in existing_variants:
                    if (hasattr(existing_variant, 'kod') and existing_variant.kod and
                        existing_variant.kod.startswith(base_code) and
                        hasattr(existing_variant, 'key_value_pairs') and
                        existing_variant.key_value_pairs == variant.key_value_pairs):
                        return existing_variant.kod

        # Find next available variant index
        used_indices = []
        for existing_variant in existing_variants:
            if (hasattr(existing_variant, 'kod') and existing_variant.kod and
                existing_variant.kod.startswith(base_code + "-")):
                try:
                    index = int(existing_variant.kod[-2:])
                    used_indices.append(index)
                except (ValueError, TypeError):
                    pass

        # Find first unused index
        used_indices.sort()
        next_index = 1
        for index in used_indices:
            if index == next_index:
                next_index += 1
            else:
                break

        return base_code + f"-{next_index:02d}"

    def _generate_variant_code_for_variant(self, base_code: str, variant: Variant, variant_index: int) -> str:
        """Generate variant code for a specific variant: base_code + '-' + 2 digits."""
        if not base_code:
            return f"VAR-{variant_index:02d}"

        # Check if this exact variant already exists
        existing_variants = self.memory.get('ExistingProductVariants', [])

        for existing_variant in existing_variants:
            if (hasattr(existing_variant, 'variantcode') and existing_variant.variantcode and
                existing_variant.variantcode.startswith(base_code) and
                hasattr(existing_variant, 'key_value_pairs') and
                existing_variant.key_value_pairs == variant.key_value_pairs):
                return existing_variant.variantcode

        # Find next available variant index
        used_indices = set()
        for existing_variant in existing_variants:
            if (hasattr(existing_variant, 'variantcode') and existing_variant.variantcode and
                existing_variant.variantcode.startswith(base_code + "-")):
                try:
                    index = int(existing_variant.variantcode[-2:])
                    used_indices.add(index)
                except (ValueError, TypeError):
                    pass

        # Check assigned variant codes
        for code in self.assigned_variant_codes:
            if code and code.startswith(base_code + "-"):
                try:
                    index = int(code[-2:])
                    used_indices.add(index)
                except (ValueError, TypeError):
                    pass

        # Find first unused index starting from 1
        next_index = 1
        while next_index in used_indices:
            next_index += 1

        variant_code = base_code + f"-{next_index:02d}"
        self.assigned_variant_codes.add(variant_code)
        return variant_code

    def _process_variants(self, downloaded: DownloadedProduct, base_code: str = "") -> List[Variant]:
        """
        Process variants with standardization and variant code generation.
        Each downloaded variant becomes one RepairedProduct variant with up to 3 key_value_pairs.
        """
        if not downloaded.variants:
            return []

        processed_variants = []

        for variant_index, variant in enumerate(downloaded.variants):
            if hasattr(variant, 'key_value_pairs') and variant.key_value_pairs:
                # Handle both dict and list formats for key_value_pairs
                pairs = []
                if isinstance(variant.key_value_pairs, dict):
                    pairs = list(variant.key_value_pairs.items())
                elif isinstance(variant.key_value_pairs, list):
                    # Convert list to pairs if it's a list of key-value items
                    for item in variant.key_value_pairs:
                        if isinstance(item, dict) and len(item) == 1:
                            pairs.extend(list(item.items()))
                        elif isinstance(item, (list, tuple)) and len(item) == 2:
                            pairs.append((item[0], item[1]))
                else:
                    logging.warning(f"Unexpected key_value_pairs format: {type(variant.key_value_pairs)}")
                    continue

                # Create ONE Variant object with up to 3 key_value_pairs
                processed_variant = Variant()

                # Limit to maximum 3 pairs and standardize them
                limited_pairs = pairs[:3]  # Take only first 3 pairs
                standardized_pairs = {}

                for key, value in limited_pairs:
                    standardized_key = self._standardize_variant_name(str(key).strip(), downloaded)
                    standardized_value = self._standardize_variant_value(str(value).strip(), downloaded)
                    standardized_pairs[standardized_key] = standardized_value

                processed_variant.key_value_pairs = standardized_pairs

                # Copy price information from original variant
                processed_variant.current_price = getattr(variant, 'current_price', 0.0) or 0.0
                processed_variant.basic_price = getattr(variant, 'basic_price', 0.0) or 0.0
                processed_variant.stock_status = self._standardize_stock_status(getattr(variant, 'stock_status', ''))

                # Generate variant code for this specific variant
                if base_code:
                    processed_variant.variantcode = self._generate_variant_code_for_variant(base_code, processed_variant, variant_index + 1)

                processed_variants.append(processed_variant)

        return processed_variants

    def _standardize_variant_name(self, name: str, downloaded: DownloadedProduct) -> str:
        """Standardize variant name using memory or OpenAI with confirmation."""
        memory_key = f"VariantNameMemory_{self.language}"
        if memory_key in self.memory:
            name_memory = self.memory[memory_key]
            if name in name_memory:
                return name_memory[name]

        # Try to find similar keys in memory
        if memory_key in self.memory:
            name_memory = self.memory[memory_key]
            similar_keys = self._find_similar_memory_keys(name, name_memory, threshold=0.8)

            if similar_keys:
                selected_variant_name = self._ask_user_for_similar_key_selection("Variant Name", name, similar_keys)
                if selected_variant_name:
                    # Save to memory with current variant name as key
                    self.memory[memory_key][name] = selected_variant_name
                    self._save_memory_file(memory_key)
                    return selected_variant_name

        # Use OpenAI with memory content
        if self.openai:
            # Get current memory content to include in prompt
            memory_content = self.memory.get(memory_key, {})
            standardized = self.openai.standardize_variant_name(name, self.language, memory_content)
            if standardized:
                # Confirm with user if needed
                confirmed_name = self._confirm_ai_result(
                    "Variant Name", name, standardized, downloaded.name, downloaded.url
                )
                if confirmed_name:
                    # Save to memory only after confirmation
                    if memory_key not in self.memory:
                        self.memory[memory_key] = {}
                    self.memory[memory_key][name] = confirmed_name
                    self._save_memory_file(memory_key)
                    return confirmed_name

        # Ask user directly if AI not available or failed
        user_name = self._ask_user_for_variant_value("Variant Name", name, downloaded, f"Variant name: {name}")
        if user_name:
            # Save to memory
            if memory_key not in self.memory:
                self.memory[memory_key] = {}
            self.memory[memory_key][name] = user_name
            self._save_memory_file(memory_key)
            return user_name

        return name

    def _standardize_variant_value(self, value: str, downloaded: DownloadedProduct) -> str:
        """Standardize variant value using memory or OpenAI with confirmation."""
        memory_key = f"VariantValueMemory_{self.language}"
        if memory_key in self.memory:
            value_memory = self.memory[memory_key]
            if value in value_memory:
                return value_memory[value]

        # Try to find similar keys in memory
        if memory_key in self.memory:
            value_memory = self.memory[memory_key]
            similar_keys = self._find_similar_memory_keys(value, value_memory, threshold=0.8)

            if similar_keys:
                selected_variant_value = self._ask_user_for_similar_key_selection("Variant Value", value, similar_keys)
                if selected_variant_value:
                    # Save to memory with current variant value as key
                    self.memory[memory_key][value] = selected_variant_value
                    self._save_memory_file(memory_key)
                    return selected_variant_value

        # Use OpenAI with memory content
        if self.openai:
            # Get current memory content to include in prompt
            memory_content = self.memory.get(memory_key, {})
            standardized = self.openai.standardize_variant_value(value, self.language, memory_content)
            if standardized:
                # Confirm with user if needed
                confirmed_value = self._confirm_ai_result(
                    "Variant Value", value, standardized, downloaded.name, downloaded.url
                )
                if confirmed_value:
                    # Save to memory only after confirmation
                    if memory_key not in self.memory:
                        self.memory[memory_key] = {}
                    self.memory[memory_key][value] = confirmed_value
                    self._save_memory_file(memory_key)
                    return confirmed_value

        # Ask user directly if AI not available or failed
        user_value = self._ask_user_for_variant_value("Variant Value", value, downloaded, f"Variant value: {value}")
        if user_value:
            # Save to memory
            if memory_key not in self.memory:
                self.memory[memory_key] = {}
            self.memory[memory_key][value] = user_value
            self._save_memory_file(memory_key)
            return user_value

        return value

    def _get_zbozi_keywords(self, downloaded: DownloadedProduct) -> str:
        """Get Zbozi keywords from memory or OpenAI with confirmation."""
        memory_key = f"KeywordsZbozi_{self.language}"
        if memory_key in self.memory:
            keywords_memory = self.memory[memory_key]
            if downloaded.name in keywords_memory:
                return keywords_memory[downloaded.name]

        # Try to find similar keys in memory
        if memory_key in self.memory:
            keywords_memory = self.memory[memory_key]
            similar_keys = self._find_similar_memory_keys(downloaded.name, keywords_memory, threshold=0.8)

            if similar_keys:
                selected_keywords = self._ask_user_for_similar_key_selection("Zbozi Keywords", downloaded.name, similar_keys)
                if selected_keywords:
                    # Save to memory with current product name as key
                    self.memory[memory_key][downloaded.name] = selected_keywords
                    self._save_memory_file(memory_key)
                    return selected_keywords

        # Use OpenAI with memory content
        if self.openai:
            # Get current memory content to include in prompt
            memory_content = self.memory.get(memory_key, {})
            keywords = self.openai.generate_zbozi_keywords(downloaded, memory_content, self.language)
            if keywords:
                # Confirm with user if needed
                confirmed_keywords = self._confirm_ai_result(
                    "Zbozi Keywords", "", keywords, downloaded.name, downloaded.url
                )
                if confirmed_keywords:
                    # Save to memory only after confirmation
                    if memory_key not in self.memory:
                        self.memory[memory_key] = {}
                    self.memory[memory_key][downloaded.name] = confirmed_keywords
                    self._save_memory_file(memory_key)
                    return confirmed_keywords

        # Ask user directly if AI not available or failed
        user_keywords = self._ask_user_for_product_value("Zbozi Keywords", downloaded)
        if user_keywords:
            # Save to memory
            if memory_key not in self.memory:
                self.memory[memory_key] = {}
            self.memory[memory_key][downloaded.name] = user_keywords
            self._save_memory_file(memory_key)
            return user_keywords

        return ""

    def repaired_to_export_product(self, repaired: RepairedProduct) -> List[ExportProduct]:
        """
        Convert RepairedProduct to array of ExportProducts (1 main + variants).
        Implements complete 96-column specification.

        Args:
            repaired (RepairedProduct): Source repaired product

        Returns:
            List[ExportProduct]: Array with ExportMainProduct first, then ExportProductVariants
        """
        export_products = []

        # Create main product
        main_product = self._create_main_export_product_complete(repaired)
        export_products.append(main_product)

        # Create variant products
        if repaired.Variants:
            for i, variant in enumerate(repaired.Variants):
                variant_product = self._create_variant_export_product_complete(repaired, variant, i + 1)
                export_products.append(variant_product)

        return export_products

    def _create_main_export_product(self, repaired: RepairedProduct) -> ExportMainProduct:
        """Create main export product from repaired product."""
        main_product = ExportMainProduct()

        # Basic product information - map all available fields
        main_product.nazev = repaired.name
        main_product.kod = repaired.code
        main_product.popis = repaired.desc
        main_product.popis_strucny = repaired.shortdesc
        main_product.vyrobce = "" if repaired.brand and self._is_desaka_brand(repaired.brand) else repaired.brand
        main_product.kategorie_id = repaired.category_ids

        # Pricing information
        main_product.cena = float(repaired.price) if repaired.price else 0.0
        main_product.cena_bezna = float(repaired.price_standard) if repaired.price_standard else main_product.cena

        # Feed-specific categories and keywords
        main_product.glami_kategorie = repaired.glami_category
        main_product.google_kategorie = repaired.google_category
        main_product.heurekacz_kategorie = repaired.heureka_category
        main_product.zbozicz_kategorie = repaired.zbozi_category
        main_product.google_stitek_0 = repaired.google_keywords
        main_product.zbozicz_stitek_0 = repaired.zbozi_keywords

        # Apply default values from memory for fields not set from repaired product
        self._apply_default_export_values(main_product)

        return main_product

    def _create_variant_export_product(self, repaired: RepairedProduct, variant: Any, variant_index: int) -> ExportProductVariant:
        """Create variant export product from repaired product and variant."""
        variant_product = ExportProductVariant()

        # Basic identification - only set what's different from main product
        variant_product.varianta_id = f"{repaired.code}-V{variant_index:02d}"
        variant_product.kod = f"{repaired.code}-V{variant_index:02d}"
        variant_product.ean = getattr(variant, 'ean', '') if hasattr(variant, 'ean') else ''
        variant_product.cena = float(getattr(variant, 'price', repaired.price)) if getattr(variant, 'price', repaired.price) else 0.0
        variant_product.cena_bezna = float(getattr(variant, 'price_standard', repaired.price_standard)) if getattr(variant, 'price_standard', repaired.price_standard) else variant_product.cena

        # Variant-specific properties
        if hasattr(variant, 'key_value_pairs') and variant.key_value_pairs:
            pairs = list(variant.key_value_pairs.items())
            if len(pairs) > 0:
                variant_product.varianta1_nazev = pairs[0][0]
                variant_product.varianta1_hodnota = pairs[0][1]
            if len(pairs) > 1:
                variant_product.varianta2_nazev = pairs[1][0]
                variant_product.varianta2_hodnota = pairs[1][1]
            if len(pairs) > 2:
                variant_product.varianta3_nazev = pairs[2][0]
                variant_product.varianta3_hodnota = pairs[2][1]

        # Apply default values from memory for variant-specific fields
        self._apply_default_export_values(variant_product, is_variant=True)

        return variant_product

    def _apply_default_export_values(self, export_product: ExportProduct, is_variant: bool = False):
        """Apply default values from DefaultExportProductValues memory."""
        default_values = self.memory.get(MEMORY_KEY_DEFAULT_EXPORT_PRODUCT_VALUES, [])

        for default_row in default_values:
            if 'key' in default_row:
                key = default_row['key']

                # Choose value based on product type
                if is_variant and 'variantvalue' in default_row:
                    value_to_use = default_row['variantvalue']
                elif 'mainvalue' in default_row:
                    value_to_use = default_row['mainvalue']
                else:
                    continue

                # Only set if the property exists and is currently empty/default
                if hasattr(export_product, key):
                    current_value = getattr(export_product, key)

                    # For variants, don't override values that are already set to "#" or "."
                    if is_variant and current_value in ["#", "."]:
                        continue

                    # Only set if empty/default
                    if not current_value or current_value == 0 or current_value == "":
                        # Convert value to appropriate type
                        if isinstance(current_value, int):
                            try:
                                if value_to_use not in ["#", "."]:
                                    setattr(export_product, key, int(value_to_use))
                            except (ValueError, TypeError):
                                pass
                        elif isinstance(current_value, float):
                            try:
                                if value_to_use not in ["#", "."]:
                                    setattr(export_product, key, float(value_to_use))
                            except (ValueError, TypeError):
                                pass
                        else:
                            setattr(export_product, key, str(value_to_use))

    def _create_main_export_product_complete(self, repaired: RepairedProduct) -> ExportMainProduct:
        """Create main export product with complete 96-column specification."""
        main_product = ExportMainProduct()

        # 1. typ - fixed value "produkt"
        main_product.typ = "produkt"

        # 2-7. varianta1-3 nazev/hodnota - fixed "#" for main product
        main_product.varianta1_nazev = "#"
        main_product.varianta1_hodnota = "#"
        main_product.varianta2_nazev = "#"
        main_product.varianta2_hodnota = "#"
        main_product.varianta3_nazev = "#"
        main_product.varianta3_hodnota = "#"

        # 8. varianta_stejne - fixed "#" for main product
        main_product.varianta_stejne = "#"

        # 9. zobrazit - "1" if price > 0, else "0"
        price_value = float(repaired.price) if repaired.price else 0.0
        main_product.zobrazit = "1" if price_value > 0 else "0"

        # 10. archiv - fixed "0"
        main_product.archiv = "0"

        # 11. kod - from RepairedProduct.code
        main_product.kod = repaired.code

        # 12. kod_vyrobku - empty (not in input)
        main_product.kod_vyrobku = ""

        # 13-14. ean, isbn - empty
        main_product.ean = ""
        main_product.isbn = ""

        # 15. nazev - from RepairedProduct.name
        main_product.nazev = repaired.name

        # 16. privlastek - empty
        main_product.privlastek = ""

        # 17. vyrobce - from RepairedProduct.brand (empty if Desaka)
        main_product.vyrobce = "" if repaired.brand and self._is_desaka_brand(repaired.brand) else repaired.brand

        # 18-19. cena, cena_bezna - from RepairedProduct
        main_product.cena = price_value
        main_product.cena_bezna = float(repaired.price_standard) if repaired.price_standard else price_value

        # 20-21. cena_nakupni, recyklacni_poplatek - empty
        main_product.cena_nakupni = ""
        main_product.recyklacni_poplatek = ""

        # 22. dph - fixed "21"
        main_product.dph = "21"

        # 23-25. sleva fields - empty
        main_product.sleva = ""
        main_product.sleva_od = ""
        main_product.sleva_do = ""

        # 26-27. popis, popis_strucny - from RepairedProduct
        main_product.popis = repaired.desc
        main_product.popis_strucny = repaired.shortdesc

        # 28-29. kosik, home
        main_product.kosik = "1"
        main_product.home = "0"

        # 30. dostupnost - "#" if has variants, "0" if no variants
        main_product.dostupnost = "#" if repaired.Variants else "0"

        # 31. doprava_zdarma - "0"
        main_product.doprava_zdarma = "0"

        # 32-33. dodaci_doba, dodaci_doba_auto
        main_product.dodaci_doba = "#"
        main_product.dodaci_doba_auto = "1"

        # 34-35. sklad, na_sklade - same as dostupnost
        main_product.sklad = "#" if repaired.Variants else "0"
        main_product.na_sklade = "#" if repaired.Variants else "0"

        # 36-37. hmotnost, delka - empty
        main_product.hmotnost = ""
        main_product.delka = ""

        # 38-42. jednotka and odber fields
        main_product.jednotka = "ks"
        main_product.odber_po = "1"
        main_product.odber_min = "1"
        main_product.odber_max = ""
        main_product.pocet = "1"

        # 43. zaruka - empty
        main_product.zaruka = ""

        # 44-45. seo fields - empty
        main_product.seo_titulek = ""
        main_product.seo_popis = ""

        # 46-47. marze_dodavatel, cena_dodavatel - empty
        main_product.marze_dodavatel = ""
        main_product.cena_dodavatel = ""

        # 48-52. flags
        main_product.eroticke = "0"
        main_product.pro_dospele = "0"
        main_product.slevovy_kupon = "1"
        main_product.darek_objednavka = "1"
        main_product.priorita = "0"

        # 53-55. poznamka, dodavatel fields - empty
        main_product.poznamka = ""
        main_product.dodavatel_id = ""
        main_product.dodavatel_kod = ""

        # 56. stitky - from RepairedProduct.zbozi_keywords (split by commas)
        main_product.stitky = repaired.zbozi_keywords

        # 57. kategorie_id - from RepairedProduct.category_ids
        main_product.kategorie_id = repaired.category_ids

        # 58-60. related product fields - empty
        main_product.podobne = ""
        main_product.prislusenstvi = ""

        # 60. variantove - list of variant codes as comma-separated string
        if repaired.Variants:
            variant_codes = []
            for i, variant in enumerate(repaired.Variants):
                if hasattr(variant, 'variantcode') and variant.variantcode:
                    variant_codes.append(variant.variantcode)
                else:
                    # Generate variant code if not present
                    variant_codes.append(f"{repaired.code}-V{i+1:02d}")
            main_product.variantove = ",".join(variant_codes)
        else:
            main_product.variantove = ""

        # 61-63. zdarma, sluzby, rozsirujici_obsah - empty
        main_product.zdarma = ""
        main_product.sluzby = ""
        main_product.rozsirujici_obsah = ""

        # 64-72. zbozicz fields
        main_product.zbozicz_skryt = "0"
        main_product.zbozicz_productname = repaired.name
        main_product.zbozicz_product = repaired.name
        main_product.zbozicz_cpc = "5"
        main_product.zbozicz_cpc_search = "5"
        main_product.zbozicz_kategorie = repaired.zbozi_category

        # Split zbozi_keywords for stitek fields
        zbozi_keywords_list = repaired.zbozi_keywords.split(',') if repaired.zbozi_keywords else []
        main_product.zbozicz_stitek_0 = zbozi_keywords_list[0].strip() if len(zbozi_keywords_list) > 0 else ""
        main_product.zbozicz_stitek_1 = zbozi_keywords_list[1].strip() if len(zbozi_keywords_list) > 1 else ""
        main_product.zbozicz_extra = ""

        # 73-77. heurekacz fields
        main_product.heurekacz_skryt = "0"
        main_product.heurekacz_productname = repaired.name
        main_product.heurekacz_product = repaired.name
        main_product.heurekacz_cpc = "1"
        main_product.heurekacz_kategorie = repaired.heureka_category

        # 78-84. google fields
        main_product.google_skryt = "0"
        main_product.google_kategorie = repaired.google_category

        # Split google_keywords for stitek fields
        google_keywords_list = repaired.google_keywords.split(',') if repaired.google_keywords else []
        main_product.google_stitek_0 = google_keywords_list[0].strip() if len(google_keywords_list) > 0 else ""
        main_product.google_stitek_1 = google_keywords_list[1].strip() if len(google_keywords_list) > 1 else ""
        main_product.google_stitek_2 = google_keywords_list[2].strip() if len(google_keywords_list) > 2 else ""
        main_product.google_stitek_3 = google_keywords_list[3].strip() if len(google_keywords_list) > 3 else ""
        main_product.google_stitek_4 = google_keywords_list[4].strip() if len(google_keywords_list) > 4 else ""

        # 85-90. glami fields
        main_product.glami_skryt = "0"
        main_product.glami_kategorie = repaired.glami_category
        main_product.glami_cpc = "1"
        main_product.glami_voucher = ""
        main_product.glami_material = ""
        main_product.glamisk_material = ""

        # 91-94. sklad fields
        main_product.sklad_umisteni = "#"
        main_product.sklad_minimalni = "#"
        main_product.sklad_optimalni = "#"
        main_product.sklad_maximalni = "#"

        return main_product

    def _create_variant_export_product(self, repaired: RepairedProduct, variant: Any, variant_index: int) -> ExportProductVariant:
        """Create variant export product with complete 96-column specification."""
        variant_product = ExportProductVariant()

        # 1. typ - fixed value "varianta"
        variant_product.typ = "varianta"

        # 2-7. varianta1-3 nazev/hodnota - from variant.key_value_pairs
        if hasattr(variant, 'key_value_pairs') and variant.key_value_pairs:
            pairs = list(variant.key_value_pairs.items())

            # varianta1
            if len(pairs) > 0:
                variant_product.varianta1_nazev = pairs[0][0] if pairs[0][0] else ""
                variant_product.varianta1_hodnota = pairs[0][1] if pairs[0][1] else ""
            else:
                variant_product.varianta1_nazev = ""
                variant_product.varianta1_hodnota = ""

            # varianta2
            if len(pairs) > 1:
                variant_product.varianta2_nazev = pairs[1][0] if pairs[1][0] else ""
                variant_product.varianta2_hodnota = pairs[1][1] if pairs[1][1] else ""
            else:
                variant_product.varianta2_nazev = ""
                variant_product.varianta2_hodnota = ""

            # varianta3
            if len(pairs) > 2:
                variant_product.varianta3_nazev = pairs[2][0] if pairs[2][0] else ""
                variant_product.varianta3_hodnota = pairs[2][1] if pairs[2][1] else ""
            else:
                variant_product.varianta3_nazev = ""
                variant_product.varianta3_hodnota = ""
        else:
            variant_product.varianta1_nazev = ""
            variant_product.varianta1_hodnota = ""
            variant_product.varianta2_nazev = ""
            variant_product.varianta2_hodnota = ""
            variant_product.varianta3_nazev = ""
            variant_product.varianta3_hodnota = ""

        # 8. varianta_stejne - fixed "1"
        variant_product.varianta_stejne = "1"

        # 9. zobrazit - fixed "#"
        variant_product.zobrazit = "#"

        # 10. archiv - fixed "0"
        variant_product.archiv = "0"

        # 11. kod - from Variant.variantcode
        if hasattr(variant, 'variantcode') and variant.variantcode:
            variant_product.kod = variant.variantcode
        else:
            # Generate variant code if not present
            variant_product.kod = f"{repaired.code}-V{variant_index:02d}"

        # 12. kod_vyrobku - empty
        variant_product.kod_vyrobku = ""

        # 13-14. ean, isbn - empty
        variant_product.ean = ""
        variant_product.isbn = ""

        # 15. nazev - inherited from main product
        variant_product.nazev = repaired.name

        # 16. privlastek - empty
        variant_product.privlastek = ""

        # 17. vyrobce - inherited from main product (empty if Desaka)
        variant_product.vyrobce = "" if repaired.brand and self._is_desaka_brand(repaired.brand) else repaired.brand

        # 18-19. cena, cena_bezna - from Variant
        if hasattr(variant, 'current_price'):
            variant_product.cena = float(variant.current_price) if variant.current_price else 0.0
        else:
            variant_product.cena = 0.0

        if hasattr(variant, 'basic_price'):
            variant_product.cena_bezna = float(variant.basic_price) if variant.basic_price else variant_product.cena
        else:
            variant_product.cena_bezna = variant_product.cena

        # 20-21. cena_nakupni, recyklacni_poplatek - empty
        variant_product.cena_nakupni = ""
        variant_product.recyklacni_poplatek = ""

        # 22. dph - fixed "21"
        variant_product.dph = "21"

        # 23-25. sleva fields - empty
        variant_product.sleva = ""
        variant_product.sleva_od = ""
        variant_product.sleva_do = ""

        # 26-27. popis, popis_strucny - inherited from main product
        variant_product.popis = repaired.desc
        variant_product.popis_strucny = repaired.shortdesc

        # 28-29. kosik, home - fixed "#"
        variant_product.kosik = "#"
        variant_product.home = "#"

        # 30. dostupnost - fixed "-"
        variant_product.dostupnost = "-"

        # 31. doprava_zdarma - fixed "0"
        variant_product.doprava_zdarma = "0"

        # 32-33. dodaci_doba, dodaci_doba_auto
        variant_product.dodaci_doba = " "  # space character
        variant_product.dodaci_doba_auto = "0"

        # 34-35. sklad, na_sklade - fixed "0"
        variant_product.sklad = "0"
        variant_product.na_sklade = "0"

        # 36-37. hmotnost, delka - empty (not in input)
        variant_product.hmotnost = ""
        variant_product.delka = ""

        # 38-42. jednotka and odber fields - fixed "#"
        variant_product.jednotka = "#"
        variant_product.odber_po = "#"
        variant_product.odber_min = "#"
        variant_product.odber_max = ""
        variant_product.pocet = "#"

        # 43. zaruka - empty
        variant_product.zaruka = ""

        # 44-45. seo fields - empty
        variant_product.seo_titulek = ""
        variant_product.seo_popis = ""

        # 46-47. marze_dodavatel, cena_dodavatel - empty
        variant_product.marze_dodavatel = ""
        variant_product.cena_dodavatel = ""

        # 48-52. flags
        variant_product.eroticke = "0"
        variant_product.pro_dospele = "0"
        variant_product.slevovy_kupon = "1"
        variant_product.darek_objednavka = "1"
        variant_product.priorita = "0"

        # 53-55. poznamka, dodavatel fields - empty
        variant_product.poznamka = ""
        variant_product.dodavatel_id = ""
        variant_product.dodavatel_kod = ""

        # 56. stitky - fixed "#"
        variant_product.stitky = "#"

        # 57. kategorie_id - fixed "#"
        variant_product.kategorie_id = "#"

        # 58-60. related product fields - empty or "#"
        variant_product.podobne = ""
        variant_product.prislusenstvi = ""
        variant_product.variantove = "#"

        # 61-63. zdarma, sluzby, rozsirujici_obsah - empty
        variant_product.zdarma = ""
        variant_product.sluzby = ""
        variant_product.rozsirujici_obsah = ""

        # 64-72. zbozicz fields - fixed "#" for variants
        variant_product.zbozicz_skryt = "0"
        variant_product.zbozicz_productname = "#"
        variant_product.zbozicz_product = "#"
        variant_product.zbozicz_cpc = "5"
        variant_product.zbozicz_cpc_search = "5"
        variant_product.zbozicz_kategorie = "#"
        variant_product.zbozicz_stitek_0 = "#"
        variant_product.zbozicz_stitek_1 = "#"
        variant_product.zbozicz_extra = ""

        # 73-77. heurekacz fields - fixed "#" for variants
        variant_product.heurekacz_skryt = "0"
        variant_product.heurekacz_productname = "#"
        variant_product.heurekacz_product = "#"
        variant_product.heurekacz_cpc = "1"
        variant_product.heurekacz_kategorie = "#"

        # 78-84. google fields - fixed "#" for variants
        variant_product.google_skryt = "0"
        variant_product.google_kategorie = "#"
        variant_product.google_stitek_0 = "#"
        variant_product.google_stitek_1 = "#"
        variant_product.google_stitek_2 = "#"
        variant_product.google_stitek_3 = "#"
        variant_product.google_stitek_4 = "#"

        # 85-90. glami fields - fixed "#" for variants
        variant_product.glami_skryt = "0"
        variant_product.glami_kategorie = "#"
        variant_product.glami_cpc = "1"
        variant_product.glami_voucher = ""
        variant_product.glami_material = ""
        variant_product.glamisk_material = ""

        # 91-94. sklad fields - fixed "#"
        variant_product.sklad_umisteni = "#"
        variant_product.sklad_minimalni = "#"
        variant_product.sklad_optimalni = "#"
        variant_product.sklad_maximalni = "#"

        return variant_product

    def _standardize_stock_status(self, stock_status: str) -> str:
        """Standardize stock status using memory or OpenAI."""
        if not stock_status or not stock_status.strip():
            return ""

        stock_status = stock_status.strip()

        # Check memory first
        memory_key = f"StockStatusMemory_{self.language}"
        if memory_key in self.memory:
            stock_status_memory = self.memory[memory_key]
            if stock_status in stock_status_memory:
                return stock_status_memory[stock_status]

        # Try to find similar keys in memory
        if memory_key in self.memory:
            stock_status_memory = self.memory[memory_key]
            similar_keys = self._find_similar_memory_keys(stock_status, stock_status_memory, threshold=0.8)

            if similar_keys:
                selected_stock_status = self._ask_user_for_similar_key_selection("Stock Status", stock_status, similar_keys)
                if selected_stock_status:
                    # Save to memory with current stock status as key
                    self.memory[memory_key][stock_status] = selected_stock_status
                    self._save_memory_file(memory_key)
                    return selected_stock_status

        # Use OpenAI if available
        if self.openai:
            standardized = self.openai.standardize_stock_status(
                stock_status, self.language,
                self.memory.get(memory_key, {})
            )
            if standardized:
                # Confirm with user if needed
                confirmed_value = self._confirm_ai_result(
                    "Stock Status", stock_status, standardized,
                    f"Stock status: {stock_status}", ""
                )
                if confirmed_value:
                    # Save to memory
                    if memory_key not in self.memory:
                        self.memory[memory_key] = {}
                    self.memory[memory_key][stock_status] = confirmed_value
                    self._save_memory_file(memory_key)
                    return confirmed_value

        # Ask user directly if AI not available or failed
        user_value = self._ask_user_for_variant_value("Stock Status", stock_status, f"Stock status: {stock_status}")
        if user_value:
            user_value = user_value.strip()
            # Save to memory
            if memory_key not in self.memory:
                self.memory[memory_key] = {}
            self.memory[memory_key][stock_status] = user_value
            self._save_memory_file(memory_key)
            return user_value

        return stock_status

