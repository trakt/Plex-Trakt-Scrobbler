def SyncDownString():

    if Prefs['sync_watched'] and Prefs['sync_ratings']:
        return "seen and rated"
    elif Prefs['sync_watched']:
        return "seen "
    elif Prefs['sync_ratings']:
        return "rated "
    else:
        return ""


def SyncUpString():
    action_strings = []
    if Prefs['sync_collection']:
        action_strings.append("library")
    if Prefs['sync_watched']:
        action_strings.append("seen items")
    if Prefs['sync_ratings']:
        action_strings.append("ratings")

    temp_string = ", ".join(action_strings)
    li = temp_string.rsplit(", ", 1)
    return " and ".join(li)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
