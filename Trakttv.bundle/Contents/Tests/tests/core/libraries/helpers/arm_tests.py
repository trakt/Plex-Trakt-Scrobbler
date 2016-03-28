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


def test_processor_identifier():
    assert ArmHelper.processor_identifier({}) == (None, None)
    assert ArmHelper.processor_identifier({0: {}}) == (None, None)

    assert ArmHelper.processor_identifier({
        0: {
            'cpu_implementer': '0x41',
            'cpu_part': '0xB02'
        }
    }) == (0x41, 0xB02)

    assert ArmHelper.processor_identifier({
        1: {
            'cpu_implementer': '0x41',
            'cpu_part': '0xB02'
        }
    }) == (0x41, 0xB02)

    assert ArmHelper.processor_identifier({
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
