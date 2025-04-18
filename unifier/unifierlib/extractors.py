import logging
import re
from bs4 import BeautifulSoup
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

def extract_original_name(downloaded_product, memory_files=None) -> str:
    """Extract original name directly from product"""
    if not downloaded_product or not hasattr(downloaded_product, 'name'):
        logger.error("Invalid product or missing name attribute")
        return ""
    return downloaded_product.name

def extract_category(downloaded_product, category_memory_file: str, language: str) -> str:
    """Extract category using memory file and OpenAI"""
    try:
        # Try to get from memory file
        with open(category_memory_file, 'r', encoding='utf-8') as f:
            for line in f:
                key, value = line.strip().split(',')
                if key == downloaded_product.name:
                    return value

        # If not found, use OpenAI
        prompt = f"Extract category for: {downloaded_product.name}\n{downloaded_product.description}"
        ai_result = _call_openai(prompt)
        if ai_result:
            confirmed = _confirm_ai_result(ai_result, "category")
            _save_to_memory_file(category_memory_file, downloaded_product.name, confirmed)
            return confirmed
        return ""
    except Exception as e:
        logger.error(f"Error extracting category: {str(e)}")
        return ""

def extract_brand(downloaded_product, brand_memory_file: str, language: str) -> str:
    # Implementation similar to extract_category
    pass

def extract_desc(downloaded_product, desc_memory_file: str, language: str) -> str:
    # Implementation with HTML cleaning
    try:
        if not downloaded_product.description:
            return ""

        cleaned_desc = _clean_html(downloaded_product.description)

        # Check memory
        with open(desc_memory_file, 'r', encoding='utf-8') as f:
            for line in f:
                key, value = line.strip().split(',')
                if key == downloaded_product.name:
                    return value

        # Save cleaned desc to memory
        _save_to_memory_file(desc_memory_file, downloaded_product.name, cleaned_desc)
        return cleaned_desc
    except Exception as e:
        logger.error(f"Error extracting description: {str(e)}")
        return downloaded_product.description

def _clean_html(html_content: str) -> str:
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for tag in soup.find_all(['script', 'style']):
            tag.decompose()
        text = soup.get_text()
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception as e:
        logger.error(f"Error cleaning HTML: {str(e)}")
        return html_content

def _call_openai(prompt: str) -> Optional[str]:
    # Mock implementation
    logger.info(f"OpenAI call with prompt: {prompt}")
    return None

def _confirm_ai_result(result: str, context: str) -> str:
    confirmation = input(f"Press Enter to confirm or type correct value for {context}: ")
    return confirmation.strip() if confirmation.strip() else result

def _save_to_memory_file(filepath: str, key: str, value: str):
    try:
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(f"{key},{value}\n")
    except Exception as e:
        logger.error(f"Error saving to memory file: {str(e)}")
