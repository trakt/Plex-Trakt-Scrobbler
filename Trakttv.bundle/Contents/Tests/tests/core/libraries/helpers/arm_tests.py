from plugin.core.libraries.helpers.arm import ArmHelper


def test_lookup():
    assert ArmHelper.lookup({}, {}) == (None, None, None)
    assert ArmHelper.lookup({0: {}}, {}) == (None, None, None)

    assert ArmHelper.lookup({
        0: {
            'cpu_implementer': '0x41',
            'cpu_part': '0xB02'
        }
    }, {}) == ('arm', '11-MPCore', None)

    assert ArmHelper.lookup({
        1: {
            'cpu_implementer': '0x56',
            'cpu_part': '0x581'
        }
    }, {}) == ('marvell', 'armada-370/XP', 'marvell-pj4')

    assert ArmHelper.lookup({
        0: {
            'BogoMIPS': '1594.16'
        },
        1: {
            'BogoMIPS': '1594.16'
        },
        2: {
            'cpu_implementer': '0x41',
            'cpu_part': '0xC09'
        }
    }, {}) == ('marvell', 'armada-375',    'marvell-pj4')


def test_cpu_identifier():
    assert ArmHelper.cpu_identifier({}) == (None, None)
    assert ArmHelper.cpu_identifier({0: {}}) == (None, None)

    assert ArmHelper.cpu_identifier({
        0: {
            'cpu_implementer': '0x41',
            'cpu_part': '0xB02'
        }
    }) == (0x41, 0xB02)

    assert ArmHelper.cpu_identifier({
        1: {
            'cpu_implementer': '0x41',
            'cpu_part': '0xB02'
        }
    }) == (0x41, 0xB02)

    assert ArmHelper.cpu_identifier({
        0: {
            'BogoMIPS': '1594.16'
        },
        1: {
            'BogoMIPS': '1594.16'
        },
        2: {
            'cpu_implementer': '0x41',
            'cpu_part': '0xB02'
        }
    }) == (0x41, 0xB02)

    assert ArmHelper.cpu_identifier({
        0: {'bogomips': '1594.16'},
        1: {'bogomips': '1594.16'}
    }) == (None, None)

    assert ArmHelper.cpu_identifier({
        0: {'bogomips': '1594.16'},
        1: {'bogomips': '1594.16'}
    }, {
        'features': 'swp half thumb fastmult vfp edsp neon vfpv3 tls',
        'cpu_implementer': '0x41',
        'cpu_architecture': '7',
        'cpu_variant': '0x4',
        'cpu_part': '0xc09',
        'cpu_revision': '1',
    }) == (0x41, 0xC09)

    assert ArmHelper.cpu_identifier({
        0: {'bogomips': '1594.16'},
        1: {'bogomips': '1594.16', 'cpu_implementer': '0x41', 'cpu_part': '0xc09'}
    }, {
        'features': 'swp half thumb fastmult vfp edsp neon vfpv3 tls',
        'cpu_implementer': '0x41',
        'cpu_architecture': '7',
        'cpu_variant': '0x4',
        'cpu_part': '0xb09',
        'cpu_revision': '1',
    }) == (0x41, 0xC09)


def test_parse():
    processors, extra = ArmHelper._parse("""Processor	: ARMv7 Processor rev 1 (v7l)
processor	: 0
BogoMIPS	: 1594.16

processor	: 1
BogoMIPS	: 1594.16

Features	: swp half thumb fastmult vfp edsp neon vfpv3 tls
CPU implementer	: 0x41
CPU architecture: 7
CPU variant	: 0x4
CPU part	: 0xc09
CPU revision	: 1

Hardware : Marvell Armada-375 Board""".split('\n'))

    assert processors == {
        0: {'bogomips': '1594.16'},
        1: {'bogomips': '1594.16'}
    }

    assert extra == {
        'features': 'swp half thumb fastmult vfp edsp neon vfpv3 tls',
        'cpu_implementer': '0x41',
        'cpu_architecture': '7',
        'cpu_variant': '0x4',
        'cpu_part': '0xc09',
        'cpu_revision': '1',

        'hardware': 'Marvell Armada-375 Board'
    }
