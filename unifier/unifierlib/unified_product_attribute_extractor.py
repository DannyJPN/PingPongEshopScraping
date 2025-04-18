    import logging
    import json
    import os
    import re
    from bs4 import BeautifulSoup
    from typing import Optional, Dict, List, Any

    from .downloaded_product import DownloadedProduct
    from .repaired_product import RepairedProduct
    from .constants import (
        NAME_MEMORY_PREFIX, DESC_MEMORY_PREFIX, SHORT_DESC_MEMORY_PREFIX,
        VARIANT_NAME_MEMORY_PREFIX, VARIANT_VALUE_MEMORY_PREFIX,
        PRODUCT_MODEL_MEMORY_PREFIX, PRODUCT_BRAND_MEMORY_PREFIX,
        PRODUCT_TYPE_MEMORY_PREFIX, CATEGORY_MEMORY_PREFIX,
        CATEGORY_MAPPING_HEUREKA_PREFIX, CATEGORY_MAPPING_ZBOZI_PREFIX,
        CATEGORY_MAPPING_GLAMI_PREFIX, CATEGORY_MAPPING_GOOGLE_PREFIX,
        KEYWORDS_GOOGLE_PREFIX, KEYWORDS_ZBOZI_PREFIX
    )



    def extract_product_attributes(
        downloaded_product: DownloadedProduct,
        memory_files: Dict,
        language: str,
        existing_products: Optional[List] = None
    ) -> RepairedProduct:
        """
        Extract and process all attributes for a product.

        Args:
            downloaded_product: Product to process
            memory_files: Dictionary containing memory file data
            language: Language code
            existing_products: Optional list of existing products for context

        Returns:
            RepairedProduct with all attributes processed
        """
        logger.info(f"Processing attributes for product: {downloaded_product.name}")

        try:
            repaired_product = RepairedProduct()
            repaired_product.fill_from_downloaded(downloaded_product)

            # Extract each attribute
            repaired_product.original_name = extract_original_name(downloaded_product)
            repaired_product.category = extract_category(downloaded_product, memory_files, language)
            repaired_product.brand = extract_brand(downloaded_product, memory_files, language)
            repaired_product.category_ids = extract_category_ids(downloaded_product, memory_files, language)
            repaired_product.code = extract_code(downloaded_product, memory_files, language, existing_products)
            repaired_product.desc = extract_desc(downloaded_product, memory_files, language)
            repaired_product.glami_category = extract_glami_category(downloaded_product, memory_files, language)
            repaired_product.google_category = extract_google_category(downloaded_product, memory_files, language)
            repaired_product.google_keywords = extract_google_keywords(downloaded_product, memory_files, language)
            repaired_product.heureka_category = extract_heureka_category(downloaded_product, memory_files, language)
            repaired_product.name = extract_name(downloaded_product, memory_files, language)
            repaired_product.price = extract_price(downloaded_product)
            repaired_product.price_standard = extract_price_standard(downloaded_product)
            repaired_product.shortdesc = extract_shortdesc(downloaded_product, memory_files, language)
            repaired_product.variantcode = extract_variantcode(downloaded_product, existing_products)
            repaired_product.variants = extract_variants(downloaded_product, memory_files, language)
            repaired_product.zbozi_category = extract_zbozi_category(downloaded_product, memory_files, language)
            repaired_product.zbozi_keyword = extract_zbozi_keywords(downloaded_product, memory_files, language)

            return repaired_product

        except Exception as e:
            logger.error(f"Error processing product {downloaded_product.name}: {str(e)}", exc_info=True)
            raise

    def get_from_memory(memory_files: Dict, prefix: str, key: str) -> Optional[str]:
        """Get value from memory file"""
        try:
            if prefix not in memory_files:
                return None

            for entry in memory_files[prefix]:
                if entry.get('KEY') == key:
                    return entry.get('VALUE')
            return None
        except Exception as e:
            logger.error(f"Error accessing memory file {prefix}: {str(e)}", exc_info=True)
            return None

    def save_to_memory(memory_files: Dict, prefix: str, key: str, value: str) -> None:
        """Save value to memory file"""
        try:
            if prefix not in memory_files:
                memory_files[prefix] = []

            memory_data = memory_files[prefix]

            for entry in memory_data:
                if entry.get('KEY') == key:
                    entry['VALUE'] = value
                    return

            memory_data.append({'KEY': key, 'VALUE': value})
        except Exception as e:
            logger.error(f"Error saving to memory file {prefix}: {str(e)}", exc_info=True)
            raise

    def call_openai(prompt: str, expected_format: Any) -> Optional[Any]:
        """Mock OpenAI API call"""
        logger.info(f"Mock OpenAI call with prompt: {prompt}")
        # TODO: Implement actual OpenAI integration
        return None

    def confirm_ai_result(result: str, context: str) -> str:
        """Get user confirmation for AI result"""
        logger.info(f"AI suggested result for {context}: {result}")
        confirmation = input(f"Press Enter to confirm or type correct value for {context}: ")
        return confirmation.strip() if confirmation.strip() else result

    def clean_html(html_content: str) -> str:
        """Clean HTML content while preserving structure"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove unwanted tags
            for tag in soup.find_all(['script', 'style']):
                tag.decompose()

            # Replace specific tags with newlines
            for tag in soup.find_all(['br', 'p', 'div']):
                tag.replace_with('\n' + tag.get_text() + '\n')

            # Clean up whitespace
            text = soup.get_text()
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = re.sub(r'^\s+|\s+$', '', text)

            return text
        except Exception as e:
            logger.error(f"Error cleaning HTML: {str(e)}", exc_info=True)
            return html_content

    def extract_original_name(product: DownloadedProduct) -> str:
        """Extract original name directly from product"""
        if not product or not hasattr(product, 'name'):
            logger.error("Invalid product or missing name attribute")
            return ""
        return product.name

    def extract_category(product: DownloadedProduct, memory_files: Dict, language: str) -> str:
        """Extract category using memory and OpenAI"""
        try:
            category = get_from_memory(memory_files, CATEGORY_MEMORY_PREFIX, product.name)
            if category:
                return category

            prompt = f"Extract category for: {product.name}\n{product.description}"
            ai_result = call_openai(prompt, "string")
            if ai_result:
                confirmed = confirm_ai_result(ai_result, "category")
                save_to_memory(memory_files, CATEGORY_MEMORY_PREFIX, product.name, confirmed)
                return confirmed

            return ""
        except Exception as e:
            logger.error(f"Error extracting category: {str(e)}", exc_info=True)
            return ""

    def extract_variants(product: DownloadedProduct, memory_files: Dict, language: str) -> List[Dict]:
        """Extract and process variants"""
        try:
            if not product.variants:
                return []

            processed_variants = []
            for variant in product.variants:
                processed = process_variant(variant, memory_files, language)
                if processed:
                    processed_variants.append(processed)

            return processed_variants
        except Exception as e:
            logger.error(f"Error extracting variants: {str(e)}", exc_info=True)
            return []

    def process_variant(variant: Dict, memory_files: Dict, language: str) -> Optional[Dict]:
        """Process individual variant data"""
        try:
            processed = {
                'varianta1_nazev': None,
                'varianta1_hodnota': None,
                'varianta2_nazev': None,
                'varianta2_hodnota': None,
                'varianta3_nazev': None,
                'varianta3_hodnota': None
            }

            variant_count = 0
            for name, value in variant.items():
                variant_count += 1
                if variant_count > 3:
                    break

                name = normalize_variant_name(name, memory_files, language)
                value = normalize_variant_value(value, memory_files, language)

                processed[f'varianta{variant_count}_nazev'] = name
                processed[f'varianta{variant_count}_hodnota'] = value

            return processed
        except Exception as e:
            logger.error(f"Error processing variant: {str(e)}", exc_info=True)
            return None

    def normalize_variant_name(name: str, memory_files: Dict, language: str) -> str:
        """Normalize variant name using memory"""
        try:
            normalized = get_from_memory(memory_files, VARIANT_NAME_MEMORY_PREFIX, name)
            if normalized:
                return normalized

            normalized = name.strip().title()
            save_to_memory(memory_files, VARIANT_NAME_MEMORY_PREFIX, name, normalized)
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing variant name: {str(e)}", exc_info=True)
            return name

    def normalize_variant_value(value: str, memory_files: Dict, language: str) -> str:
        """Normalize variant value using memory"""
        try:
            normalized = get_from_memory(memory_files, VARIANT_VALUE_MEMORY_PREFIX, str(value))
            if normalized:
                return normalized

            normalized = str(value).strip()
            save_to_memory(memory_files, VARIANT_VALUE_MEMORY_PREFIX, str(value), normalized)
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing variant value: {str(e)}", exc_info=True)
            return str(value)
