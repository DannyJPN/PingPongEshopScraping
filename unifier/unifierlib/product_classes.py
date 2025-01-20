from dataclasses import dataclass, field
from typing import Dict, Any, Optional, ClassVar
import logging

@dataclass
class UnifiedExportProduct:
    """Base class for unified export products."""

    # Class variable to store defaults
    defaults: ClassVar[Dict[str, Dict[str, str]]] = {}

    # Identifikace produktu
    id: str = field(default="#")
    typ: str = field(default="#")
    varianta_id: str = field(default="#")
    varianta1_nazev: str = field(default="#")
    varianta1_hodnota: str = field(default="#")
    varianta2_nazev: str = field(default="#")
    varianta2_hodnota: str = field(default="#")
    varianta3_nazev: str = field(default="#")
    varianta3_hodnota: str = field(default="#")
    varianta_stejne: str = field(default="#")

    # Viditelnost a stav produktu
    zobrazit: int = field(default=1)
    archiv: int = field(default=0)

    # Základní informace o produktu
    kod: str = field(default="#")
    kod_vyrobku: str = field(default="#")
    ean: str = field(default="#")
    isbn: str = field(default="#")
    nazev: str = field(default="#")
    privlastek: str = field(default="#")
    vyrobce: str = field(default="#")
    dodavatel_id: str = field(default="#")

    # Cenové informace
    cena: float = field(default=0.0)
    cena_bezna: float = field(default=0.0)
    cena_nakupni: float = field(default=0.0)
    recyklacni_poplatek: float = field(default=0.0)
    dph: int = field(default=21)
    sleva: float = field(default=0.0)
    sleva_od: str = field(default="#")
    sleva_do: str = field(default="#")

    # Popis a obsah
    popis: str = field(default="#")
    popis_strucny: str = field(default="#")

    # Atributy produktu
    kosik: int = field(default=1)
    home: int = field(default=0)
    dostupnost: str = field(default="#")
    doprava_zdarma: int = field(default=0)
    dodaci_doba: str = field(default="#")
    dodaci_doba_auto: str = field(default="#")
    sklad: str = field(default="#")
    na_sklade: str = field(default="#")
    hmotnost: float = field(default=0.0)
    delka: float = field(default=0.0)
    jednotka: str = field(default="ks")
    odber_po: int = field(default=1)
    odber_min: int = field(default=1)
    odber_max: str = field(default="#")
    pocet: int = field(default=1)
    zaruka: str = field(default="#")
    marze_dodavatel: str = field(default="#")

    # SEO a marketing
    seo_titulek: str = field(default="#")
    seo_popis: str = field(default="#")

    # Speciální vlastnosti
    eroticke: int = field(default=0)
    pro_dospele: int = field(default=0)
    slevovy_kupon: int = field(default=1)
    darek_objednavka: int = field(default=1)
    priorita: int = field(default=0)

    # Poznámky a štítky
    poznamka: str = field(default="#")
    stitky: str = field(default="#")

    # Kategorie a související produkty
    kategorie_id: str = field(default="#")
    podobne: str = field(default="#")
    prislusenstvi: str = field(default="#")
    variantove: str = field(default="#")
    zdarma: str = field(default="#")
    sluzby: str = field(default="#")
    rozsirujici_obsah: str = field(default="#")

    # Zbozi.cz
    zbozicz_skryt: int = field(default=0)
    zbozicz_productname: str = field(default="#")
    zbozicz_product: str = field(default="#")
    zbozicz_cpc: float = field(default=5.0)
    zbozicz_cpc_search: float = field(default=5.0)
    zbozicz_kategorie: str = field(default="#")
    zbozicz_stitek_0: str = field(default="#")
    zbozicz_stitek_1: str = field(default="#")
    zbozicz_extra: str = field(default="#")

    # Heureka.cz
    heurekacz_skryt: int = field(default=0)
    heurekacz_productname: str = field(default="#")
    heurekacz_product: str = field(default="#")
    heurekacz_cpc: float = field(default=1.0)
    heurekacz_kategorie: str = field(default="#")

    # Google
    google_skryt: int = field(default=0)
    google_kategorie: str = field(default="#")
    google_stitek_0: str = field(default="#")
    google_stitek_1: str = field(default="#")
    google_stitek_2: str = field(default="#")
    google_stitek_3: str = field(default="#")
    google_stitek_4: str = field(default="#")

    # Glami
    glami_skryt: int = field(default=0)
    glami_kategorie: str = field(default="#")
    glami_cpc: float = field(default=1.0)
    glami_voucher: str = field(default="#")
    glami_material: str = field(default="#")
    glamisk_material: str = field(default="#")

    # Sklad
    sklad_umisteni: str = field(default="#")
    sklad_minimalni: str = field(default="#")
    sklad_optimalni: str = field(default="#")
    sklad_maximalni: str = field(default="#")

    def __init__(self, defaults: Dict[str, str]):
        """
        Initialize attributes with their default values.

        Args:
            defaults: Dictionary of default values for product attributes
        """
        try:
            logging.debug(f"Initializing {self.__class__.__name__} with defaults")
            for attr_name in self.__annotations__:
                if attr_name == 'defaults':  # Skip ClassVar
                    continue

                attr_type = self.__annotations__[attr_name]
                default_value = defaults.get(attr_name, "#")

                try:
                    if attr_type == float:
                        value = float(default_value) if default_value != "#" else 0.0
                    elif attr_type == int:
                        value = int(default_value) if default_value != "#" else 0
                    else:
                        value = default_value
                    setattr(self, attr_name, value)
                except (ValueError, TypeError) as e:
                    logging.warning(f"Failed to convert value for {attr_name}: {e}")
                    setattr(self, attr_name, "#" if attr_type == str else 0)

        except Exception as e:
            logging.error(f"Error initializing {self.__class__.__name__}: {str(e)}", exc_info=True)
            raise

    def update_from_json(self, json_data: Dict[str, Any]) -> None:
        """
        Update attributes from JSON data.

        Args:
            json_data: Dictionary containing product data from JSON
        """
        try:
            logging.debug(f"Updating {self.__class__.__name__} from JSON data")
            for key, value in json_data.items():
                if hasattr(self, key):
                    attr_type = self.__annotations__.get(key)
                    if isinstance(value, str) and not value.strip():
                        value = "#"
                    elif value is not None and attr_type:
                        try:
                            if attr_type == int:
                                value = int(value)
                            elif attr_type == float:
                                value = float(value)
                        except (ValueError, TypeError) as e:
                            logging.warning(f"Failed to convert value '{value}' for attribute '{key}': {e}")
                            value = "#" if attr_type == str else 0
                    setattr(self, key, value)
                else:
                    logging.warning(f"Attribute '{key}' not found in {self.__class__.__name__}")
        except Exception as e:
            logging.error(f"Error updating {self.__class__.__name__} from JSON: {str(e)}", exc_info=True)
            raise

    def validate(self) -> bool:
        """
        Validate required attributes are set.

        Returns:
            bool: True if validation passes, False otherwise
        """
        try:
            required_attrs = ['kod', 'nazev', 'cena']
            for attr in required_attrs:
                value = getattr(self, attr)
                if value in (None, "#") or (isinstance(value, str) and not value.strip()):
                    logging.error(f"Required attribute '{attr}' is empty in {self.__class__.__name__}")
                    return False
            return True
        except Exception as e:
            logging.error(f"Error validating {self.__class__.__name__}: {str(e)}", exc_info=True)
            return False

@dataclass
class UnifiedExportProductMain(UnifiedExportProduct):
    """Main product class containing core product information."""

    pocet_variant: int = field(default=0)
    atributy_variant: str = field(default="#")

    def __init__(self, defaults: Dict[str, str]):
        """
        Initialize main product with default values.

        Args:
            defaults: Dictionary of default values for main product attributes
        """
        try:
            super().__init__(defaults)
            self.typ = "produkt"
            logging.debug("Initialized UnifiedExportProductMain")
        except Exception as e:
            logging.error("Error initializing UnifiedExportProductMain", exc_info=True)
            raise

@dataclass
class UnifiedExportProductVariant(UnifiedExportProduct):
    """Product variant class containing variant-specific information."""

    nadrazeny_kod: str = field(default="#")
    typ_varianty: str = field(default="#")
    hodnota_varianty: str = field(default="#")
    pozice_varianty: int = field(default=0)

    def __init__(self, defaults: Dict[str, str]):
        """
        Initialize product variant with default values.

        Args:
            defaults: Dictionary of default values for variant attributes
        """
        try:
            super().__init__(defaults)
            self.typ = "varianta"
            logging.debug("Initialized UnifiedExportProductVariant")
        except Exception as e:
            logging.error("Error initializing UnifiedExportProductVariant", exc_info=True)
            raise

    def update_from_json(self, json_data: Dict[str, Any]) -> None:
        """
        Update variant attributes from JSON data.

        Args:
            json_data: Dictionary containing variant data from JSON
        """
        try:
            super().update_from_json(json_data)
            # Add any variant-specific JSON processing here if needed
        except Exception as e:
            logging.error("Error updating UnifiedExportProductVariant from JSON", exc_info=True)
            raise