def build_version(base, branch):
    version = '.'.join([str(x) for x in base])

    if branch == 'master':
        return version

    return version + '-' + branch
