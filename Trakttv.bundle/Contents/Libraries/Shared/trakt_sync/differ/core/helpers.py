def dict_path(d, path):
    if not isinstance(path, (list, tuple)):
        raise ValueError()

    for key in path:
        if key not in d:
            d[key] = {}

        d = d[key]

    return d
