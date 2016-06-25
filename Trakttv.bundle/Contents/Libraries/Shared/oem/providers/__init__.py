# flake8: noqa

from oem.providers.package import PackageProvider
from oem.providers.release.complete import CompleteReleaseProvider
from oem.providers.release.incremental import IncrementalReleaseProvider

PROVIDERS = {
    'package':              PackageProvider,

    'release:complete':     CompleteReleaseProvider,
    'release:incremental':  IncrementalReleaseProvider
}
