from msgpack.fallback import DEFAULT_RECURSE_LIMIT
import msgpack.fallback


class Packer(msgpack.fallback.Packer):
    def _fb_pack_map_pairs(self, n, pairs, nest_limit=DEFAULT_RECURSE_LIMIT):
        return super(Packer, self)._fb_pack_map_pairs(
            n, sorted(pairs),
            nest_limit=nest_limit
        )
