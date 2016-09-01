from tzlocal.constants import ZONE_MAPPINGS
import pytz


def _get_timezone(zone):
    # Ensure there is no "Timezone/" prefix (Synology)
    zone = zone.lstrip('Timezone/')

    # Apply mappings
    key = zone.lower()

    if key in ZONE_MAPPINGS:
        zone = ZONE_MAPPINGS[key]

    # Retrieve timezone (via pytz)
    return pytz.timezone(zone)
