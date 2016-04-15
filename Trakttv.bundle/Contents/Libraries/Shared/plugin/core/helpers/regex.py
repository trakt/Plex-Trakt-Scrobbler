from re import *


def compile_list(patterns, flags=0):
    result = []

    for pattern in patterns:
        result.append(compile(pattern, flags))

    return result
