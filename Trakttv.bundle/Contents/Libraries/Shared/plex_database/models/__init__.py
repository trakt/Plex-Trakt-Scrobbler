from plex_database.models.account import Account
from plex_database.models.directory import Directory
from plex_database.models.library_section import LibrarySection, LibrarySectionType
from plex_database.models.media_item import MediaItem
from plex_database.models.media_part import MediaPart
from plex_database.models.metadata_item import MetadataItem, MetadataItemType
from plex_database.models.metadata_item_settings import MetadataItemSettings

# Model aliases
Season = MetadataItem.alias()
Episode = MetadataItem.alias()
