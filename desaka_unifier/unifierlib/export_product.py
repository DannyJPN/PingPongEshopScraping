"""
ExportProduct classes for desaka_unifier project.
Hierarchical structure with base class and specialized subclasses.
"""


class ExportProduct:
    """
    Base class for export products.
    Contains all properties that can be used by main products and variants.
    """

    def __init__(self):
        """
        Initialize empty ExportProduct.
        Constructor doesn't fill any properties.
        """
        # Product identification
        self.id: int = 0
        self.typ: str = ""
        self.varianta_id: str = ""
        self.varianta1_nazev: str = ""
        self.varianta1_hodnota: str = ""
        self.varianta2_nazev: str = ""
        self.varianta2_hodnota: str = ""
        self.varianta3_nazev: str = ""
        self.varianta3_hodnota: str = ""
        self.varianta_stejne: str = ""

        # Visibility and status
        self.zobrazit: int = 0
        self.archiv: int = 0

        # Basic product information
        self.kod: str = ""
        self.kod_vyrobku: str = ""
        self.ean: str = ""
        self.isbn: str = ""
        self.nazev: str = ""
        self.privlastek: str = ""
        self.vyrobce: str = ""
        self.dodavatel_id: str = ""

        # Pricing information
        self.cena: float = 0.0
        self.cena_bezna: float = 0.0
        self.cena_nakupni: str = ""
        self.recyklacni_poplatek: str = ""
        self.dph: int = 0
        self.sleva: float = 0.0
        self.sleva_od: str = ""
        self.sleva_do: str = ""

        # Description and content
        self.popis: str = ""
        self.popis_strucny: str = ""

        # Product attributes
        self.kosik: int = 0
        self.home: int = 0
        self.dostupnost: str = ""
        self.doprava_zdarma: int = 0
        self.dodaci_doba: str = ""
        self.dodaci_doba_auto: str = ""
        self.sklad: str = ""
        self.na_sklade: str = ""
        self.hmotnost: str = ""
        self.delka: str = ""
        self.jednotka: str = ""
        self.odber_po: int = 0
        self.odber_min: int = 0
        self.odber_max: str = ""
        self.pocet: int = 0
        self.zaruka: str = ""
        self.marze_dodavatel: str = ""

        # SEO and marketing
        self.seo_titulek: str = ""
        self.seo_popis: str = ""

        # Special properties
        self.eroticke: int = 0
        self.pro_dospele: int = 0
        self.slevovy_kupon: int = 0
        self.darek_objednavka: int = 0
        self.priorita: int = 0

        # Notes and tags
        self.poznamka: str = ""
        self.dodavatel_kod: str = ""
        self.stitky: str = ""
        self.cena_dodavatel: str = ""

        # Categories and related products
        self.kategorie_id: str = ""
        self.podobne: str = ""
        self.prislusenstvi: str = ""
        self.variantove: str = ""
        self.zdarma: str = ""
        self.sluzby: str = ""
        self.rozsirujici_obsah: str = ""

        # Zbozi.cz
        self.zbozicz_skryt: int = 0
        self.zbozicz_productname: str = ""
        self.zbozicz_product: str = ""
        self.zbozicz_cpc: int = 0
        self.zbozicz_cpc_search: int = 0
        self.zbozicz_kategorie: str = ""
        self.zbozicz_stitek_0: str = ""
        self.zbozicz_stitek_1: str = ""
        self.zbozicz_extra: str = ""

        # Heureka.cz
        self.heurekacz_skryt: int = 0
        self.heurekacz_productname: str = ""
        self.heurekacz_product: str = ""
        self.heurekacz_cpc: int = 0
        self.heurekacz_kategorie: str = ""

        # Google
        self.google_skryt: int = 0
        self.google_kategorie: str = ""
        self.google_stitek_0: str = ""
        self.google_stitek_1: str = ""
        self.google_stitek_2: str = ""
        self.google_stitek_3: str = ""
        self.google_stitek_4: str = ""

        # Glami
        self.glami_skryt: int = 0
        self.glami_kategorie: str = ""
        self.glami_cpc: int = 0
        self.glami_voucher: str = ""
        self.glami_material: str = ""
        self.glamisk_material: str = ""

        # Warehouse
        self.sklad_umisteni: str = ""
        self.sklad_minimalni: str = ""
        self.sklad_optimalni: str = ""
        self.sklad_maximalni: str = ""

    def __str__(self) -> str:
        """String representation of the export product."""
        return f"ExportProduct(id={self.id}, typ='{self.typ}', nazev='{self.nazev}')"


class ExportMainProduct(ExportProduct):
    """
    Main product class with default values for main products.
    Inherits all properties from ExportProduct.
    """

    def __init__(self):
        """
        Initialize ExportMainProduct with default values for main products.
        """
        super().__init__()
        # Set default values specific to main products (from your mapping)
        self.typ = "produkt"
        self.varianta_id = "#"
        self.varianta1_nazev = "#"
        self.varianta1_hodnota = "#"
        self.varianta2_nazev = "#"
        self.varianta2_hodnota = "#"
        self.varianta3_nazev = "#"
        self.varianta3_hodnota = "#"
        self.varianta_stejne = "#"
        self.zobrazit = 1
        self.archiv = 0
        self.kosik = 1
        self.home = 0
        self.dostupnost = "#"
        self.doprava_zdarma = 0
        self.dodaci_doba = "#"
        self.dodaci_doba_auto = "#"
        self.sklad = "#"
        self.na_sklade = "#"
        self.jednotka = "ks"
        self.odber_po = 1
        self.odber_min = 1
        self.pocet = 1
        self.eroticke = 0
        self.pro_dospele = 0
        self.slevovy_kupon = 1
        self.darek_objednavka = 1
        self.priorita = 0
        self.zbozicz_cpc = 5
        self.zbozicz_cpc_search = 5
        self.heurekacz_cpc = 1
        self.glami_cpc = 1
        self.sklad_umisteni = "#"
        self.sklad_minimalni = "#"
        self.sklad_optimalni = "#"
        self.sklad_maximalni = "#"


class ExportProductVariant(ExportProduct):
    """
    Product variant class with default values for variants.
    Inherits all properties from ExportProduct.
    """

    def __init__(self):
        """
        Initialize ExportProductVariant with default values for variants.
        """
        super().__init__()
        # Set default values specific to variants (from your mapping)
        self.typ = "varianta"
        self.varianta1_nazev = "#"
        self.varianta1_hodnota = "#"
        self.varianta2_nazev = "#"
        self.varianta2_hodnota = "#"
        self.varianta3_nazev = "#"
        self.varianta3_hodnota = "#"
        self.varianta_stejne = "#"
        self.zobrazit = "#"
        self.archiv = "#"
        self.isbn = "#"
        self.nazev = "#"
        self.privlastek = "#"
        self.vyrobce = "#"
        self.dodavatel_id = "#"
        self.recyklacni_poplatek = "#"
        self.dph = "#"
        self.sleva = "#"
        self.sleva_od = "#"
        self.sleva_do = "#"
        self.popis = "#"
        self.popis_strucny = "#"
        self.kosik = "#"
        self.home = "#"
        self.dostupnost = ""
        self.doprava_zdarma = "#"
        self.dodaci_doba = ""
        self.dodaci_doba_auto = "#"
        self.sklad = "#"
        self.na_sklade = "#"
        self.jednotka = "#"
        self.odber_po = "#"
        self.odber_min = "#"
        self.odber_max = "#"
        self.pocet = "#"
        self.zaruka = "#"
        self.marze_dodavatel = "#"
        self.seo_titulek = "#"
        self.seo_popis = "#"
        self.eroticke = "#"
        self.pro_dospele = "#"
        self.slevovy_kupon = "#"
        self.darek_objednavka = "#"
        self.priorita = "#"
        self.poznamka = "#"
        self.stitky = "#"
        self.kategorie_id = "#"
        self.podobne = "#"
        self.prislusenstvi = "#"
        self.variantove = "#"
        self.zdarma = "#"
        self.sluzby = "#"
        self.rozsirujici_obsah = "#"
        self.zbozicz_skryt = "#"
        self.zbozicz_productname = "#"
        self.zbozicz_product = "#"
        self.zbozicz_cpc = "#"
        self.zbozicz_cpc_search = "#"
        self.zbozicz_kategorie = "#"
        self.zbozicz_stitek_0 = "#"
        self.zbozicz_stitek_1 = "#"
        self.zbozicz_extra = "#"
        self.heurekacz_skryt = "#"
        self.heurekacz_productname = "#"
        self.heurekacz_product = "#"
        self.heurekacz_cpc = "#"
        self.heurekacz_kategorie = "#"
        self.google_skryt = "#"
        self.google_kategorie = "#"
        self.google_stitek_0 = "#"
        self.google_stitek_1 = "#"
        self.google_stitek_2 = "#"
        self.google_stitek_3 = "#"
        self.google_stitek_4 = "#"
        self.glami_skryt = "#"
        self.glami_kategorie = "#"
        self.glami_cpc = "#"
        self.glami_voucher = "#"
        self.glami_material = "#"
        self.glamisk_material = "#"
