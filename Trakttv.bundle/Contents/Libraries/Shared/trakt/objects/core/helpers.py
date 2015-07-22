def update_attributes(obj, dictionary, keys):
    if not dictionary:
        return

    for key in keys:
        if key not in dictionary:
            continue

        if getattr(obj, key) is not None and dictionary[key] is None:
            continue

        setattr(obj, key, dictionary[key])
