"""Prompt builder for memory validation."""
from __future__ import annotations

from typing import Dict


def build_memory_prompt(payload: Dict[str, object]) -> str:
    memory_file = str(payload.get("memory_file", ""))
    memory_type = _memory_type_from_file(memory_file)
    key = str(payload.get("key", ""))
    value = str(payload.get("value", ""))

    product_context = payload.get("product_context", {}) or {}

    context_lines = [
        f"memory_file: {memory_file}",
        f"memory_type: {memory_type}",
        f"memory_key: {key}",
        f"memory_value: {value}",
    ]

    for field in [
        "source_eshop",
        "url",
        "short_description",
        "description",
        "variants",
        "main_photo",
        "gallery",
        "catalog_number",
        "manufacturer"
    ]:
        field_value = product_context.get(field)
        if field_value:
            context_lines.append(f"{field}: {field_value}")

    context_block = "\n".join(context_lines)

    return (
        "You are validating product memory mappings.\n"
        "Decide if the memory value is correct for the given product key.\n"
        "If needed, search the internet to verify product details.\n"
        "Use the product context, URL, and descriptions to identify the correct value.\n"
        "If no product context is available, validate only from key/value.\n"
        "\n"
        "RULES:\n"
        "- Return ONLY valid JSON.\n"
        "- Use 'yes' or 'no' for is_correct.\n"
        "- Provide correct_value even if is_correct is 'yes'.\n"
        "- reason must be short, keyword-style (no long sentences).\n"
        "- source should be a URL if available, otherwise 'provided_data'.\n"
        "\n"
        "MEMORY TYPE GUIDANCE:\n"
        "- ProductBrandMemory: value should be the brand.\n"
        "- ProductTypeMemory: value should be the product type (e.g., rubber, blade, apparel).\n"
        "- Only table tennis (ping-pong) terms are valid; reject non-table-tennis types (e.g., skateboard).\n"
        "- For rubbers, use the general type (e.g., 'potah'), not specific surface styles like 'trava' or 'sendvic'.\n"
        "- Avoid overly generic values; for apparel, always use a concrete clothing type (e.g., tričko, mikina, bunda), never just 'oblečení'.\n"
        "- ProductTypeMemory should be a simple noun phrase: ideally one noun, at most one adjective (e.g., 'teplakova souprava', 'ochranna folie'); avoid appended usage phrases like 'na pálku', 'na rezani'.\n"
        "- ProductModelMemory: value should be the model name without brand or type.\n"
        "- NameMemory: value must be 'Type Brand Model' and words must be capitalized except abbreviations and conjunctions.\n"
        "- CategoryMemory: value should be the internal category label.\n"
        "- CategoryNameMemory: value is the canonical category label.\n"
        "- CategoryMapping*: value is the target platform category path.\n"
        "- DescMemory: value is the full HTML description for the product.\n"
        "- ShortDescMemory: value is the short description.\n"
        "- VariantNameMemory: value is the normalized variant name.\n"
        "- VariantValueMemory: value is the normalized variant value.\n"
        "- StockStatusMemory: value is the normalized stock status in Czech.\n"
        "- KeywordsGoogle/KeywordsZbozi: value is keyword list for the platform.\n"
        "- The value 'Vyradit' is a valid category for CategoryMemory.\n"
        "- If the product name contains 'set', 'sada', or similar, this is always the primary type and overrides other types.\n"
        "\n"
        "PRODUCT CONTEXT:\n"
        f"{context_block}\n"
        "\n"
        "OUTPUT JSON:\n"
        "{\n"
        "  \"is_correct\": \"yes|no\",\n"
        "  \"correct_value\": \"...\",\n"
        "  \"reason\": [\"keyword1\", \"keyword2\"],\n"
        "  \"source\": \"...\"\n"
        "}\n"
    )


def _memory_type_from_file(memory_file: str) -> str:
    base = memory_file.replace("\\", "/").split("/")[-1]
    if base.endswith(".csv"):
        base = base[:-4]
    return base
