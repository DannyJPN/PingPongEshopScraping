import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Any, Optional
from tqdm import tqdm

from .product_classes import UnifiedExportProductMain, UnifiedExportProductVariant
from .csv_reader import read_default_values
from .mappings import UnifyProductMapping

class ProductTransformer:
    """Handles transformation of JSON product data into UnifiedExportProduct objects."""

    def __init__(self, default_values_path: Path):
        """
        Initialize transformer with default values from CSV.

        Args:
            default_values_path: Path to DefaultUnifiedProductValues.csv
        """
        logging.info(f"Initializing ProductTransformer with defaults from: {default_values_path}")
        try:
            self.defaults = read_default_values(default_values_path)
            logging.debug(f"Loaded default values: {self.defaults}")
        except Exception as e:
            logging.error(f"Failed to initialize ProductTransformer: {e}", exc_info=True)
            raise

    def transform_single_product(self, json_item: Dict[str, Any]) -> Optional[List[UnifiedExportProductMain]]:
        """
        Transform single JSON item into list of UnifiedExportProduct objects.

        Args:
            json_item: Single product data from JSON

        Returns:
            List containing main product and its variants, or None if transformation fails
        """
        try:
            logging.debug(f"Transforming product: {json_item.get('id', 'unknown id')}")

            # Create mappings using UnifyProductMapping
            mappings = UnifyProductMapping.create_mappings(json_item)
            if not mappings:
                logging.error("Failed to create mappings for product")
                return None

            # Create main product
            main_product = UnifiedExportProductMain(self.defaults['main'])
            main_mapping = mappings[0]  # First mapping is always the main product

            # Map all attributes according to UnifyProductMapping
            main_product.id = main_mapping.get('id', self.defaults['main'].get('id', ''))
            main_product.typ = main_mapping.get('typ', self.defaults['main'].get('typ', 'produkt'))
            main_product.varianta_id = main_mapping.get('varianta_id', self.defaults['main'].get('varianta_id', '#'))
            main_product.varianta1_nazev = main_mapping.get('varianta1_nazev', self.defaults['main'].get('varianta1_nazev', '#'))
            main_product.varianta1_hodnota = main_mapping.get('varianta1_hodnota', self.defaults['main'].get('varianta1_hodnota', '#'))
            main_product.varianta2_nazev = main_mapping.get('varianta2_nazev', self.defaults['main'].get('varianta2_nazev', '#'))
            main_product.varianta2_hodnota = main_mapping.get('varianta2_hodnota', self.defaults['main'].get('varianta2_hodnota', '#'))
            main_product.varianta3_nazev = main_mapping.get('varianta3_nazev', self.defaults['main'].get('varianta3_nazev', '#'))
            main_product.varianta3_hodnota = main_mapping.get('varianta3_hodnota', self.defaults['main'].get('varianta3_hodnota', '#'))
            main_product.varianta_stejne = main_mapping.get('varianta_stejne', self.defaults['main'].get('varianta_stejne', '#'))
            
            # Visibility and status
            main_product.zobrazit = int(main_mapping.get('zobrazit', self.defaults['main'].get('zobrazit', 1)))
            main_product.archiv = int(main_mapping.get('archiv', self.defaults['main'].get('archiv', 0)))
            
            # Basic product information
            main_product.kod = main_mapping.get('kod', self.defaults['main'].get('kod', ''))
            main_product.kod_vyrobku = main_mapping.get('kod_vyrobku', self.defaults['main'].get('kod_vyrobku', ''))
            main_product.ean = main_mapping.get('ean', self.defaults['main'].get('ean', ''))
            main_product.isbn = main_mapping.get('isbn', self.defaults['main'].get('isbn', ''))
            main_product.nazev = main_mapping.get('nazev', self.defaults['main'].get('nazev', ''))
            main_product.privlastek = main_mapping.get('privlastek', self.defaults['main'].get('privlastek', ''))
            main_product.vyrobce = main_mapping.get('vyrobce', self.defaults['main'].get('vyrobce', ''))
            main_product.dodavatel_id = main_mapping.get('dodavatel_id', self.defaults['main'].get('dodavatel_id', ''))

            # Pricing
            main_product.cena = float(main_mapping.get('cena', self.defaults['main'].get('cena', 0)))
            main_product.cena_bezna = float(main_mapping.get('cena_bezna', self.defaults['main'].get('cena_bezna', 0)))
            main_product.cena_nakupni = main_mapping.get('cena_nakupni', self.defaults['main'].get('cena_nakupni', ''))
            main_product.dph = float(main_mapping.get('dph', self.defaults['main'].get('dph', 21)))
            main_product.sleva = float(main_mapping.get('sleva', self.defaults['main'].get('sleva', 0)))

            # Description
            main_product.popis = main_mapping.get('popis', self.defaults['main'].get('popis', ''))
            main_product.popis_strucny = main_mapping.get('popis_strucny', self.defaults['main'].get('popis_strucny', ''))

            # Stock and availability
            main_product.dostupnost = main_mapping.get('dostupnost', self.defaults['main'].get('dostupnost', '#'))
            main_product.sklad = main_mapping.get('sklad', self.defaults['main'].get('sklad', '#'))
            main_product.na_sklade = main_mapping.get('na_sklade', self.defaults['main'].get('na_sklade', '#'))

            # Platform categories
            main_product.zbozicz_kategorie = main_mapping.get('zbozi_category', self.defaults['main'].get('zbozicz_kategorie', ''))
            main_product.heurekacz_kategorie = main_mapping.get('heureka_category', self.defaults['main'].get('heurekacz_kategorie', ''))
            main_product.google_kategorie = main_mapping.get('google_category', self.defaults['main'].get('google_kategorie', ''))
            main_product.glami_kategorie = main_mapping.get('glami_category', self.defaults['main'].get('glami_kategorie', ''))

            result = [main_product]

            # Process variants if present
            variant_mappings = mappings[1:]  # Rest of mappings are variants
            if variant_mappings:
                logging.debug(f"Processing {len(variant_mappings)} variants for product {json_item.get('id', 'unknown')}")

                for variant_mapping in variant_mappings:
                    try:
                        variant = UnifiedExportProductVariant(self.defaults['variant'])

                        # Map variant attributes according to UnifyProductMapping
                        variant.id = variant_mapping.get('id', self.defaults['variant'].get('id', ''))
                        variant.typ = 'varianta'
                        variant.varianta_id = variant_mapping.get('variant_id', self.defaults['variant'].get('varianta_id', '#'))
                        variant.kod = variant_mapping.get('kod', self.defaults['variant'].get('kod', ''))
                        variant.nazev = variant_mapping.get('nazev', self.defaults['variant'].get('nazev', ''))
                        variant.cena = float(variant_mapping.get('cena', self.defaults['variant'].get('cena', 0)))
                        variant.sklad = variant_mapping.get('sklad', self.defaults['variant'].get('sklad', '#'))
                        variant.ean = variant_mapping.get('ean', self.defaults['variant'].get('ean', ''))

                        # Map variant options
                        variant_options = variant_mapping.get('variant_options', {})
                        for i, (name, value) in enumerate(variant_options.items(), 1):
                            if i <= 3:  # Maximum 3 variants supported
                                setattr(variant, f'varianta{i}_nazev', name)
                                setattr(variant, f'varianta{i}_hodnota', value)

                        result.append(variant)
                        logging.debug(f"Successfully processed variant {variant.kod}")
                    except Exception as ve:
                        logging.error(f"Error processing variant: {ve}", exc_info=True)
                        continue

            return result

        except Exception as e:
            logging.error(f"Error transforming product {json_item.get('id', 'unknown')}: {e}", exc_info=True)
            return None

    def transform_products(self, json_data: List[Dict[str, Any]], max_workers: int = None) -> List[List[UnifiedExportProductMain]]:
        """
        Transform JSON items into UnifiedExportProduct objects using parallel processing.

        Args:
            json_data: List of product data from JSON
            max_workers: Maximum number of worker threads (None for default)

        Returns:
            List of transformed product lists (each inner list contains main product and its variants)
        """
        results = []
        successful_transforms = 0
        failed_transforms = 0

        try:
            logging.info(f"Starting parallel transformation of {len(json_data)} products")

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_item = {
                    executor.submit(self.transform_single_product, item): item
                    for item in json_data
                }

                # Process results with progress bar
                with tqdm(total=len(future_to_item), desc="Transforming products") as pbar:
                    for future in as_completed(future_to_item):
                        try:
                            result = future.result()
                            if result:
                                results.append(result)
                                successful_transforms += 1
                            else:
                                failed_transforms += 1
                        except Exception as e:
                            logging.error(f"Error processing product: {e}", exc_info=True)
                            failed_transforms += 1
                        finally:
                            pbar.update(1)

            logging.info(f"Transformation completed: {successful_transforms} successful, "
                        f"{failed_transforms} failed")

            return results

        except Exception as e:
            logging.error(f"Error in parallel transformation: {e}", exc_info=True)
            return []

    def get_transformation_stats(self, results: List[List[UnifiedExportProductMain]]) -> Dict[str, int]:
        """
        Calculate transformation statistics.

        Args:
            results: List of transformed product lists

        Returns:
            Dictionary with statistics (total products, main products, variants)
        """
        try:
            total_products = sum(len(product_list) for product_list in results)
            main_products = len(results)
            variants = total_products - main_products

            stats = {
                'total_products': total_products,
                'main_products': main_products,
                'variants': variants
            }

            logging.info(f"Transformation stats: {stats}")
            return stats

        except Exception as e:
            logging.error(f"Error calculating transformation stats: {e}", exc_info=True)
            return {
                'total_products': 0,
                'main_products': 0,
                'variants': 0
            }