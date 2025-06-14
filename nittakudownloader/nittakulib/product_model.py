class Variant:
    def __init__(self):
        self.key_value_pairs = {}
        self.current_price = 0
        self.basic_price = 0
        self.stock_status = ""

class Product:
    def __init__(self):
        self.name = ""
        self.short_description = ""
        self.description = ""
        self.variants = []  # List of Variant objects
        self.main_photo_link = ""
        self.main_photo_filepath = ""
        self.photogallery_links = []
        self.photogallery_filepaths = []
        self.url = ""
