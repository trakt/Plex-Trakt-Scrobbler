#
# This file is part of pyasn1 software.
#
# Copyright (c) 2005-2017, Ilya Etingof <etingof@gmail.com>
# License: http://pyasn1.sf.net/license.html
#
from pyasn1.type import char, tag


class ObjectDescriptor(char.GraphicString):
    tagSet = char.GraphicString.tagSet.tagImplicitly(
        tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 7)
    )


class GeneralizedTime(char.VisibleString):
    tagSet = char.VisibleString.tagSet.tagImplicitly(
        tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 24)
    )


class UTCTime(char.VisibleString):
    tagSet = char.VisibleString.tagSet.tagImplicitly(
        tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 23)
    )
