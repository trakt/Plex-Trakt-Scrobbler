from .arm import ARMTags


class Tags(object):
    @staticmethod
    def name(tag, machine):
        if machine == 'EM_ARM':
            return ARMTags.name(tag)

        return tag

    @staticmethod
    def value(tag, value, machine):
        if type(value) is not int:
            return value

        if machine == 'EM_ARM':
            return ARMTags.value(tag, value)

        return '<unknown: %d>' % value
