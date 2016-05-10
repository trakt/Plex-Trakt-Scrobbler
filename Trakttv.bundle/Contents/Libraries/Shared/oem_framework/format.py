import os


class Format(object):
    __construct__ = None
    __extension__ = None
    __supports_binary__ = None

    @property
    def available(self):
        return False

    #
    # Dump
    #

    def dump_file(self, obj, fp):
        raise NotImplementedError

    def dump_path(self, obj, path):
        with open(self.parse_path(path), 'wb') as fp:
            return self.dump_file(obj, fp)

    def dump_string(self, obj):
        raise NotImplementedError

    #
    # Load
    #

    def load_file(self, fp):
        raise NotImplementedError

    def load_path(self, path):
        with open(self.parse_path(path), 'rb') as fp:
            return self.load_file(fp)

    def load_string(self, value):
        raise NotImplementedError

    #
    # From
    #

    def from_dict(self, collection, model, data, **kwargs):
        """Convert `data` dictionary into the specified `model` object

        :param collection: Collection to attach object with
        :type collection: oem_core.models.collection.Collection

        :param model: Model to use for conversion
        :type model: oem_core.models.base.writable.Model

        :param data: Dictionary of data to convert into a `model` object
        :type data: dict

        :return: oem_core.models.base.writable.Writable
        """

        return model.from_dict(collection, data, **kwargs)

    def from_file(self, collection, model, fp, **parameters):
        return self.from_dict(collection, model, self.load_file(fp), **parameters)

    def from_path(self, collection, model, path, **parameters):
        return self.from_dict(collection, model, self.load_path(path), **parameters)

    def from_string(self, collection, model, value, **parameters):
        return self.from_dict(collection, model, self.load_string(value), **parameters)

    #
    # To
    #

    def to_dict(self, item, **kwargs):
        """Converted `item` into a dictionary

        :param item: Item to convert into a dictionary
        :type item: oem_core.models.base.writable.Model

        :return: dict
        """

        return item.to_dict(**kwargs)

    def to_file(self, item, fp, **parameters):
        return self.dump_file(self.to_dict(item, **parameters), fp)

    def to_path(self, item, path, **parameters):
        return self.dump_path(self.to_dict(item, **parameters), path)

    def to_string(self, item, **parameters):
        return self.dump_string(self.to_dict(item, **parameters))

    #
    # Encode + Decode
    #

    def encode(self, model, data, **kwargs):
        return data

    def decode(self, model, data, **kwargs):
        return data

    #
    # Helper methods
    #

    def parse_path(self, path):
        ext = '.' + self.__extension__

        _, path_ext = os.path.splitext(path)

        if path_ext and path.endswith(ext):
            return path

        if path_ext == '':
            return path + ext

        raise ValueError('Path %r has an incorrect extension for %r' % (path, self))
