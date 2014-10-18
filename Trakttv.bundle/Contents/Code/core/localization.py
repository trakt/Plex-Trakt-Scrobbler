from core.logger import Logger

log = Logger('core.localization')


def localization(name):
    def L_(key):
        return L('%s:%s' % (name, key))

    def LF_(key, *args):
        value = L_(key)

        try:
            return str(value) % args
        except Exception, ex:
            log.warn('Unable to format localization string "%s" (args: %s) - %s', value, args, ex)
            return value

    return L_, LF_
