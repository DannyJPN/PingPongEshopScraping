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
                # Create filename with just the basename of the URL
                filename = os.path.join(photos_folder, sanitize_filename(os.path.basename(product.main_photo_link)))
                # Get the sanitized filepath that will be used
                directory, basename = os.path.split(filename)
                sanitized_basename = sanitize_filename(basename).split("%")[0]
                sanitized_filepath = os.path.join(directory, sanitized_basename)

                # Download the image and check if successful
                success = download_image(product.main_photo_link, filename, overwrite, debug)
                logging.debug(f"Download success for main photo: {success}")
                if success:  # True if download was successful or file already exists
                    product.main_photo_filepath = sanitized_filepath
                    logging.debug(f"Set main_photo_filepath to: {product.main_photo_filepath}")
    except Exception as e:
        logging.error(f"Error downloading main product images: {e}", exc_info=True)

def download_product_gallery_images(products, root_folder, overwrite=False, debug=False):
    try:
        photos_folder = get_photos_folder(root_folder)
        for product in tqdm(products, desc="Downloading product gallery images"):
            for link in product.photogallery_links:
                # Create filename with just the basename of the URL
                filename = os.path.join(photos_folder, sanitize_filename(os.path.basename(link)))
                # Get the sanitized filepath that will be used
                directory, basename = os.path.split(filename)
                sanitized_basename = sanitize_filename(basename).split("%")[0]
                sanitized_filepath = os.path.join(directory, sanitized_basename)

                # Download the image and check if successful
                success = download_image(link, filename, overwrite, debug)
                logging.debug(f"Download success for gallery photo: {success}")
                if success:  # True if download was successful or file already exists
                    product.photogallery_filepaths.append(sanitized_filepath)
                    logging.debug(f"Added to photogallery_filepaths, now has {len(product.photogallery_filepaths)} items")
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
