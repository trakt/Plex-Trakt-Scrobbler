from elapsed.sample import DummySample, Sample

import inspect
import logging

log = logging.getLogger(__name__)

ENABLED = False
SAMPLES = []

DUMMY_SAMPLE = DummySample()


def setup(enabled=False):
    global ENABLED
    ENABLED = enabled

    # Reset current samples
    reset()


def reset():
    global SAMPLES
    SAMPLES = []


def clock(*args):
    if len(args) < 1:
        raise ValueError('At least one parameter is required')

    # Parse arguments
    if inspect.isfunction(args[0]):
        return clock_decorate(args[0])

    if type(args[0]) is tuple:
        return clock_context(args[0])
    elif len(args) > 1:
        return clock_context(args)

    raise ValueError('Unknown parameter provided')


def clock_context(key):
    if not ENABLED:
        return DUMMY_SAMPLE

    # Parse key
    if len(key) == 2 and inspect.isclass(key[0]):
        cls = key[0]
        key = (cls.__module__, cls.__name__, key[1])
    elif len(key) != 3:
        raise ValueError('Unknown key format')

    # Construct sample
    return Sample(
        key=key,
        root=SAMPLES
    )


def clock_decorate(func):
    def inner(*args, **kwargs):
        if not ENABLED:
            return func(*args, **kwargs)

        arguments = inspect.getcallargs(func, *args, **kwargs)

        # Retrieve owner class
        if 'self' in arguments:
            cls = arguments['self'].__class__
        elif 'cls' in arguments:
            cls = arguments['cls']
        else:
            cls = None

        # Construct sample
        sample = Sample(
            key=(cls.__module__, cls.__name__, func.func_name),
            root=SAMPLES
        )

        with sample:
            result = func(*args, **kwargs)

        return result

    return inner


def format_report():
    for line in format_samples(SAMPLES):
        yield line


def format_children(children, depth=0):
    # Sort by `started_at`
    children_sorted = children.values()
    children_sorted.sort(key=lambda x: x[0].started_at)

    # Format samples
    for samples in children_sorted:
        for line in format_samples(samples, depth):
            yield line


def format_samples(samples, depth=0):
    for sample in samples:
        sample.aggregate_children()

        yield '%-80s\t%6.3fs%s' % (
            ('    ' * depth) + ('%s:%s.%s' % sample.key),
            sample.elapsed,
            (' (%7.3f%%)' % sample.percent) if sample.percent is not None else ''
        )

        for line in format_children(sample.children, depth + 1):
            yield line


def print_report():
    print '\n'.join(format_report())
