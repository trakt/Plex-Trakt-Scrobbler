class HamaMapper(object):
    def __init__(self, mapper):
        self.mapper = mapper

    def map(self, source, key, identifier=None, resolve_mappings=True):
        if source == 'tvdb3':
            return self.map_tvdb3(
                key,
                identifier=identifier,
                resolve_mappings=resolve_mappings
            )

        return False, None

    def map_tvdb3(self, key, identifier=None, resolve_mappings=True):
        # Find matching anidb service identifier
        supported, match = self.mapper.map(
            'tvdb', key,
            resolve_mappings=False,
            use_handlers=False
        )

        if not supported:
            return False, None

        if not match.identifiers or not match.identifiers.get('anidb'):
            return False, None

        # Map episode identifier with the `anidb_id` we've found
        return self.mapper.map(
            'anidb', match.identifiers['anidb'],
            identifier=identifier,
            resolve_mappings=resolve_mappings
        )
