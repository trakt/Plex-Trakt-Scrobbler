#
# This file is part of pyasn1 software.
#
# Copyright (c) 2005-2017, Ilya Etingof <etingof@gmail.com>
# License: http://pyasn1.sf.net/license.html
#
from sys import version_info

if version_info[0:2] < (2, 6):
    def bin(x):
        if x <= 1:
            return '0b' + str(x)
        else:
            return bin(x >> 1) + str(x & 1)
else:
    bin = bin
