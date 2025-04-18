Based on the development instructions and user feedback, I'll create a new file `unifierlib/json_transformer.py` that will separate the JSON loading and transformation logic from the `eshop_data_handler.py` file. Here's the implementation:

```python
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from typing import List, Dict, Any, Optional
from unifierlib.unified_export_product import UnifiedExportProduct, UnifiedExportProductMain, UnifiedExportProductVariant
from unifierlib.product_mapper import json_to_unified

def load_json_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of dictionaries containing the parsed JSON data
        
    Raises:
        JSONDecodeError: If JSON parsing fails
        IOError: If file reading fails
    """
    try:
        logging.info(f"Loading JSON file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            
        logging.debug(f"Type of loaded JSON data: {type(json_data)}")
        if isinstance(json_data, list):
            logging.debug(f"First item in JSON data: {json_data[0] if json_data else 'Empty list'}")
        else:
            logging.error("Loaded JSON data is not a list")
            raise ValueError("JSON file must contain a list of objects")
            
        return json_data
        
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON file {file_path}: {str(e)}", exc_info=True)
        raise
    except IOError as e:
        logging.error(f"Failed to read file {file_path}: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logging.error(f"Unexpected error while loading JSON file {file_path}: {str(e)}", exc_info=True)
        raise

def process_json_item(item: Dict[str, Any]) -> Optional[List[UnifiedExportProduct]]:
    """
    Process a single JSON item and transform it into UnifiedExportProduct objects.
    
    Args:
        item: Dictionary containing product data
        
    Returns:
        List of UnifiedExportProduct objects or None if processing fails
    """
    try:
        logging.debug(f"Type of received item: {type(item)}")
        logging.debug(f"Processing JSON item with ID: {item.get('id', 'unknown')}")
        
        transformed_items = json_to_unified(item)
        
        unified_products = []
        for mapping in transformed_items:
            if mapping['typ'] == 'produkt':
                product = UnifiedExportProductMain()
            else:
                product = UnifiedExportProductVariant()
            product.fill(mapping)
            unified_products.append(product)
            
        logging.debug(f"Successfully transformed item ID: {item.get('id', 'unknown')} into {len(unified_products)} products")
        return unified_products
        
    except Exception as e:
        logging.error(f"Error processing JSON item: {str(e)}\nTraceback: ", exc_info=True)
        return None

def transform_json_to_unified_products(json_data: List[Dict[str, Any]]) -> List[UnifiedExportProduct]:
    """
    Transform JSON data into UnifiedExportProduct objects using parallel processing.
    
    Args:
        json_data: List of dictionaries containing product data
        
    Returns:
        List of transformed UnifiedExportProduct objects
    """
    if not json_data:
        logging.warning("Empty JSON data provided")
        return []
        
    unified_products = []
    max_workers = min(32, len(json_data))  # Limit max threads to 32 or number of items
    logging.info(f"Starting parallel processing with {max_workers} threads")
    
    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(process_json_item, item): item
                for item in json_data
            }
            
            # Use tqdm to track progress of completed threads
            with tqdm(total=len(future_to_item), desc="Processing products") as pbar:
                for future in as_completed(future_to_item):
                    try:
                        result = future.result()
                        if result:
                            unified_products.extend(result)
                    except Exception as e:
                        logging.error(f"Thread execution failed: {str(e)}\nTraceback: ", exc_info=True)
                    finally:
                        pbar.update(1)
                        
        logging.info(f"Successfully transformed {len(unified_products)} products")
        return unified_products
        
    except Exception as e:
        logging.error(f"Error in parallel processing: {str(e)}", exc_info=True)
        return []
```

This implementation:

1. Separates the JSON loading and transformation logic into distinct functions
2. Adds comprehensive error handling and logging
3. Uses type hints for better code clarity
4. Includes detailed logging of data types and content for debugging
5. Maintains the multithreaded processing capability with progress tracking
6. Follows clean code principles with clear function names and responsibilities
7. Includes proper documentation for all functions

The code can be used by importing the necessary functions and using them separately, which addresses the user's feedback about separating the load and transform functionality.
