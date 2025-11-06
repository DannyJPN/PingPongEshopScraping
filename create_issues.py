#!/usr/bin/env python3
"""
Create GitHub Issues for missing memory entries.
"""
import subprocess
import os
import sys

# Configuration
issues_config = [
    # ProductBrandMemory_CS.csv
    {
        "eshop": "SpinWay",
        "memory_type": "ProductBrandMemory",
        "count": 261,
        "missing_file": "desaka_unifier/Memory/Consolidated/ProductBrandMemory_CS.csv/SpinWayOutput.csv_MISSING.txt",
        "ai_method": "find_brand",
        "ai_lines": "181-200",
        "value_rule": "Značky (brands) se NEPŘEKLÁDAJÍ - zůstává název výrobce v originále",
        "value_examples": '"Nittaku","Nittaku" nebo "Butterfly","Butterfly"'
    },
    {
        "eshop": "SportSpin",
        "memory_type": "ProductBrandMemory",
        "count": 427,
        "missing_file": "desaka_unifier/Memory/Consolidated/ProductBrandMemory_CS.csv/SportSpinOutput.csv_MISSING.txt",
        "ai_method": "find_brand",
        "ai_lines": "181-200",
        "value_rule": "Značky (brands) se NEPŘEKLÁDAJÍ - zůstává název výrobce v originále",
        "value_examples": '"Nittaku","Nittaku" nebo "Butterfly","Butterfly"'
    },
    {
        "eshop": "Stoten",
        "memory_type": "ProductBrandMemory",
        "count": 51,
        "missing_file": "desaka_unifier/Memory/Consolidated/ProductBrandMemory_CS.csv/StotenOutput.csv_MISSING.txt",
        "ai_method": "find_brand",
        "ai_lines": "181-200",
        "value_rule": "Značky (brands) se NEPŘEKLÁDAJÍ - zůstává název výrobce v originále",
        "value_examples": '"Nittaku","Nittaku" nebo "Butterfly","Butterfly"'
    },
    {
        "eshop": "VseNaStolniTenis",
        "memory_type": "ProductBrandMemory",
        "count": 138,
        "missing_file": "desaka_unifier/Memory/Consolidated/ProductBrandMemory_CS.csv/VseNaStolniTenisOutput.csv_MISSING.txt",
        "ai_method": "find_brand",
        "ai_lines": "181-200",
        "value_rule": "Značky (brands) se NEPŘEKLÁDAJÍ - zůstává název výrobce v originále",
        "value_examples": '"Nittaku","Nittaku" nebo "Butterfly","Butterfly"'
    },
    # ProductModelMemory_CS.csv
    {
        "eshop": "Nittaku",
        "memory_type": "ProductModelMemory",
        "count": 108,
        "missing_file": "desaka_unifier/Memory/Consolidated/ProductModelMemory_CS.csv/NittakuOutput.csv_MISSING.txt",
        "ai_method": "get_product_model",
        "ai_lines": "769-782",
        "value_rule": "Model se obvykle NEPŘEKLÁDÁ - zůstává originální název (Hurricane 3, Tenergy 05, atd.)",
        "value_examples": '"Nittaku Hurricane 3","Hurricane 3" nebo "Butterfly Tenergy 05","Tenergy 05"'
    },
    {
        "eshop": "SpinWay",
        "memory_type": "ProductModelMemory",
        "count": 802,
        "missing_file": "desaka_unifier/Memory/Consolidated/ProductModelMemory_CS.csv/SpinWayOutput.csv_MISSING.txt",
        "ai_method": "get_product_model",
        "ai_lines": "769-782",
        "value_rule": "Model se obvykle NEPŘEKLÁDÁ - zůstává originální název (Hurricane 3, Tenergy 05, atd.)",
        "value_examples": '"Nittaku Hurricane 3","Hurricane 3" nebo "Butterfly Tenergy 05","Tenergy 05"'
    },
    {
        "eshop": "SportSpin",
        "memory_type": "ProductModelMemory",
        "count": 1168,
        "missing_file": "desaka_unifier/Memory/Consolidated/ProductModelMemory_CS.csv/SportSpinOutput.csv_MISSING.txt",
        "ai_method": "get_product_model",
        "ai_lines": "769-782",
        "value_rule": "Model se obvykle NEPŘEKLÁDÁ - zůstává originální název (Hurricane 3, Tenergy 05, atd.)",
        "value_examples": '"Nittaku Hurricane 3","Hurricane 3" nebo "Butterfly Tenergy 05","Tenergy 05"'
    },
    {
        "eshop": "Stoten",
        "memory_type": "ProductModelMemory",
        "count": 1186,
        "missing_file": "desaka_unifier/Memory/Consolidated/ProductModelMemory_CS.csv/StotenOutput.csv_MISSING.txt",
        "ai_method": "get_product_model",
        "ai_lines": "769-782",
        "value_rule": "Model se obvykle NEPŘEKLÁDÁ - zůstává originální název (Hurricane 3, Tenergy 05, atd.)",
        "value_examples": '"Nittaku Hurricane 3","Hurricane 3" nebo "Butterfly Tenergy 05","Tenergy 05"'
    },
    {
        "eshop": "VseNaStolniTenis",
        "memory_type": "ProductModelMemory",
        "count": 2058,
        "missing_file": "desaka_unifier/Memory/Consolidated/ProductModelMemory_CS.csv/VseNaStolniTenisOutput.csv_MISSING.txt",
        "ai_method": "get_product_model",
        "ai_lines": "769-782",
        "value_rule": "Model se obvykle NEPŘEKLÁDÁ - zůstává originální název (Hurricane 3, Tenergy 05, atd.)",
        "value_examples": '"Nittaku Hurricane 3","Hurricane 3" nebo "Butterfly Tenergy 05","Tenergy 05"'
    },
    # ProductTypeMemory_CS.csv
    {
        "eshop": "SpinWay",
        "memory_type": "ProductTypeMemory",
        "count": 3,
        "missing_file": "desaka_unifier/Memory/Consolidated/ProductTypeMemory_CS.csv/SpinWayOutput.csv_MISSING.txt",
        "ai_method": "get_product_type",
        "ai_lines": "721-734",
        "value_rule": 'Typ MUSÍ být ČESKY! ("Potah" ne "Rubber", "Dřevo" ne "Blade", "Míček" ne "Ball")',
        "value_examples": '"Butterfly Tenergy 05","Potah" nebo "Nittaku Acoustic","Dřevo"'
    },
    {
        "eshop": "SportSpin",
        "memory_type": "ProductTypeMemory",
        "count": 499,
        "missing_file": "desaka_unifier/Memory/Consolidated/ProductTypeMemory_CS.csv/SportSpinOutput.csv_MISSING.txt",
        "ai_method": "get_product_type",
        "ai_lines": "721-734",
        "value_rule": 'Typ MUSÍ být ČESKY! ("Potah" ne "Rubber", "Dřevo" ne "Blade", "Míček" ne "Ball")',
        "value_examples": '"Butterfly Tenergy 05","Potah" nebo "Nittaku Acoustic","Dřevo"'
    },
    {
        "eshop": "Stoten",
        "memory_type": "ProductTypeMemory",
        "count": 346,
        "missing_file": "desaka_unifier/Memory/Consolidated/ProductTypeMemory_CS.csv/StotenOutput.csv_MISSING.txt",
        "ai_method": "get_product_type",
        "ai_lines": "721-734",
        "value_rule": 'Typ MUSÍ být ČESKY! ("Potah" ne "Rubber", "Dřevo" ne "Blade", "Míček" ne "Ball")',
        "value_examples": '"Butterfly Tenergy 05","Potah" nebo "Nittaku Acoustic","Dřevo"'
    },
    {
        "eshop": "VseNaStolniTenis",
        "memory_type": "ProductTypeMemory",
        "count": 826,
        "missing_file": "desaka_unifier/Memory/Consolidated/ProductTypeMemory_CS.csv/VseNaStolniTenisOutput.csv_MISSING.txt",
        "ai_method": "get_product_type",
        "ai_lines": "721-734",
        "value_rule": 'Typ MUSÍ být ČESKY! ("Potah" ne "Rubber", "Dřevo" ne "Blade", "Míček" ne "Ball")',
        "value_examples": '"Butterfly Tenergy 05","Potah" nebo "Nittaku Acoustic","Dřevo"'
    },
]

# AI prompts
ai_prompts = {
    "find_brand": """I respectfully ask you to:
1. Search the internet for information about table tennis brands and manufacturers
2. Check pincesobchod.cz for brand information and product listings
3. Carefully analyze the product information
4. Select EXACTLY ONE brand from the list above
5. The brand must be chosen strictly from the provided list
6. Keep brand names in their original language (manufacturer names should not be translated)
7. If any explanatory text is needed, translate it to {target_language} using proper table tennis terminology
8. Use your knowledge of current table tennis brand landscape
9. Return the result as JSON with the property "brand" """,

    "get_product_type": """I respectfully ask you to:
1. Analyze the product information carefully
2. Determine the general product type (e.g., "Laptop", "Shirt", "Ball", "Racket")
3. Translate the product type to {target_language} using proper table tennis terminology (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
4. Keep it concise and general (not specific model)
5. Use {target_language} language for the type
6. Return the result as JSON with the property "type" """,

    "get_product_model": """I respectfully ask you to:
1. Analyze the product information thoroughly
2. Extract the specific model name/number (e.g., "ROG Strix", "Air Max 90", "Pro V1")
3. If the model name is not in {target_language}, translate descriptive parts to {target_language} using proper table tennis terminology (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
4. Keep brand-specific model names in their original form when appropriate
5. Keep it concise and specific to the model
6. Return the result as JSON with the property "model" """
}

tt_terminology = """## Stolní tenis terminologie

```
"rubber" = "Potah" (NIKDY "Guma"!)
"blade" = "Dřevo" (NIKDY "Čepel"!)
"ball" = "Míček"
"paddle/racket" = "Pálka"
"case" = "Pouzdro"
"cleaner" = "Čistič"
"glue" = "Lepidlo"
"sponge" = "Houba"
"shirt" = "Tričko" / "Dres"
"shorts" = "Kraťasy"
"shoes" = "Boty"
"bag" = "Taška"
"net" = "Síťka"
"table" = "Stůl"
```"""

def read_missing_file(filepath):
    """Read MISSING file with UTF-16 LE encoding."""
    full_path = os.path.join("F:/Dropbox/Scripts/Python/Desaka", filepath)
    try:
        with open(full_path, 'r', encoding='utf-16-le') as f:
            content = f.read().strip()
            # Remove BOM if present
            if content.startswith('\ufeff'):
                content = content[1:]
            return content
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return ""

def create_issue(config):
    """Create a GitHub issue for a memory file."""
    import tempfile
    eshop = config["eshop"]
    memory_type = config["memory_type"]
    count = config["count"]
    missing_file = config["missing_file"]
    ai_method = config["ai_method"]
    ai_lines = config["ai_lines"]
    value_rule = config["value_rule"]
    value_examples = config["value_examples"]

    # Read MISSING file content
    missing_content = read_missing_file(missing_file)

    if not missing_content:
        print(f"WARNING: Skipping {eshop}/{memory_type} - empty MISSING file", file=sys.stderr)
        return None

    # Build issue title
    title = f"[Memory] Doplnit {memory_type} z {eshop} ({count} polozek)"

    # Build issue body
    terminology_section = tt_terminology if memory_type == "ProductTypeMemory" else ""

    body = f"""## Prehled ukolu

Doplnit **{count} chybejicich zaznamu** z eshopu **{eshop}** do souboru `{memory_type}_CS.csv`.

## KRITICKE - Pravidlo jazyku

```
KEY (klic)      = Originalni jazyk a podoba (z eshopu {eshop})
VALUE (hodnota) = VZDY CESKY! (soubor konci _CS.csv)
```

**Priklady:**
```csv
{value_examples}
```

POZOR: {value_rule}

## Umisteni souboru

- **Cilovy memory soubor:** `desaka_unifier/Memory/{memory_type}_CS.csv`
- **Seznam chybejicich klicu:** `{missing_file}`

## Jak AI generuje hodnoty

Z `openai_unifier.py::{ai_method}()` (radky {ai_lines}):

```
{ai_prompts[ai_method]}
```

{terminology_section}

## Postup reseni

1. Precist chybejici klice z MISSING souboru (UTF-16 LE encoding)
2. Pro kazdy klic (ktery zustane BEZE ZMENY):
   - Vyhledat informace o produktu:
     - **pincesobchod.cz** - hlavni zdroj pro stolni tenis
     - Oficialni stranky vyrobcu
     - Google/web search
   - Pouzit existujici zaznamy v memory souboru jako referenci
   - Podle AI promptu urcit spravnou CESKOU hodnotu
3. Doplnit nove zaznamy do CSV:
   ```csv
   "ORIGINALNI_KEY","CESKA_VALUE"
   ```
4. Zachovat format CSV s uvozovkami

## Kompletni obsah MISSING souboru

```
{missing_content}
```

## Uzitecne zdroje

- https://pincesobchod.cz - cesky e-shop se stolnim tenisem
- https://nittaku.com, https://butterfly.tt, https://tibhar.com - oficialni stranky vyrobcu
- `desaka_unifier/Memory/BrandCodeList.csv` - seznam znamych znacek
"""

    # Create issue using gh CLI with temp file for body
    try:
        # Write body to temp file due to Windows command line length limits
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.md') as tmp:
            tmp.write(body)
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                ["gh", "issue", "create", "--title", title, "--label", "enhancement", "--body-file", tmp_path],
                cwd="F:/Dropbox/Scripts/Python/Desaka",
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if result.returncode == 0:
                issue_url = result.stdout.strip()
                print(f"OK: Created {issue_url}")
                return issue_url
            else:
                print(f"ERROR creating issue for {eshop}/{memory_type}: {result.stderr}")
                return None
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
    except Exception as e:
        print(f"EXCEPTION creating issue for {eshop}/{memory_type}: {e}")
        return None

def main():
    """Main entry point."""
    print("Creating GitHub Issues for missing memory entries...")
    print()

    created_issues = []

    for config in issues_config:
        eshop = config["eshop"]
        memory_type = config["memory_type"]
        print(f"Creating issue for {eshop} / {memory_type}...")

        issue_url = create_issue(config)
        if issue_url:
            created_issues.append({
                "eshop": eshop,
                "memory_type": memory_type,
                "count": config["count"],
                "url": issue_url
            })

    print()
    print(f"SUCCESS: Created {len(created_issues)} issues out of {len(issues_config)}")
    print()
    print("Created Issues:")
    for issue in created_issues:
        print(f"  - [{issue['eshop']}] {issue['memory_type']} ({issue['count']} items): {issue['url']}")

if __name__ == "__main__":
    main()
