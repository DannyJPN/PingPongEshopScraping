import csv
import logging
from tqdm import tqdm
import json

def export_to_csv(csv_output_path, products):
    with open(csv_output_path, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter.writerow(['Name', 'Short Description', 'Description',  'Main Photo Filepath', 'Gallery Filepaths', 'Variants','URL'])
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for product in tqdm(products, desc="Writing products to CSV"):
            writer.writerow({
                'name': product.name,
                'short_description': product.short_description,
                'description': product.description,
                'main_photo_filepath': product.main_photo_filepath,
                'gallery_photo_filepaths': ';'.join(product.photogallery_filepaths),
                'variants': ';'.join([json.dumps({"key_value_pairs": variant.key_value_pairs,"current_price": variant.current_price,"basic_price": variant.basic_price,"stock_status": variant.stock_status}, ensure_ascii=False) for variant in product.variants]),
                'url': product.url
            })
        logging.info(f"CSV file created at {csv_output_path}")