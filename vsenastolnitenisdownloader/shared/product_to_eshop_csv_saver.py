import csv
import logging
from tqdm import tqdm
import json

def export_to_csv(csv_output_path,products):
    with open(csv_output_path, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        # Write the header
        csvwriter.writerow(['Name', 'Short Description', 'Description',  'Main Photo Filepath', 'Gallery Filepaths', 'Variants','URL'])
        # Write product data
        with tqdm(total=len(products), desc="Exporting to csv") as pbar:
            for product in products:
                # Log the values being written to CSV
                logging.debug(f"Product: {product.name}")
                logging.debug(f"Main Photo Filepath: {product.main_photo_filepath}")
                logging.debug(f"Gallery Filepaths: {product.photogallery_filepaths}")
                
                csvwriter.writerow([
                    product.name,
                    product.short_description,
                    product.description,
                    product.main_photo_filepath,
                    '|'.join(product.photogallery_filepaths),
                    '|'.join([json.dumps({"key_value_pairs": variant.key_value_pairs,"current_price": variant.current_price,"basic_price": variant.basic_price,"stock_status": variant.stock_status},ensure_ascii=False) for variant in product.variants]),
                    product.url
                ])
                pbar.update(1)

    logging.info(f"CSV output generated at: {csv_output_path}")
