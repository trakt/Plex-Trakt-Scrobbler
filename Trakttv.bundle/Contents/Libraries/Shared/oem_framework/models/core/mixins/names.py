import logging

log = logging.getLogger(__name__)


class NamesMixin(object):
    @classmethod
    def _flatten_names(cls, collection, data):
        if not data or 'names' not in data:
            return False

        identifiers = data.get('identifiers', {}).get(collection.target, {})

        # Flatten "names" attribute
        if (type(identifiers) is not list or len(identifiers) == 1) and len(data['names']) == 1:
            data['names'] = list(data['names'].values())[0]
            return True

        if type(data['names']) is dict:
            unique_names = set()

            for _, names in data['names'].items():
                for name in names:
                    unique_names.add(name)

            if len(unique_names) == 1:
                data['names'] = {'*': list(data['names'].values())[0]}
                return True

        # Remove "names" attribute
        if not data['names']:
            del data['names']
            return True

        return False

    @classmethod
    def _parse_names(cls, collection, identifiers, names):
        if not names or type(names) is dict:
            return names

        if type(names) is set:
            if not identifiers or collection.target not in identifiers:
                log.info('Unable to parse names, unsupported identifiers format')
                return None

            # Retrieve target key
            target_key = identifiers[collection.target]

            if type(target_key) is list:
                log.info('Unable to parse names, multiple keys returned for service')
                return None

            # Convert `names` to dictionary
            return {
                target_key: names
            }

        log.warn('Unknown names format: %r', names)
        return None
