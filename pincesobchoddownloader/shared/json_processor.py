import os
import json
import logging
from tqdm import tqdm  # Import TQDM
from shared.image_downloader import download_image
from shared.utils import get_products_folder, get_photos_folder, sanitize_filename

def process_json_file(json_filepath, result_folder, lang_code, overwrite):
    try:
        logging.debug(f"Starting process_json_file function with overwrite={overwrite}")

        with open(json_filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)

        products = data.get('data', [])
        logging.info(f"Found {len(products)} products in the JSON file.")

        products_folder = get_products_folder(result_folder)
        photos_folder = get_photos_folder(result_folder)

        # First loop: Process and save product information
        with tqdm(total=len(products), desc="Processing Products") as pbar:
            for product in products:
                product_name = product.get('translations', {}).get(lang_code.lower(), {}).get('name', 'Unknown')
                product_code = product.get('catalogNumber', 'Unknown')

                # Sanitize the product name for use as a filename
                sanitized_product_name = sanitize_filename(product_name)

                # Save the entire product information
                product_info_filepath = os.path.join(products_folder, f"{sanitized_product_name}.json")
                logging.debug(f"Checking if product info file exists: {product_info_filepath}")
                if not overwrite and os.path.exists(product_info_filepath):
                    logging.debug(f"Product info file already exists and overwrite is not set: {product_info_filepath}")
                else:
                    with open(product_info_filepath, 'w', encoding='utf-8') as product_file:
                        json.dump(product, product_file, ensure_ascii=False, indent=4)
                    logging.debug(f"Saved product info for {product_name} to {product_info_filepath}")

                pbar.update(1)

        # Separate progress bars for main and gallery images
        main_images = []
        gallery_images = []

        for product in products:
            product_code = product.get('catalogNumber', 'Unknown')
            product_images = product.get('images', [])
            for index, image in enumerate(product_images, start=1):
                image_url = image.get('url')
                is_default = image.get('default', False)
                image_index = '01' if is_default else f"{index:02d}"
                image_filename = f"{product_code}_{image_index}.jpg"
                image_filepath = os.path.join(photos_folder, image_filename)
                if is_default:
                    main_images.append((image_url, image_filepath))
                else:
                    gallery_images.append((image_url, image_filepath))

        # Download main images
        with tqdm(total=len(main_images), desc="Downloading Main Images") as pbar:
            for image_url, image_filepath in main_images:
                logging.debug(f"Downloading main image from {image_url} to {image_filepath}")
                download_image(image_url, image_filepath, overwrite=overwrite)
                pbar.update(1)

        # Download gallery images
        with tqdm(total=len(gallery_images), desc="Downloading Gallery Images") as pbar:
            for image_url, image_filepath in gallery_images:
                logging.debug(f"Downloading gallery image from {image_url} to {image_filepath}")
                download_image(image_url, image_filepath, overwrite=overwrite)
                pbar.update(1)

    except Exception as e:
        logging.error(f"Error processing JSON file {json_filepath}: {e}", exc_info=True)
        raise










