import inspect
import re


RE_HANDLER_ARGUMENTS = re.compile(r'\@\w+\(.*?\)', re.IGNORECASE)


def wraps(wrapped):
    def inner(*args, **kwargs):
        args = list(args)

        # Handle case where decorator is called without parameters
        current = inspect.currentframe()
        previous = inspect.getframeinfo(current.f_back)

        code = ''.join(previous.code_context).strip()

        if RE_HANDLER_ARGUMENTS.match(code):
            wrapper = wrapped(*args, **kwargs)
        else:
            if len(args) == 1 and len(kwargs) == 0:
                func = args.pop(0)

                # Call `wrapper` with `func` parameter
                wrapper = wrapped()(func)
            else:
                raise ValueError('Unknown call to @handler decorator')

        return wrapper

    return inner
