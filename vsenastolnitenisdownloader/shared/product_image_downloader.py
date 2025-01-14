import os
import logging
from tqdm import tqdm
from shared.utils import get_photos_folder
from shared.utils import sanitize_filename
from shared.image_downloader import download_image

def download_product_main_image(products, root_folder, overwrite=False, debug=False):
    try:
        photos_folder = get_photos_folder(root_folder)
        for product in tqdm(products, desc="Downloading main product images"):
            if product.main_photo_link:
                filename = os.path.join(photos_folder, sanitize_filename(product.main_photo_link))
                if download_image(product.main_photo_link, filename, overwrite, debug):
                    product.main_photo_filepath = filename
    except Exception as e:
        logging.error(f"Error downloading main product images: {e}", exc_info=True)

def download_product_gallery_images(products, root_folder, overwrite=False, debug=False):
    try:
        photos_folder = get_photos_folder(root_folder)
        for product in tqdm(products, desc="Downloading product gallery images"):
            for link in product.photogallery_links:
                filename = os.path.join(photos_folder, sanitize_filename(link))
                if download_image(link, filename, overwrite, debug):
                    product.photogallery_filepaths.append(filename)
    except Exception as e:
        logging.error(f"Error downloading product gallery images: {e}", exc_info=True)

def get_image_folder(product, root_folder, image_type):
    photo_folder = get_photos_folder(root_folder)
    product_name_sanitized = sanitize_filename(product.name)
    folder = os.path.join(photo_folder, product_name_sanitized, image_type)
    if not os.path.exists(folder):
        os.makedirs(folder)
        logging.debug(f"Created folder: {folder}")
    return folder