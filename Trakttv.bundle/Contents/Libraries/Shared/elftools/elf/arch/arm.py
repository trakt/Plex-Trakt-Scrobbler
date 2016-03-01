from ...common.py3compat import iteritems


class ARMTags(object):
    @staticmethod
    def name(tag):
        return _DESCR_TAGS.get(tag, tag)

    @classmethod
    def value(cls, tag, value):
        if type(value) is not int:
            return value

        # Retrieve value via function
        func = getattr(cls, 'value_%s' % tag.lower(), None)

        if func:
            return func(value)

        # Retrieve enum value
        values = globals().get('TAG_%s' % tag.upper())

        if values is None or value >= len(values):
            return '<unknown: %d>' % value

        return values[value]

    @staticmethod
    def value_cpu_arch_profile(value):
        if value == 0:
            return 'None'

        if value == ord('A'):
            return 'Application'

        if value == ord('R'):
            return 'Realtime'

        if value == ord('M'):
            return 'Microcontroller'

        if value == ord('S'):
            return 'Application or Realtime'

        return '??? (%d)' % value

    @staticmethod
    def value_abi_align_needed(value):
        if value == 0:
            return 'None'

        if value == 1:
            return '8-byte'

        if value == 2:
            return '4-byte'

        if value == 3:
            return '??? 3'

        if value <= 12:
            return '8-byte and up to %d-byte extended' % (1 << value)

        return '??? (%d)' % value

    @staticmethod
    def value_abi_align_preserved(value):
        if value == 0:
            return 'None'

        if value == 1:
            return '8-byte, except leaf SP'

        if value == 2:
            return '8-byte'

        if value == 3:
            return '??? 3'

        if value <= 12:
            return '8-byte and up to %d-byte extended' % (1 << value)

        return '??? (%d)' % value


#
# Enums
#

TAGS = dict(
    CPU_name=5,
    CPU_arch=6,
    CPU_arch_profile=7,
    ARM_ISA_use=8,
    THUMB_ISA_use=9,
    FP_arch=10,
    WMMX_arch=11,
    Advanced_SIMD_arch=12,
    PCS_config=13,
    ABI_PCS_R9_use=14,
    ABI_PCS_RW_data=15,
    ABI_PCS_RO_data=16,
    ABI_PCS_GOT_use=17,
    ABI_PCS_wchar_t=18,
    ABI_FP_rounding=19,
    ABI_FP_denormal=20,
    ABI_FP_exceptions=21,
    ABI_FP_user_exceptions=22,
    ABI_FP_number_model=23,
    ABI_align_needed=24,
    ABI_align_preserved=25,
    ABI_enum_size=26,
    ABI_HardFP_use=27,
    ABI_VFP_args=28,
    ABI_WMMX_args=29,
    ABI_optimization_goals=30,
    ABI_FP_optimization_goals=31,
    compatibility=32,
    CPU_unaligned_access=34,
    FP_HP_extension=36,
    ABI_FP_16bit_format=38,
    MPextension_use=42,
    DIV_use=44,
    nodefaults=64,
    also_compatible_with=65,
    T2EE_use=66,
    conformance=67,
    Virtualization_use=68,
    MPextension_use_legacy=70
)

TAG_CPU_ARCH = [
    "Pre-v4", "v4", "v4T", "v5T", "v5TE", "v5TEJ", "v6", "v6KZ", "v6T2",
    "v6K", "v7", "v6-M", "v6S-M", "v7E-M", "v8"
]

TAG_ARM_ISA_USE = ["No", "Yes"]

TAG_THUMB_ISA_USE = ["No", "Thumb-1", "Thumb-2"]

TAG_FP_ARCH =[
    "No", "VFPv1", "VFPv2", "VFPv3", "VFPv3-D16", "VFPv4", "VFPv4-D16",
    "FP for ARMv8", "FPv5/FP-D16 for ARMv8"
]

TAG_WMMX_ARCH = ["No", "WMMXv1", "WMMXv2"]

TAG_ADVANCED_SIMD_ARCH = ["No", "NEONv1", "NEONv1 with Fused-MAC", "NEON for ARMv8"]

TAG_PCS_CONFIG = [
    "None", "Bare platform", "Linux application", "Linux DSO", "PalmOS 2004",
    "PalmOS (reserved)", "SymbianOS 2004", "SymbianOS (reserved)"
]

TAG_ABI_PCS_R9_USE = ["V6", "SB", "TLS", "Unused"]
TAG_ABI_PCS_RW_DATA = ["Absolute", "PC-relative", "SB-relative", "None"]
TAG_ABI_PCS_RO_DATA = ["Absolute", "PC-relative", "None"]
TAG_ABI_PCS_GOT_USE = ["None", "direct", "GOT-indirect"]
TAG_ABI_PCS_WCHAR_T = ["None", "??? 1", "2", "??? 3", "4"]

TAG_ABI_FP_ROUNDING = ["Unused", "Needed"]
TAG_ABI_FP_DENORMAL = ["Unused", "Needed", "Sign only"]
TAG_ABI_FP_EXCEPTIONS= ["Unused", "Needed"]
TAG_ABI_FP_USER_EXCEPTIONS = ["Unused", "Needed"]
TAG_ABI_FP_NUMBER_MODEL = ["Unused", "Finite", "RTABI", "IEEE 754"]

TAG_ABI_ENUM_SIZE = ["Unused", "small", "int", "forced to int"]
TAG_ABI_HARDFP_USE = ["As Tag_FP_arch", "SP only", "Reserved", "Deprecated"]
TAG_ABI_VFP_ARGS = ["AAPCS", "VFP registers", "custom", "compatible"]
TAG_ABI_WMMX_ARGS = ["AAPCS", "WMMX registers", "custom"]
TAG_ABI_OPTIMIZATION_GOALS = [
    "None", "Prefer Speed", "Aggressive Speed", "Prefer Size",
    "Aggressive Size", "Prefer Debug", "Aggressive Debug"
]
TAG_ABI_FP_OPTIMIZATION_GOALS = [
    "None", "Prefer Speed", "Aggressive Speed", "Prefer Size",
    "Aggressive Size", "Prefer Accuracy", "Aggressive Accuracy"
]
TAG_CPU_UNALIGNED_ACCESS = ["None", "v6"]
TAG_FP_HP_EXTENSION = ["Not Allowed", "Allowed"]
TAG_ABI_FP_16BIT_FORMAT = ["None", "IEEE 754", "Alternative Format"]
TAG_MPEXTENSION_USE = ["Not Allowed", "Allowed"]
TAG_DIV_USE = [
    "Allowed in Thumb-ISA, v7-R or v7-M", "Not allowed",
    "Allowed in v7-A with integer division extension"
]
TAG_T2EE_USE = ["Not Allowed", "Allowed"]
TAG_VIRTUALIZATION_USE = [
    "Not Allowed", "TrustZone", "Virtualization Extensions",
    "TrustZone and Virtualization Extensions"
]
TAG_MPEXTENSION_USE_LEGACY = ["Not Allowed", "Allowed"]

#
# Descriptions
#

_DESCR_TAGS = dict((v, k) for k, v in iteritems(TAGS))
