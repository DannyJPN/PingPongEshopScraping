import os
import logging
from tqdm import tqdm
from shared.utils import get_photos_folder
from shared.utils import sanitize_filename
from shared.image_downloader import download_image
from shared.download_constants import BASE_RETRY_DELAY

def download_product_main_image(products,rootfolder, overwrite, stats=None):
    with tqdm(total=len(products), desc="Downloading main images") as pbar:
        for i in range(len(products)):
            try:
                main_image_folder = get_image_folder(products[i], rootfolder, "MainImage")
                file_path = os.path.join(main_image_folder,sanitize_filename(os.path.basename(products[i].main_photo_link)))
                if download_image(products[i].main_photo_link, file_path, overwrite=overwrite, stats=stats):
                    products[i].main_photo_filepath = os.path.abspath(file_path)

                # Update progress bar with statistics
                if stats:
                    url = products[i].main_photo_link
                    total_req, failed_req = stats.get_stats(url)
                    if total_req > 0:
                        success_rate = ((total_req - failed_req) / total_req) * 100
                        failure_rate = stats.get_failure_rate(url)
                        current_delay = BASE_RETRY_DELAY * (1 + failure_rate)
                        pbar.set_postfix({
                            'OK': f'{success_rate:.1f}%',
                            'delay': f'{current_delay:.3f}s'
                        })
                pbar.update(1)
            except Exception as e:
                logging.error(f"Error downloading main image for product {products[i].name}: {e}", exc_info=True)
    return products
    
    
    
def download_product_gallery_images(products,rootfolder, overwrite, stats=None):
    total = sum([len(product.photogallery_links) for product in products])
    with tqdm(total=total, desc="Downloading gallery images") as pbar:
        for i in range(len(products)):
            try:
                gallery_image_folder = get_image_folder(products[i], rootfolder, "GalleryImages")
                for link in products[i].photogallery_links:
                    file_path = os.path.join(gallery_image_folder, sanitize_filename(os.path.basename(link)))
                    if download_image(link, file_path, overwrite=overwrite, stats=stats):
                        products[i].photogallery_filepaths.append(os.path.abspath(file_path))

                    # Update progress bar with statistics
                    if stats:
                        total_req, failed_req = stats.get_stats(link)
                        if total_req > 0:
                            success_rate = ((total_req - failed_req) / total_req) * 100
                            failure_rate = stats.get_failure_rate(link)
                            current_delay = BASE_RETRY_DELAY * (1 + failure_rate)
                            pbar.set_postfix({
                                'OK': f'{success_rate:.1f}%',
                                'delay': f'{current_delay:.3f}s'
                            })
                    pbar.update(1)
            except Exception as e:
                logging.error(f"Error downloading gallery images for product {products[i].name}: {e}", exc_info=True)
    return products
    
def get_image_folder(product, root_folder, image_type):
    photo_folder=get_photos_folder(root_folder)
    # Use sanitize_filename instead of URL-encoding the entire name
    product_name_sanitized = sanitize_filename(product.name)
    folder = os.path.join(photo_folder, product_name_sanitized,image_type)
    if not os.path.exists(folder):
        os.makedirs(folder)
        logging.debug(f"Created folder: {folder}")
    return folder
