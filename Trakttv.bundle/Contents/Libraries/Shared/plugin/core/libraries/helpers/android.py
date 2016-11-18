import logging
import os
import platform

log = logging.getLogger(__name__)


class AndroidHelper(object):
    _is_android = None

    @classmethod
    def is_android(cls):
        if cls._is_android is not None:
            return cls._is_android

        try:
            # Check android platform criteria
            if not os.path.exists('/system/build.prop'):
                # Couldn't find "build.prop" file
                cls._is_android = False
            elif os.path.exists('/system/lib/libandroid_runtime.so'):
                # Found "libandroid_runtime.so" file
                log.info('Detected android system (found the "libandroid_runtime.so" file)')
                cls._is_android = True
            elif '-google' in platform.python_compiler():
                # Found "-google" in the python compiler attribute
                log.info('Detected android system (found "-google" in the python compiler attribute)')
                cls._is_android = True
            else:
                log.warn('Found the "build.prop" file, but could\'t confirm if the system is running android')
                cls._is_android = False

        except Exception as ex:
            log.warn('Unable to check if the system is running android: %s', ex, exc_info=True)

        return cls._is_android
