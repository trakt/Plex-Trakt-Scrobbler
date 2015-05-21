def dict_path(d, path):
    if not isinstance(path, (list, tuple)):
        raise ValueError()

    for keys in path:
        if type(keys) is not list:
            keys = [keys]

        value = None

        for key in keys:
            if key not in d:
                continue

            value = d[key]

        if value is None:
            value = {}

        for key in keys:
            d[key] = value

        d = value

    return d
