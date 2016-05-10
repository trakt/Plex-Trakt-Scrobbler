from oem_framework import models


class Metadata(models.Metadata):
    def get(self):
        return self.storage.open_item(self.collection, self.media)
