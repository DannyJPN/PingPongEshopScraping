class DownloadedProduct:
    def __init__(self):
        self.name = None
        self.short_description = None
        self.description = None
        self.main_photo_filepath = None
        self.gallery_photo_filepaths = None
        self.variants = None
        self.url = None

    def fill(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
