from raven.processors import Processor
import logging
import os

log = logging.getLogger(__name__)


class RelativePathProcessor(Processor):
    separator = 'plug-ins'

    def process(self, data, **kwargs):
        data = super(RelativePathProcessor, self).process(data, **kwargs)

        try:
            extra = data.get('extra', {})

            self.to_relative(extra, 'pathname')
            self.to_relative(extra.get('sys.argv', []))
        except Exception:
            log.warn('Exception raised in RelativePathProcessor.process()', exc_info=True)

        return data

    def filter_stacktrace(self, data, **kwargs):
        for frame in data.get('frames', []):
            try:
                self.to_relative(frame, 'abs_path')
                self.to_relative(frame, 'filename')
            except Exception:
                log.warn('Exception raised in RelativePathProcessor.filter_stacktrace()', exc_info=True)

    def to_relative(self, d, key=None):
        if type(d) is list:
            if key is not None:
                value = d[key]
            else:
                # Run `to_relative` on each item
                for x in range(len(d)):
                    self.to_relative(d, x)

                return True
        else:
            value = d.get(key)

        if not value:
            return False

        # Find `separator` position
        pos = os.path.normcase(value).find(self.separator)

        if pos == -1:
            return False

        # Update `d[key]` with relative path
        d[key] = value[pos:]

        return True
