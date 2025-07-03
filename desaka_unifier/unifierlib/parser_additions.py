"""
Dočasný soubor s metodami pro implementaci do parser.py
"""

def _clean_brand_value(self, brand_value: str) -> str:
    """
    Ensure brand value doesn't contain product type or model information.
    Uses BrandCodeList as a reference for valid brands.
    """
    if not brand_value:
        return ""

    # Get reference list of valid brands
    brand_list = self.memory.get(MEMORY_KEY_BRAND_CODE_LIST, {})
    if not brand_list:
        return brand_value

    # Find the closest matching brand from the BrandCodeList
    best_match = ""
    for valid_brand in brand_list.keys():
        if valid_brand.lower() in brand_value.lower():
            # Choose the longest matching brand name
            if len(valid_brand) > len(best_match):
                best_match = valid_brand

    # If we found a match, use it instead of the potentially contaminated value
    return best_match if best_match else brand_value

def _get_product_type(self, downloaded: DownloadedProduct, brand: str) -> str:
    """
    Get product type from memory or OpenAI with user confirmation.
    Ensures the type doesn't contain brand or model information.
    """
    memory_key = MEMORY_KEY_PRODUCT_TYPE_MEMORY.format(language=self.language)
    if memory_key in self.memory:
        type_memory = self.memory[memory_key]
        if downloaded.name in type_memory:
            product_type = type_memory[downloaded.name]
            # Clean type to ensure it doesn't contain brand or model references
            product_type = self._clean_type_value(product_type, brand)
            return product_type

    # Use OpenAI if memory is empty or product not found
    if self.openai:
        product_type = self.openai.find_product_type(downloaded, self.language)
        if product_type:
            # Clean type before confirming with user
            product_type = self._clean_type_value(product_type, brand)

            # Confirm with user if needed
            confirmed_type = self._confirm_ai_result(
                "Product Type", "", product_type, downloaded.name, downloaded.url
            )
            if confirmed_type:
                # Save to memory
                if memory_key not in self.memory:
                    self.memory[memory_key] = {}
                self.memory[memory_key][downloaded.name] = confirmed_type
                self._save_memory_file(memory_key)
                return confirmed_type

    # Ask user directly if AI not available or failed
    user_type = self._ask_user_for_product_value("Product Type", downloaded)
    if user_type:
        # Clean type before saving to memory
        user_type = self._clean_type_value(user_type, brand)

        # Save to memory
        if memory_key not in self.memory:
            self.memory[memory_key] = {}
        self.memory[memory_key][downloaded.name] = user_type
        self._save_memory_file(memory_key)
        return user_type

    return ""

def _clean_type_value(self, product_type: str, brand: str) -> str:
    """
    Ensure product type value doesn't contain brand information.
    """
    if not product_type:
        return ""

    # Get brand memory to ensure type doesn't contain brand information
    cleaned_type = product_type

    # Remove brand from type if present
    if brand and brand in cleaned_type:
        cleaned_type = cleaned_type.replace(brand, "").strip()

    # Check against all brands in BrandCodeList
    brand_list = self.memory.get(MEMORY_KEY_BRAND_CODE_LIST, {})
    for valid_brand in brand_list.keys():
        if valid_brand in cleaned_type:
            cleaned_type = cleaned_type.replace(valid_brand, "").strip()

    # Remove extra spaces
    cleaned_type = " ".join(cleaned_type.split())

    return cleaned_type

def _get_product_model(self, downloaded: DownloadedProduct, brand: str, product_type: str) -> str:
    """
    Get product model from memory or OpenAI with user confirmation.
    Ensures the model doesn't contain brand or type information.
    """
    memory_key = MEMORY_KEY_PRODUCT_MODEL_MEMORY.format(language=self.language)
    if memory_key in self.memory:
        model_memory = self.memory[memory_key]
        if downloaded.name in model_memory:
            model = model_memory[downloaded.name]
            # Clean model to ensure it doesn't contain brand or type references
            model = self._clean_model_value(model, brand, product_type)
            return model

    # Use OpenAI if memory is empty or product not found
    if self.openai:
        model = self.openai.find_product_model(downloaded, self.language)
        if model:
            # Clean model before confirming with user
            model = self._clean_model_value(model, brand, product_type)

            # Confirm with user if needed
            confirmed_model = self._confirm_ai_result(
                "Product Model", "", model, downloaded.name, downloaded.url
            )
            if confirmed_model:
                # Save to memory
                if memory_key not in self.memory:
                    self.memory[memory_key] = {}
                self.memory[memory_key][downloaded.name] = confirmed_model
                self._save_memory_file(memory_key)
                return confirmed_model

    # Ask user directly if AI not available or failed
    user_model = self._ask_user_for_product_value("Product Model", downloaded)
    if user_model:
        # Clean model before saving to memory
        user_model = self._clean_model_value(user_model, brand, product_type)

        # Save to memory
        if memory_key not in self.memory:
            self.memory[memory_key] = {}
        self.memory[memory_key][downloaded.name] = user_model
        self._save_memory_file(memory_key)
        return user_model

    return ""

def _clean_model_value(self, model: str, brand: str, product_type: str) -> str:
    """
    Ensure model value doesn't contain brand or type information.
    """
    if not model:
        return ""

    cleaned_model = model

    # Remove brand from model if present
    if brand and brand in cleaned_model:
        cleaned_model = cleaned_model.replace(brand, "").strip()

    # Remove type from model if present
    if product_type and product_type in cleaned_model:
        cleaned_model = cleaned_model.replace(product_type, "").strip()

    # Check against all brands in BrandCodeList to ensure no brand remains
    brand_list = self.memory.get(MEMORY_KEY_BRAND_CODE_LIST, {})
    for valid_brand in brand_list.keys():
        if valid_brand in cleaned_model:
            cleaned_model = cleaned_model.replace(valid_brand, "").strip()

    # Remove extra spaces
    cleaned_model = " ".join(cleaned_model.split())

    return cleaned_model
