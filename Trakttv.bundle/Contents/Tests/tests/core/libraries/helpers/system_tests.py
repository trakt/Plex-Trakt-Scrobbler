from plugin.core.libraries.helpers.system import SystemHelper


def test_arm():
    # ARMv5
    assert SystemHelper.arm('armv5', 'sf') == 'armv5_sf'
    assert SystemHelper.arm('armv5', 'hf') == 'armv5_hf'

    # ARMv6
    assert SystemHelper.arm('armv6', 'sf') == 'armv6_sf'
    assert SystemHelper.arm('armv6', 'hf') == 'armv6_hf'

    # ARMv7
    assert SystemHelper.arm('armv7l', 'sf') == 'armv7_sf'
    assert SystemHelper.arm('armv7l', 'hf') == 'armv7_hf'

    # AArch64
    assert SystemHelper.arm('aarch64') == 'aarch64'
