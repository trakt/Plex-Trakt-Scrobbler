from plugin.sync.core.enums import SyncMode
from plugin.sync.modes.core.base import Mode

import elapsed


class PersonalLists(Mode):
    mode = SyncMode.Pull

    @elapsed.clock
    def run(self):
        pass
