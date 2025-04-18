def json_to_unified(data):

    mappings = []

    # Main product mapping
    base_mapping = {
        # Product identification
        'id': data.get('id'),
        'typ': 'produkt',
        'varianta_id': "#",
        'varianta1_nazev': "#",
        'varianta1_hodnota': "#",
        'varianta2_nazev': "#",
        'varianta2_hodnota': "#",
        'varianta3_nazev': "#",
        'varianta3_hodnota': "#",
        'varianta_stejne': "#",

        # Visibility and status
        'zobrazit': int(data.get('visibility', 1)),
        'archiv': int(data.get('archive', 0)),

        # Basic product information
        'kod': data.get('catalogNumber', ""),
        'kod_vyrobku': data.get('mpn', ""),
        'ean': data.get('ean', ""),
        'isbn': data.get('isbn', ""),
        'nazev': (data.get('translations') or {}).get('cs', {}).get('name', ""),
        'privlastek': (data.get('translations') or {}).get('cs', {}).get('nameext', ""),
        'vyrobce': (data.get('manufacturer') or {}).get('name', ""),
        'dodavatel_id': data.get('supplier_id', ""),

        # Pricing information
        'cena': data.get('price', 0),
        'cena_bezna': data.get('standardPrice', 0),
        'cena_nakupni': data.get('purchasePrice', ""),
        'recyklacni_poplatek': data.get('recycle_fee', ""),
        'dph': (data.get('vat') or {}).get('rate', 21),
        'sleva': data.get('discount', 0),
        'sleva_od': data.get('discount_from', ""),
        'sleva_do': data.get('discount_to', ""),

        # Description and content
        'popis': (data.get('translations') or {}).get('cs', {}).get('description', ""),
        'popis_strucny': (data.get('translations') or {}).get('cs', {}).get('annotation', ""),

        # Product attributes
        'kosik': int(data.get('sales', 1)),
        'home': int(data.get('homepage', 0)),
        'dostupnost': data.get('availability', "#"),
        'doprava_zdarma': int(data.get('deliveryFree', 0)),
        'dodaci_doba': data.get('deliveryTime', "#"),
        'dodaci_doba_auto': data.get('deliveryTimeAuto', "#"),
        'sklad': data.get('stock', "#"),
        'na_sklade': data.get('inStock', "#"),
        'hmotnost': data.get('weight', ""),
        'delka': data.get('length', ""),
        'jednotka': data.get('unit', "ks"),
        'odber_po': data.get('limitMultiple', 1),
        'odber_min': data.get('limitMin', 1),
        'odber_max': data.get('limitMax', ""),
        'pocet': data.get('quantityPack', 1),
        'zaruka': (data.get('guarantee') or {}).get('name', ""),
        'marze_dodavatel': data.get('margin', ""),

        # SEO and marketing
        'seo_titulek': (data.get('translations') or {}).get('cs', {}).get('metaTitle', ""),
        'seo_popis': (data.get('translations') or {}).get('cs', {}).get('metaDescription', ""),

        # Special properties
        'eroticke': int(data.get('erotic', 0)),
        'pro_dospele': int(data.get('adult', 0)),
        'slevovy_kupon': int(data.get('voucherDiscount', 1)),
        'darek_objednavka': int(data.get('gift_free', 1)),
        'priorita': data.get('priority', 0),

        # Notes and tags
        'poznamka': data.get('comment', ""),
        'stitky': ",".join([str((tag or {}).get('name', '')) for tag in data.get('tags', [])]),

        # Categories and related products
        'kategorie_id': ",".join([str((cat or {}).get('id', '')) for cat in data.get('categories', [])]),
        'podobne': ",".join([str((rel or {}).get('id', '')) for rel in data.get('related', [])]),
        'prislusenstvi': ",".join([str((acc or {}).get('id', '')) for acc in data.get('accessory', [])]),
        'variantove': ",".join([str((var or {}).get('id', '')) for var in data.get('variants', [])]),
        'zdarma': ",".join([str((fr or {}).get('id', '')) for fr in data.get('free', [])]),
        'sluzby': ",".join([str((serv or {}).get('id', '')) for serv in data.get('services', [])]),
        'rozsirujici_obsah': ",".join([str((ext or {}).get('id', '')) for ext in data.get('extended_content', [])]),

        # Zbozi.cz
        'zbozicz_skryt': int((data.get('feeds') or {}).get('zbozi', {}).get('hidden', 0)),
        'zbozicz_productname': (data.get('feeds') or {}).get('zbozi', {}).get('productname', ""),
        'zbozicz_product': (data.get('feeds') or {}).get('zbozi', {}).get('product', ""),
        'zbozicz_cpc': (data.get('feeds') or {}).get('zbozi', {}).get('cpc', 5),
        'zbozicz_cpc_search': (data.get('feeds') or {}).get('zbozi', {}).get('cpc_search', 5),
        'zbozicz_kategorie': (data.get('feeds') or {}).get('zbozi', {}).get('category', ""),
        'zbozicz_stitek_0': (data.get('feeds') or {}).get('zbozi', {}).get('customeLabel0', ""),
        'zbozicz_stitek_1': (data.get('feeds') or {}).get('zbozi', {}).get('customeLabel1', ""),
        'zbozicz_extra': (data.get('feeds') or {}).get('zbozi', {}).get('extraMessage', ""),

        # Heureka.cz
        'heurekacz_skryt': int((data.get('feeds') or {}).get('heurekacs', {}).get('hidden', 0)),
        'heurekacz_productname': (data.get('feeds') or {}).get('heurekacs', {}).get('productname', ""),
        'heurekacz_product': (data.get('feeds') or {}).get('heurekacs', {}).get('product', ""),
        'heurekacz_cpc': (data.get('feeds') or {}).get('heurekacs', {}).get('cpc', 5),
        'heurekacz_kategorie': (data.get('feeds') or {}).get('heurekacs', {}).get('category', ""),

        # Google
        'google_skryt': int((data.get('feeds') or {}).get('google', {}).get('hidden', 0)),
        'google_kategorie': (data.get('feeds') or {}).get('google', {}).get('category', ""),
        'google_stitek_0': (data.get('feeds') or {}).get('google', {}).get('customeLabel0', ""),
        'google_stitek_1': (data.get('feeds') or {}).get('google', {}).get('customeLabel1', ""),
        'google_stitek_2': (data.get('feeds') or {}).get('google', {}).get('customeLabel2', ""),
        'google_stitek_3': (data.get('feeds') or {}).get('google', {}).get('customeLabel3', ""),
        'google_stitek_4': (data.get('feeds') or {}).get('google', {}).get('customeLabel4', ""),

        # Glami
        'glami_skryt': int((data.get('feeds') or {}).get('glami', {}).get('hidden', 0)),
        'glami_kategorie': (data.get('feeds') or {}).get('glami', {}).get('category', ""),
        'glami_cpc': (data.get('feeds') or {}).get('glami', {}).get('cpc', 1),
        'glami_voucher': (data.get('feeds') or {}).get('glami', {}).get('promotionId', ""),
        'glami_material': (data.get('feeds') or {}).get('glami', {}).get('material', ""),
        'glamisk_material': (data.get('feeds') or {}).get('glami', {}).get('material', ""),

        # Warehouse
        'sklad_umisteni': (data.get('warehouse') or {}).get('location', "#"),
        'sklad_minimalni': (data.get('warehouse') or {}).get('stockMinimum', "#"),
        'sklad_optimalni': (data.get('warehouse') or {}).get('stockOptimal', "#"),
        'sklad_maximalni': (data.get('warehouse') or {}).get('stockMaximum', "#")
    }

    # Add main product mapping
    mappings.append(base_mapping)

    # Process variants
    for variant in data.get('variants', []):
        variant_mapping = {
            'typ': 'varianta',
            'varianta_id': variant.get('id'),
            'varianta1_nazev': "",
            'varianta1_hodnota': "",
            'varianta2_nazev': "",
            'varianta2_hodnota': "",
            'varianta3_nazev': "",
            'varianta3_hodnota': "",
            'varianta_stejne': "1",

            'zobrazit': "#",
            'archiv': "#",

            'kod': variant.get('catalogNumber', ""),
            'kod_vyrobku': variant.get('mpn', ""),
            'ean': variant.get('ean', ""),
            'isbn': "#",
            'nazev': "#",
            'privlastek': "#",
            'vyrobce': "#",
            'dodavatel_id': "#",

            'cena': variant.get('price', 0),
            'cena_bezna': variant.get('standardPrice', 0),
            'cena_nakupni': variant.get('purchasePrice', ""),
            'recyklacni_poplatek': "#",
            'dph': "#",
            'sleva': "#",
            'sleva_od': "#",
            'sleva_do': "#",

            'popis': "#",
            'popis_strucny': "#",

            'kosik': "#",
            'home': "#",
            'dostupnost': ".",
            'doprava_zdarma': "#",
            'dodaci_doba': "#",
            'dodaci_doba_auto': "#",
            'sklad': "#",
            'na_sklade': "#",
            'hmotnost': variant.get('weight', ""),
            'delka': variant.get('length', ""),
            'jednotka': "#",
            'odber_po': "#",
            'odber_min': "#",
            'odber_max': "#",
            'pocet': "#",
            'zaruka': "#",
            'marze_dodavatel': "#",

            'seo_titulek': "#",
            'seo_popis': "#",

            'eroticke': "#",
            'pro_dospele': "#",
            'slevovy_kupon': "#",
            'darek_objednavka': "#",
            'priorita': "#",

            'poznamka': "#",
            'stitky': "#",

            'kategorie_id': "#",
            'podobne': "#",
            'prislusenstvi': "#",
            'variantove': "#",
            'zdarma': "#",
            'sluzby': "#",
            'rozsirujici_obsah': "#",

            'zbozicz_skryt': "#",
            'zbozicz_productname': "#",
            'zbozicz_product': "#",
            'zbozicz_cpc': "#",
            'zbozicz_cpc_search': "#",
            'zbozicz_kategorie': "#",
            'zbozicz_stitek_0': "#",
            'zbozicz_stitek_1': "#",
            'zbozicz_extra': "#",

            'heurekacz_skryt': "#",
            'heurekacz_productname': "#",
            'heurekacz_product': "#",
            'heurekacz_cpc': "#",
            'heurekacz_kategorie': "#",

            'google_skryt': "#",
            'google_kategorie': "#",
            'google_stitek_0': "#",
            'google_stitek_1': "#",
            'google_stitek_2': "#",
            'google_stitek_3': "#",
            'google_stitek_4': "#",

            'glami_skryt': "#",
            'glami_kategorie': "#",
            'glami_cpc': "#",
            'glami_voucher': "#",
            'glami_material': "#",
            'glamisk_material': "#",

            'sklad_umisteni': (variant.get('warehouse') or {}).get('location', ""),
            'sklad_minimalni': (variant.get('warehouse') or {}).get('stockMinimum', ""),
            'sklad_optimalni': (variant.get('warehouse') or {}).get('stockOptimal', ""),
            'sklad_maximalni': (variant.get('warehouse') or {}).get('stockMaximum', "")
        }

        # Process variant options
        if variant.get('options'):
            for i, option in enumerate(variant.get('options', []), 1):
                if i <= 3:  # Maximum 3 variants
                    variant_mapping[f'varianta{i}_nazev'] = (option or {}).get('name', "").strip()
                    variant_mapping[f'varianta{i}_hodnota'] = (option or {}).get('value', "").strip()

        mappings.append(variant_mapping)

    return mappings
    
    
def csv_to_downloaded(data):
    mappings = []

    # Main product mapping
    base_mapping = {
        'name': data.get('Name',""),
        'short_description': data.get('Short Description',""),
        'description': data.get('Description',""),
        'main_photo_filepath': data.get('Main Photo Filepath',""),
        'gallery_photo_filepaths': data.get('Gallery Filepaths',""),
        'variants': data.get('Variants',""),
        'url': data.get('URL',"")
    }
    mappings.append(base_mapping)
    return mappings
