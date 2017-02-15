#
# This file is part of pyasn1 software.
#
# Copyright (c) 2005-2017, Ilya Etingof <etingof@gmail.com>
# License: http://pyasn1.sf.net/license.html
#
import operator
import sys
import math
from pyasn1.type import base, tag, constraint, namedtype, namedval, tagmap
from pyasn1.codec.ber import eoo
from pyasn1.compat import octets
from pyasn1 import error

NoValue = base.NoValue
noValue = NoValue()


# "Simple" ASN.1 types (yet incomplete)

class Integer(base.AbstractSimpleAsn1Item):
    """Creates ASN.1 INTEGER type or object.

    The INTEGER type denotes an arbitrary integer. INTEGER values can
    be positive, negative, or zero, and can have any magnitude.

    Parameters
    ----------
    value : :class:`int`, :class:`str` or :py:class:`~pyasn1.type.univ.Integer` object
        Python integer or string literal or *Integer* class instance.

    tagSet: :py:class:`~pyasn1.type.tag.TagSet`
        Object representing non-default ASN.1 tag(s)

    subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
        Object representing non-default ASN.1 subtype constraint(s)

    namedValues: :py:class:`~pyasn1.type.namedval.NamedValues`
        Object representing non-default symbolic aliases for numbers

    Raises
    ------
    : :py:class:`pyasn1.error.PyAsn1Error`
        On constraint violation or bad initializer.

    """
    #: Default :py:class:`~pyasn1.type.tag.TagSet` object for ASN.1
    #: *Integer* objects
    tagSet = tag.initTagSet(
        tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 0x02)
    )
    baseTagSet = tagSet

    #: Default :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
    #: object imposing constraints on initialization values.
    subtypeSpec = constraint.ConstraintsIntersection()

    #: Default :py:class:`~pyasn1.type.namedval.NamedValues` object
    #: representing symbolic aliases for numbers
    namedValues = namedval.NamedValues()

    def __init__(self, value=noValue, tagSet=None, subtypeSpec=None,
                 namedValues=None):
        if namedValues is None:
            self.__namedValues = self.namedValues
        else:
            self.__namedValues = namedValues
        base.AbstractSimpleAsn1Item.__init__(
            self, value, tagSet, subtypeSpec
        )

    def __repr__(self):
        if self.__namedValues is not self.namedValues:
            return '%s, %r)' % (base.AbstractSimpleAsn1Item.__repr__(self)[:-1], self.__namedValues)
        else:
            return base.AbstractSimpleAsn1Item.__repr__(self)

    def __and__(self, value):
        return self.clone(self._value & value)

    def __rand__(self, value):
        return self.clone(value & self._value)

    def __or__(self, value):
        return self.clone(self._value | value)

    def __ror__(self, value):
        return self.clone(value | self._value)

    def __xor__(self, value):
        return self.clone(self._value ^ value)

    def __rxor__(self, value):
        return self.clone(value ^ self._value)

    def __lshift__(self, value):
        return self.clone(self._value << value)

    def __rshift__(self, value):
        return self.clone(self._value >> value)

    def __add__(self, value):
        return self.clone(self._value + value)

    def __radd__(self, value):
        return self.clone(value + self._value)

    def __sub__(self, value):
        return self.clone(self._value - value)

    def __rsub__(self, value):
        return self.clone(value - self._value)

    def __mul__(self, value):
        return self.clone(self._value * value)

    def __rmul__(self, value):
        return self.clone(value * self._value)

    def __mod__(self, value):
        return self.clone(self._value % value)

    def __rmod__(self, value):
        return self.clone(value % self._value)

    def __pow__(self, value, modulo=None):
        return self.clone(pow(self._value, value, modulo))

    def __rpow__(self, value):
        return self.clone(pow(value, self._value))

    def __floordiv__(self, value):
        return self.clone(self._value // value)

    def __rfloordiv__(self, value):
        return self.clone(value // self._value)

    if sys.version_info[0] <= 2:
        def __div__(self, value):
            if isinstance(value, float):
                return Real(self._value / value)
            else:
                return self.clone(self._value / value)

        def __rdiv__(self, value):
            if isinstance(value, float):
                return Real(value / self._value)
            else:
                return self.clone(value / self._value)
    else:
        def __truediv__(self, value):
            return Real(self._value / value)

        def __rtruediv__(self, value):
            return Real(value / self._value)

        def __divmod__(self, value):
            return self.clone(divmod(self._value, value))

        def __rdivmod__(self, value):
            return self.clone(divmod(value, self._value))

        __hash__ = base.AbstractSimpleAsn1Item.__hash__

    def __int__(self):
        return int(self._value)

    if sys.version_info[0] <= 2:
        def __long__(self): return long(self._value)

    def __float__(self):
        return float(self._value)

    def __abs__(self):
        return self.clone(abs(self._value))

    def __index__(self):
        return int(self._value)

    def __pos__(self):
        return self.clone(+self._value)

    def __neg__(self):
        return self.clone(-self._value)

    def __invert__(self):
        return self.clone(~self._value)

    def __round__(self, n=0):
        r = round(self._value, n)
        if n:
            return self.clone(r)
        else:
            return r

    def __floor__(self):
        return math.floor(self._value)

    def __ceil__(self):
        return math.ceil(self._value)

    if sys.version_info[0:2] > (2, 5):
        def __trunc__(self): return self.clone(math.trunc(self._value))

    def __lt__(self, value):
        return self._value < value

    def __le__(self, value):
        return self._value <= value

    def __eq__(self, value):
        return self._value == value

    def __ne__(self, value):
        return self._value != value

    def __gt__(self, value):
        return self._value > value

    def __ge__(self, value):
        return self._value >= value

    def prettyIn(self, value):
        if not octets.isStringType(value):
            try:
                return int(value)
            except:
                raise error.PyAsn1Error(
                    'Can\'t coerce %r into integer: %s' % (value, sys.exc_info()[1])
                )
        r = self.__namedValues.getValue(value)
        if r is not None:
            return r
        try:
            return int(value)
        except:
            raise error.PyAsn1Error(
                'Can\'t coerce %r into integer: %s' % (value, sys.exc_info()[1])
            )

    def prettyOut(self, value):
        r = self.__namedValues.getName(value)
        return r is None and str(value) or repr(r)

    def getNamedValues(self):
        return self.__namedValues

    def clone(self, value=noValue, tagSet=None, subtypeSpec=None,
              namedValues=None):
        """Creates a copy of object representing ASN.1 INTEGER type or value.

        If additional parameters are specified, they will be used
        in resulting object instead of corresponding parameters of
        current object.

        Parameters
        ----------
        value : :class:`int`, :class:`str` or :py:class:`~pyasn1.type.univ.Integer` object
            Initialization value to pass to new ASN.1 object instead of
            inheriting one from the caller.

        tagSet: :py:class:`~pyasn1.type.tag.TagSet`
            Object representing ASN.1 tag(s) to use in new object instead of inheriting from the caller

        subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
            Object representing ASN.1 subtype constraint(s) to use in new object instead of inheriting from the caller 

        namedValues: :py:class:`~pyasn1.type.namedval.NamedValues`
            Object representing symbolic aliases for numbers to use instead of inheriting from caller

        Returns
        -------
        : :py:class:`~pyasn1.type.univ.Integer`
            new instance of INTEGER type/value

        """
        if self.isNoValue(value):
            if self.isNoValue(tagSet, subtypeSpec, namedValues):
                return self
            value = self._value
        if tagSet is None:
            tagSet = self._tagSet
        if subtypeSpec is None:
            subtypeSpec = self._subtypeSpec
        if namedValues is None:
            namedValues = self.__namedValues
        return self.__class__(value, tagSet, subtypeSpec, namedValues)

    def subtype(self, value=noValue, implicitTag=None, explicitTag=None,
                subtypeSpec=None, namedValues=None):
        """Creates a copy of object representing ASN.1 INTEGER subtype or a value.

        If additional parameters are specified, they will be merged
        with the ones of the caller, then applied to newly created object.

        Parameters
        ----------
        value : :class:`int`, :class:`str` or :py:class:`~pyasn1.type.univ.Integer` object
            Initialization value to pass to new ASN.1 object instead of 
            inheriting one from the caller.

        implicitTag: :py:class:`~pyasn1.type.tag.Tag`
            Implicitly apply given ASN.1 tag object to caller's 
            :py:class:`~pyasn1.type.tag.TagSet`, then use the result as
            new object's ASN.1 tag(s).

        explicitTag: :py:class:`~pyasn1.type.tag.Tag`
            Explicitly apply given ASN.1 tag object to caller's 
            :py:class:`~pyasn1.type.tag.TagSet`, then use the result as
            new object's ASN.1 tag(s).

        subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
            Add ASN.1 constraints object to one of the caller, then
            use the result as new object's ASN.1 constraints.

        namedValues: :py:class:`~pyasn1.type.namedval.NamedValues`
            Add given object representing symbolic aliases for numbers
            to one of the caller, then use the result as new object's
            named numbers.

        Returns
        -------
        : :py:class:`~pyasn1.type.univ.Integer`
            new instance of INTEGER type/value

        """
        if self.isNoValue(value):
            value = self._value
        if implicitTag is not None:
            tagSet = self._tagSet.tagImplicitly(implicitTag)
        elif explicitTag is not None:
            tagSet = self._tagSet.tagExplicitly(explicitTag)
        else:
            tagSet = self._tagSet
        if subtypeSpec is None:
            subtypeSpec = self._subtypeSpec
        else:
            subtypeSpec = self._subtypeSpec + subtypeSpec
        if namedValues is None:
            namedValues = self.__namedValues
        else:
            namedValues = namedValues + self.__namedValues
        return self.__class__(value, tagSet, subtypeSpec, namedValues)


class Boolean(Integer):
    """Creates ASN.1 BOOLEAN type or object.

    BOOLEAN in ASN.1 express values that can be either TRUE or FALSE.

    Parameters
    ----------
    value : :class:`bool`, :class:`int` or :py:class:`~pyasn1.type.univ.Boolean` object
        Python boolean or integer or *Boolean* class instance.

    tagSet: :py:class:`~pyasn1.type.tag.TagSet`
        Object representing non-default ASN.1 tag(s)

    subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
        Object representing non-default ASN.1 subtype constraint(s)

    Raises
    ------
    : :py:class:`pyasn1.error.PyAsn1Error`
        On constraint violation or bad initializer.

    """
    #: Default :py:class:`~pyasn1.type.tag.TagSet` object for ASN.1
    #: *Boolean* objects
    tagSet = tag.initTagSet(
        tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 0x01),
    )
    baseTagSet = tagSet

    #: Default :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
    #: object imposing constraints on initialization values.
    subtypeSpec = Integer.subtypeSpec + constraint.SingleValueConstraint(0, 1)

    namedValues = Integer.namedValues.clone(('False', 0), ('True', 1))

    def clone(self, value=noValue, tagSet=None, subtypeSpec=None):
        """Creates a copy of BOOLEAN object representing ASN.1 type or value.

        If additional parameters are specified, they will be used
        in resulting object instead of corresponding parameters of
        current object.

        Parameters
        ----------
        value : :class:`int` or :py:class:`~pyasn1.type.univ.Boolean` object
            Initialization value to pass to new ASN.1 object instead of 
            inheriting one from the caller.

        tagSet: :py:class:`~pyasn1.type.tag.TagSet`
            Object representing ASN.1 tag(s) to use in new object instead of inheriting from the caller

        subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
            Object representing ASN.1 subtype constraint(s) to use in new object instead of inheriting from the caller

        Returns
        -------
        : :py:class:`~pyasn1.type.univ.Boolean`
            new instance of Boolean class

        """
        return Integer.clone(self, value, tagSet, subtypeSpec)

    def subtype(self, value=noValue, implicitTag=None, explicitTag=None,
                subtypeSpec=None):
        """Creates a copy of BOOLEAN object representing ASN.1 subtype or a value.

        If additional parameters are specified, they will be merged
        with the ones of the caller, then applied to newly created object.

        Parameters
        ----------
        value : :class:`int` or :py:class:`~pyasn1.type.univ.Boolean` object
            Initialization value to pass to new ASN.1 object instead of 
            inheriting one from the caller.

        implicitTag: :py:class:`~pyasn1.type.tag.Tag`
            Implicitly apply given ASN.1 tag object to caller's 
            :py:class:`~pyasn1.type.tag.TagSet`, then use the result as
            new object's ASN.1 tag(s).

        explicitTag: :py:class:`~pyasn1.type.tag.Tag`
            Explicitly apply given ASN.1 tag object to caller's 
            :py:class:`~pyasn1.type.tag.TagSet`, then use the result as
            new object's ASN.1 tag(s).

        subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
            Add ASN.1 constraints object to one from the caller, then
            use the result as new object's ASN.1 constraints.

        Returns
        -------
        : :py:class:`~pyasn1.type.univ.Boolean`
            new instance of Boolean class

        """
        return Integer.subtype(self, value, implicitTag, explicitTag)


class BitString(base.AbstractSimpleAsn1Item):
    """Creates ASN.1 BIT STRING type or object.

    The BIT STRING type denotes an arbitrary string of bits. A BIT STRING
    value can have any length.

    Parameters
    ----------
    value : :class:`int`, :class:`str` or :py:class:`~pyasn1.type.univ.BitString` object
        Python integer or string literal or *BitString* class instance.

    tagSet: :py:class:`~pyasn1.type.tag.TagSet`
        Object representing non-default ASN.1 tag(s)

    subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
        Object representing non-default ASN.1 subtype constraint(s)

    namedValues: :py:class:`~pyasn1.type.namedval.NamedValues`
        Object representing non-default symbolic aliases for numbers

    binValue: :py:class:`str`
        Binary string initializer to use instead of the *value*.
        Example: '10110011'.

    hexValue: :py:class:`str`
        Hexadecimal string initializer to use instead of the *value*.
        Example: 'DEADBEEF'.

    Raises
    ------
    : :py:class:`pyasn1.error.PyAsn1Error`
        On constraint violation or bad initializer.

    """
    #: Default :py:class:`~pyasn1.type.tag.TagSet` object for ASN.1
    #: *BitString* objects
    tagSet = tag.initTagSet(
        tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 0x03)
    )
    baseTagSet = tagSet

    #: Default :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
    #: object imposing constraints on initialization values.
    subtypeSpec = constraint.ConstraintsIntersection()

    #: Default :py:class:`~pyasn1.type.namedval.NamedValues` object
    #: representing symbolic aliases for numbers
    namedValues = namedval.NamedValues()

    defaultBinValue = defaultHexValue = noValue

    def __init__(self, value=noValue, tagSet=None, subtypeSpec=None,
                 namedValues=None, binValue=noValue, hexValue=noValue):
        if namedValues is None:
            self.__namedValues = self.namedValues
        else:
            self.__namedValues = namedValues
        if not self.isNoValue(binValue):
            value = self.fromBinaryString(binValue)
        if not self.isNoValue(hexValue):
            value = self.fromHexString(hexValue)
        if self.isNoValue(value):
            if self.defaultBinValue is not noValue:
                value = self.fromBinaryString(self.defaultBinValue)
            elif self.defaultHexValue is not noValue:
                value = self.fromHexString(self.defaultHexValue)
        self.__asNumbersCache = {}
        base.AbstractSimpleAsn1Item.__init__(
            self, value, tagSet, subtypeSpec
        )

    def clone(self, value=noValue, tagSet=None, subtypeSpec=None,
              namedValues=None, binValue=noValue, hexValue=noValue):
        """Creates a copy of BitString object representing ASN.1 type or value.

        If additional parameters are specified, they will be used
        in resulting object instead of corresponding parameters of
        current object.

        Parameters
        ----------
        value : :class:`str` or :py:class:`~pyasn1.type.univ.BitString` object
            Initialization value to pass to new ASN.1 object instead of 
            inheriting one from the caller.

        tagSet: :py:class:`~pyasn1.type.tag.TagSet`
            Object representing ASN.1 tag(s) to use in new object instead of inheriting from the caller

        subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
            Object representing ASN.1 subtype constraint(s) to use in new object instead of inheriting from the caller

        namedValues: :py:class:`~pyasn1.type.namedval.NamedValues`
            Class instance representing BitString type enumerations

        binValue: :py:class:`str`
            Binary string initializer to use instead of the *value*.
            Example: '10110011'.

        hexValue: :py:class:`str`
            Hexadecimal string initializer to use instead of the *value*.
            Example: 'DEADBEEF'.

        Returns
        -------
        : :py:class:`~pyasn1.type.univ.BitString`
            new instance of BIT STRING type/value
                
        """
        if self.isNoValue(value, binValue, hexValue):
            if self.isNoValue(tagSet, subtypeSpec, namedValues):
                return self
            value = self._value
        if tagSet is None:
            tagSet = self._tagSet
        if subtypeSpec is None:
            subtypeSpec = self._subtypeSpec
        if namedValues is None:
            namedValues = self.__namedValues
        return self.__class__(value, tagSet, subtypeSpec, namedValues, binValue, hexValue)

    def subtype(self, value=noValue, implicitTag=None, explicitTag=None,
                subtypeSpec=None, namedValues=None, binValue=noValue, hexValue=noValue):
        """Creates a copy of BIT STRING object representing ASN.1 subtype or a value.

        If additional parameters are specified, they will be merged
        with the ones of the caller, then applied to newly created object.

        Parameters
        ----------
        value : :class:`str` or :py:class:`~pyasn1.type.univ.BitString` object
            Initialization value to pass to new ASN.1 object instead of 
            inheriting one from the caller.

        implicitTag: :py:class:`~pyasn1.type.tag.Tag`
            Implicitly apply given ASN.1 tag object to caller's 
            :py:class:`~pyasn1.type.tag.TagSet`, then use the result as
            new object's ASN.1 tag(s).

        explicitTag: :py:class:`~pyasn1.type.tag.Tag`
            Explicitly apply given ASN.1 tag object to caller's 
            :py:class:`~pyasn1.type.tag.TagSet`, then use the result as
            new object's ASN.1 tag(s).

        subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
            Add ASN.1 constraints object to one of the caller, then
            use the result as new object's ASN.1 constraints.

        namedValues: :py:class:`~pyasn1.type.namedval.NamedValues`
            Add given object representing symbolic aliases for numbers
            to one of the caller, then use the result as new object's
            named numbers.

        binValue: :py:class:`str`
            Binary string initializer to use instead of the *value*.
            Example: '10110011'.

        hexValue: :py:class:`str`
            Hexadecimal string initializer to use instead of the *value*.
            Example: 'DEADBEEF'.

        Returns
        -------
        : :py:class:`~pyasn1.type.univ.BitString`
            new instance of BIT STRING type/value

        """
        if self.isNoValue(value, binValue, hexValue):
            if self.isNoValue(implicitTag, explicitTag, subtypeSpec, namedValues):
                return self
            value = self._value
        if implicitTag is not None:
            tagSet = self._tagSet.tagImplicitly(implicitTag)
        elif explicitTag is not None:
            tagSet = self._tagSet.tagExplicitly(explicitTag)
        else:
            tagSet = self._tagSet
        if subtypeSpec is None:
            subtypeSpec = self._subtypeSpec
        else:
            subtypeSpec = self._subtypeSpec + subtypeSpec
        if namedValues is None:
            namedValues = self.__namedValues
        else:
            namedValues = namedValues + self.__namedValues
        return self.__class__(value, tagSet, subtypeSpec, namedValues, binValue, hexValue)

    def __str__(self):
        return ''.join([str(x) for x in self._value])

    # Immutable sequence object protocol

    def __len__(self):
        if self._len is None:
            self._len = len(self._value)
        return self._len

    def __getitem__(self, i):
        if isinstance(i, slice):
            return self.clone(operator.getitem(self._value, i))
        else:
            return self._value[i]

    def __contains__(self, bit):
        return bit in self._value

    def __reversed__(self):
        reversed_value = list(self._value)
        reversed_value.reverse()
        return self.clone(reversed_value)

    def __add__(self, value):
        return self.clone(self._value + value)

    def __radd__(self, value):
        return self.clone(value + self._value)

    def __mul__(self, value):
        return self.clone(self._value * value)

    def __rmul__(self, value):
        return self * value

    def asNumbers(self, padding=True):
        """Get BIT STRING as a sequence of 8-bit integers.

        Parameters
        ----------
        padding: :class:`bool`
            Allow left-padding if BIT STRING length is not a multiples of eight.

        Raises
        ------
        : :py:class:`pyasn1.error.PyAsn1Error`
            If BIT STRING length is not multiples of eight and no padding is allowed.
        """
        if not padding and len(self) % 8 != 0:
            raise error.PyAsn1Error('BIT STRING length is not a multiple of 8')

        if padding in self.__asNumbersCache:
            return self.__asNumbersCache[padding]

        result = []
        bitstring = list(self)
        while len(bitstring) % 8:
            bitstring.insert(0, 0)
        bitIndex = 0
        while bitIndex < len(bitstring):
            byte = 0
            for x in range(8):
                byte |= bitstring[bitIndex + x] << (7 - x)
            result.append(byte)
            bitIndex += 8

        self.__asNumbersCache[padding] = tuple(result)

        return self.__asNumbersCache[padding]

    def asOctets(self, padding=True):
        """Get BIT STRING as a sequence of octets.

        Parameters
        ----------
        padding: :class:`bool`
            Allow left-padding if BIT STRING length is not a multiples of eight.

        Raises
        ------
        : :py:class:`pyasn1.error.PyAsn1Error`
            If BIT STRING length is not multiples of eight and no padding is allowed.
        """
        return octets.ints2octs(self.asNumbers(padding))

    def asInteger(self, padding=True):
        """Get BIT STRING as a single integer value.

        Parameters
        ----------
        padding: :class:`bool`
            Allow left-padding if BIT STRING length is not a multiples of eight.

        Raises
        ------
        : :py:class:`pyasn1.error.PyAsn1Error`
            If BIT STRING length is not multiples of eight and no padding is allowed.
        """
        accumulator = 0
        for byte in self.asNumbers(padding):
            accumulator <<= 8
            accumulator |= byte
        return accumulator

    @staticmethod
    def fromHexString(value):
        r = []
        for v in value:
            v = int(v, 16)
            i = 4
            while i:
                i -= 1
                r.append((v >> i) & 0x01)
        return tuple(r)

    @staticmethod
    def fromBinaryString(value):
        r = []
        for v in value:
            if v in ('0', '1'):
                r.append(int(v))
            else:
                raise error.PyAsn1Error(
                    'Non-binary BIT STRING initializer %s' % (v,)
                )
        return tuple(r)

    def prettyIn(self, value):
        r = []
        if not value:
            return ()

        elif octets.isStringType(value):
            if value[0] == '\'':  # "'1011'B" -- ASN.1 schema representation
                if value[-2:] == '\'B':
                    return self.fromBinaryString(value[1:-2])
                elif value[-2:] == '\'H':
                    return self.fromHexString(value[1:-2])
                else:
                    raise error.PyAsn1Error(
                        'Bad BIT STRING value notation %s' % (value,)
                    )
            elif self.__namedValues and not value.isdigit():  # named bits like 'Urgent, Active'
                for i in value.split(','):
                    j = self.__namedValues.getValue(i)
                    if j is None:
                        raise error.PyAsn1Error(
                            'Unknown bit identifier \'%s\'' % (i,)
                        )
                    if j >= len(r):
                        r.extend([0] * (j - len(r) + 1))
                    r[j] = 1
                return tuple(r)
            else:  # assume plain binary string like '1011'
                return self.fromBinaryString(value)

        elif isinstance(value, (tuple, list)):
            r = tuple(value)
            for b in r:
                if b and b != 1:
                    raise error.PyAsn1Error(
                        'Non-binary BitString initializer \'%s\'' % (r,)
                    )
            return r

        elif isinstance(value, BitString):
            return tuple(value)

        else:
            raise error.PyAsn1Error(
                'Bad BitString initializer type \'%s\'' % (value,)
            )

    def prettyOut(self, value):
        return '\'%s\'' % str(self)


try:
    # noinspection PyStatementEffect
    all

except NameError:  # Python 2.4
    # noinspection PyShadowingBuiltins
    def all(iterable):
        for element in iterable:
            if not element:
                return False
        return True


class OctetString(base.AbstractSimpleAsn1Item):
    """Creates ASN.1 OCTET STRING type or object.

    The OCTET STRING type denotes an arbitrary string of octets (eight-bit
    numbers). An OCTET STRING value can have any length.

    Parameters
    ----------
    value : :class:`str`, :class:`bytes` or :py:class:`~pyasn1.type.univ.OctetString` object
        Python string literal or bytes or *OctetString* class instance.

    tagSet: :py:class:`~pyasn1.type.tag.TagSet`
        Object representing non-default ASN.1 tag(s)

    subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
        Object representing non-default ASN.1 subtype constraint(s)

    encoding: :py:class:`str`
        Unicode codec ID to encode/decode :class:`unicode` (Python 2) or
        :class:`str` (Python 3) the payload when *OctetString* object is used
        in string context.

    binValue: :py:class:`str`
        Binary string initializer to use instead of the *value*.
        Example: '10110011'.
        
    hexValue: :py:class:`str`
        Hexadecimal string initializer to use instead of the *value*.
        Example: 'DEADBEEF'.

    Raises
    ------
    : :py:class:`pyasn1.error.PyAsn1Error`
        On constraint violation or bad initializer.

    """
    #: Default :py:class:`~pyasn1.type.tag.TagSet` object for ASN.1
    #: *OctetString* objects
    tagSet = tag.initTagSet(
        tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 0x04)
    )
    baseTagSet = tagSet

    #: Default :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
    #: object imposing constraints on initialization values.
    subtypeSpec = constraint.ConstraintsIntersection()

    defaultBinValue = defaultHexValue = noValue
    encoding = 'us-ascii'

    def __init__(self, value=noValue, tagSet=None, subtypeSpec=None,
                 encoding=None, binValue=noValue, hexValue=noValue):
        if encoding is None:
            self._encoding = self.encoding
        else:
            self._encoding = encoding
        if not self.isNoValue(binValue):
            value = self.fromBinaryString(binValue)
        if not self.isNoValue(hexValue):
            value = self.fromHexString(hexValue)
        if self.isNoValue(value):
            if self.defaultBinValue is not noValue:
                value = self.fromBinaryString(self.defaultBinValue)
            elif self.defaultHexValue is not noValue:
                value = self.fromHexString(self.defaultHexValue)
        self.__asNumbersCache = None
        base.AbstractSimpleAsn1Item.__init__(self, value, tagSet, subtypeSpec)

    def clone(self, value=noValue, tagSet=None, subtypeSpec=None,
              encoding=None, binValue=noValue, hexValue=noValue):
        """Creates a copy of OCTET STRING object representing ASN.1 type or value.

        If additional parameters are specified, they will be used
        in resulting object instead of corresponding parameters of
        current object.

        Parameters
        ----------
        value : :class:`str`, :class:`bytes` or :py:class:`~pyasn1.type.univ.OctetString` object
            Initialization value to pass to new ASN.1 object instead of 
            inheriting one from the caller.

        tagSet: :py:class:`~pyasn1.type.tag.TagSet`
            Object representing ASN.1 tag(s) to use in new object instead of inheriting from the caller

        subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
            Object representing ASN.1 subtype constraint(s) to use in new object instead of inheriting from the caller

        encoding: :py:class:`str`
            Unicode codec ID to encode/decode :class:`unicode` (Python 2)
            or :class:`str` (Python 3) the payload when *OctetString*
            object is used in string context.

        binValue: :py:class:`str`
            Binary string initializer. Example: '10110011'.
        
        hexValue: :py:class:`str`
            Hexadecimal string initializer. Example: 'DEADBEEF'.

        Returns
        -------
        : :py:class:`~pyasn1.type.univ.OctetString`
            new instance of OCTET STRING type/value

        """
        if self.isNoValue(value, binValue, hexValue):
            if self.isNoValue(tagSet, subtypeSpec, encoding):
                return self
            value = self._value
        if tagSet is None:
            tagSet = self._tagSet
        if subtypeSpec is None:
            subtypeSpec = self._subtypeSpec
        if encoding is None:
            encoding = self._encoding
        return self.__class__(
            value, tagSet, subtypeSpec, encoding, binValue, hexValue
        )

    def subtype(self, value=noValue, implicitTag=None, explicitTag=None,
                subtypeSpec=None, encoding=None, binValue=noValue,
                hexValue=noValue):
        """Creates a copy of OCTET STRING object representing ASN.1 subtype or a value.

        If additional parameters are specified, they will be merged
        with the ones of the caller, then applied to newly created object.

        Parameters
        ----------
        value : :class:`str`, :class:`bytes` or :py:class:`~pyasn1.type.univ.OctetString` object
            Initialization value to pass to new ASN.1 object instead of 
            inheriting one from the caller.

        implicitTag: :py:class:`~pyasn1.type.tag.Tag`
            Implicitly apply given ASN.1 tag object to caller's 
            :py:class:`~pyasn1.type.tag.TagSet`, then use the result as
            new object's ASN.1 tag(s).

        explicitTag: :py:class:`~pyasn1.type.tag.Tag`
            Explicitly apply given ASN.1 tag object to caller's 
            :py:class:`~pyasn1.type.tag.TagSet`, then use the result as
            new object's ASN.1 tag(s).

        subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
            Add ASN.1 constraints object to one of the caller, then
            use the result as new object's ASN.1 constraints.

        encoding: :py:class:`str`
            Unicode codec ID to encode/decode :class:`unicode` (Python 2)
            or :class:`str` (Python 3) the payload when *OctetString*
            object is used in string context.

        binValue: :py:class:`str`
            Binary string initializer. Example: '10110011'.
        
        hexValue: :py:class:`str`
            Hexadecimal string initializer. Example: 'DEADBEEF'.

        Returns
        -------
        : :py:class:`~pyasn1.type.univ.OctetString`
            new instance of OCTET STRING type/value

        """
        if self.isNoValue(value, binValue, hexValue):
            if self.isNoValue(implicitTag, explicitTag, subtypeSpec, encoding):
                return self
            value = self._value
        if implicitTag is not None:
            tagSet = self._tagSet.tagImplicitly(implicitTag)
        elif explicitTag is not None:
            tagSet = self._tagSet.tagExplicitly(explicitTag)
        else:
            tagSet = self._tagSet
        if subtypeSpec is None:
            subtypeSpec = self._subtypeSpec
        else:
            subtypeSpec = self._subtypeSpec + subtypeSpec
        if encoding is None:
            encoding = self._encoding
        return self.__class__(
            value, tagSet, subtypeSpec, encoding, binValue, hexValue
        )

    if sys.version_info[0] <= 2:
        def prettyIn(self, value):
            if isinstance(value, str):
                return value
            elif isinstance(value, unicode):
                try:
                    return value.encode(self._encoding)
                except (LookupError, UnicodeEncodeError):
                    raise error.PyAsn1Error(
                        'Can\'t encode string \'%s\' with \'%s\' codec' % (value, self._encoding)
                    )
            elif isinstance(value, (tuple, list)):
                try:
                    return ''.join([chr(x) for x in value])
                except ValueError:
                    raise error.PyAsn1Error(
                        'Bad OctetString initializer \'%s\'' % (value,)
                    )
            else:
                return str(value)
    else:
        def prettyIn(self, value):
            if isinstance(value, bytes):
                return value
            elif isinstance(value, str):
                try:
                    return value.encode(self._encoding)
                except UnicodeEncodeError:
                    raise error.PyAsn1Error(
                        'Can\'t encode string \'%s\' with \'%s\' codec' % (value, self._encoding)
                    )
            elif isinstance(value, OctetString):
                return value.asOctets()
            elif isinstance(value, (tuple, list, map)):
                try:
                    return bytes(value)
                except ValueError:
                    raise error.PyAsn1Error(
                        'Bad OctetString initializer \'%s\'' % (value,)
                    )
            else:
                try:
                    return str(value).encode(self._encoding)
                except UnicodeEncodeError:
                    raise error.PyAsn1Error(
                        'Can\'t encode string \'%s\' with \'%s\' codec' % (value, self._encoding)
                    )

    def prettyOut(self, value):
        if sys.version_info[0] <= 2:
            numbers = tuple((ord(x) for x in value))
        else:
            numbers = tuple(value)
        for x in numbers:
            if x < 32 or x > 126:
                return '0x' + ''.join(('%.2x' % x for x in numbers))
        else:
            return octets.octs2str(value)

    @staticmethod
    def fromBinaryString(value):
        bitNo = 8
        byte = 0
        r = []
        for v in value:
            if bitNo:
                bitNo -= 1
            else:
                bitNo = 7
                r.append(byte)
                byte = 0
            if v in ('0', '1'):
                v = int(v)
            else:
                raise error.PyAsn1Error(
                    'Non-binary OCTET STRING initializer %s' % (v,)
                )
            byte |= v << bitNo

        r.append(byte)

        return octets.ints2octs(r)

    @staticmethod
    def fromHexString(value):
        r = []
        p = []
        for v in value:
            if p:
                r.append(int(p + v, 16))
                p = None
            else:
                p = v
        if p:
            r.append(int(p + '0', 16))

        return octets.ints2octs(r)

    def __repr__(self):
        r = []
        doHex = False
        if self._value is not self.defaultValue:
            for x in self.asNumbers():
                if x < 32 or x > 126:
                    doHex = True
                    break
            if not doHex:
                r.append('%r' % (self._value,))
        if self._tagSet is not self.tagSet:
            r.append('tagSet=%r' % (self._tagSet,))
        if self._subtypeSpec is not self.subtypeSpec:
            r.append('subtypeSpec=%r' % (self._subtypeSpec,))
        if self.encoding is not self._encoding:
            r.append('encoding=%r' % (self._encoding,))
        if doHex:
            r.append('hexValue=%r' % ''.join(['%.2x' % x for x in self.asNumbers()]))
        return '%s(%s)' % (self.__class__.__name__, ', '.join(r))

    if sys.version_info[0] <= 2:
        def __str__(self):
            return str(self._value)

        def __unicode__(self):
            return self._value.decode(self._encoding, 'ignore')

        def asOctets(self, padding=True):
            return self._value

        def asNumbers(self, padding=True):
            if self.__asNumbersCache is None:
                self.__asNumbersCache = tuple([ord(x) for x in self._value])
            return self.__asNumbersCache
    else:
        def __str__(self):
            return self._value.decode(self._encoding, 'ignore')

        def __bytes__(self):
            return self._value

        def asOctets(self, padding=True):
            return self._value

        def asNumbers(self, padding=True):
            if self.__asNumbersCache is None:
                self.__asNumbersCache = tuple(self._value)
            return self.__asNumbersCache

    # Immutable sequence object protocol

    def __len__(self):
        if self._len is None:
            self._len = len(self._value)
        return self._len

    def __getitem__(self, i):
        if isinstance(i, slice):
            return self.clone(operator.getitem(self._value, i))
        else:
            return self._value[i]

    def __iter__(self):
        return iter(self._value)

    def __contains__(self, value):
        return value in self._value

    def __reversed__(self):
        reversed_value = list(self.asNumbers())
        reversed_value.reverse()
        return self.clone(reversed_value)

    def __add__(self, value):
        return self.clone(self._value + self.prettyIn(value))

    def __radd__(self, value):
        return self.clone(self.prettyIn(value) + self._value)

    def __mul__(self, value):
        return self.clone(self._value * value)

    def __rmul__(self, value):
        return self * value

    def __int__(self):
        return int(self._value)

    def __float__(self):
        return float(self._value)


class Null(OctetString):
    """Creates ASN.1 NULL type or object.

    The NULL type denotes a null value.

    Parameters
    ----------
    value : :class:`str` or :py:class:`~pyasn1.type.univ.Null` object
        Python empty string literal or *Null* class instance.

    tagSet: :py:class:`~pyasn1.type.tag.TagSet`
        Object representing non-default ASN.1 tag(s)

    Raises
    ------
    : :py:class:`pyasn1.error.PyAsn1Error`
        On constraint violation or bad initializer.

    """
    defaultValue = ''.encode()  # This is tightly constrained

    #: Default :py:class:`~pyasn1.type.tag.TagSet` object for ASN.1
    #: *Null* objects
    tagSet = tag.initTagSet(
        tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 0x05)
    )
    baseTagSet = tagSet
    subtypeSpec = OctetString.subtypeSpec + constraint.SingleValueConstraint(octets.str2octs(''))

    def clone(self, value=noValue, tagSet=None):
        """Creates a copy of object representing ASN.1 type or value.

        If additional parameters are specified, they will be used
        in resulting object instead of corresponding parameters of
        current object.

        Parameters
        ----------
        value : :class:`str` or :py:class:`~pyasn1.type.univ.Null` object
            Initialization value to pass to new ASN.1 object instead of 
            inheriting one from the caller.

        tagSet: :py:class:`~pyasn1.type.tag.TagSet`
            Object representing ASN.1 tag(s) to use in new object instead of inheriting from the caller

        Returns
        -------
        : :py:class:`~pyasn1.type.univ.Null`
            new instance of NULL type/value

        """
        return OctetString.clone(self, value, tagSet)

    def subtype(self, value=noValue, implicitTag=None, explicitTag=None):
        """Creates a copy of object representing ASN.1 subtype or a value.

        If additional parameters are specified, they will be merged
        with the ones of the caller, then applied to newly created object.

        Parameters
        ----------
        value: :class:`str` or :py:class:`~pyasn1.type.univ.Null` object
            Initialization value to pass to new ASN.1 object instead of 
            inheriting one from the caller.

        implicitTag: :py:class:`~pyasn1.type.tag.Tag`
            Implicitly apply given ASN.1 tag object to caller's 
            :py:class:`~pyasn1.type.tag.TagSet`, then use the result as
            new object's ASN.1 tag(s).

        explicitTag: :py:class:`~pyasn1.type.tag.Tag`
            Explicitly apply given ASN.1 tag object to caller's 
            :py:class:`~pyasn1.type.tag.TagSet`, then use the result as
            new object's ASN.1 tag(s).

        Returns
        -------
        : :py:class:`~pyasn1.type.univ.Null`
            new instance of NULL type/value

        """
        return OctetString.subtype(self, value, implicitTag, explicitTag)


if sys.version_info[0] <= 2:
    intTypes = (int, long)
else:
    intTypes = (int,)

numericTypes = intTypes + (float,)


class ObjectIdentifier(base.AbstractSimpleAsn1Item):
    """Creates ASN.1 OBJECT IDENTIFIER type or object.

    The OBJECT IDENTIFIER type denotes an identifier that takes shape of
    a sequence of integers. An OBJECT IDENTIFIER value can have any number
    of non-negative integers.

    Parameters
    ----------
    value : :class:`tuple`, :class:`str` or :py:class:`~pyasn1.type.univ.ObjectIdentifier` object
        Python sequence of :class:`int` or string literal or *ObjectIdentifier* class instance.

    tagSet: :py:class:`~pyasn1.type.tag.TagSet`
        Object representing non-default ASN.1 tag(s)

    subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
        Object representing non-default ASN.1 subtype constraint(s)

    Raises
    ------
    : :py:class:`pyasn1.error.PyAsn1Error`
        On constraint violation or bad initializer.

    """
    #: Default :py:class:`~pyasn1.type.tag.TagSet` object for ASN.1
    #: *ObjectIdentifier* objects
    tagSet = tag.initTagSet(
        tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 0x06)
    )
    baseTagSet = tagSet

    #: Default :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
    #: object imposing constraints on initialization values.
    subtypeSpec = constraint.ConstraintsIntersection()

    def clone(self, value=noValue, tagSet=None, subtypeSpec=None):
        """Creates a copy of OBJECT IDENTIFIER object representing ASN.1 type or value.

        If additional parameters are specified, they will be used
        in resulting object instead of corresponding parameters of
        current object.

        Parameters
        ----------
        value : :class:`tuple`, :class:`str` or :py:class:`~pyasn1.type.univ.ObjectIdentifier` object
            Initialization value to pass to new ASN.1 object instead of 
            inheriting one from the caller.

        tagSet: :py:class:`~pyasn1.type.tag.TagSet`
            Object representing ASN.1 tag(s) to use in new object instead of inheriting from the caller

        subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
            Object representing ASN.1 subtype constraint(s) to use in new object instead of inheriting from the caller

        Returns
        -------
        : :py:class:`~pyasn1.type.univ.ObjectIdentifier`
            new instance of OBJECT IDENTIFIER type/value

        """
        return base.AbstractSimpleAsn1Item.clone(self, value, tagSet, subtypeSpec)

    def subtype(self, value=noValue, implicitTag=None, explicitTag=None,
                subtypeSpec=None):
        """Creates a copy of OBJECT IDENTIFIER object representing ASN.1 subtype or a value.

        If additional parameters are specified, they will be merged
        with the ones of the caller, then applied to newly created object.

        Parameters
        ----------
        value : :class:`tuple`, :class:`str` or :py:class:`~pyasn1.type.univ.ObjectIdentifier` object
            Initialization value to pass to new ASN.1 object instead of 
            inheriting one from the caller.

        implicitTag: :py:class:`~pyasn1.type.tag.Tag`
            Implicitly apply given ASN.1 tag object to caller's 
            :py:class:`~pyasn1.type.tag.TagSet`, then use the result as
            new object's ASN.1 tag(s).

        explicitTag: :py:class:`~pyasn1.type.tag.Tag`
            Explicitly apply given ASN.1 tag object to caller's 
            :py:class:`~pyasn1.type.tag.TagSet`, then use the result as
            new object's ASN.1 tag(s).

        subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
            Add ASN.1 constraints object to one of the caller, then
            use the result as new object's ASN.1 constraints.

        Returns
        -------
        : :py:class:`~pyasn1.type.univ.ObjectIdentifier`
            new instance of OBJECT IDENTIFIER type/value

        """
        return base.AbstractSimpleAsn1Item.subtype(self, value, implicitTag, explicitTag)

    def __add__(self, other):
        return self.clone(self._value + other)

    def __radd__(self, other):
        return self.clone(other + self._value)

    def asTuple(self):
        return self._value

    # Sequence object protocol

    def __len__(self):
        if self._len is None:
            self._len = len(self._value)
        return self._len

    def __getitem__(self, i):
        if isinstance(i, slice):
            return self.clone(
                operator.getitem(self._value, i)
            )
        else:
            return self._value[i]

    def __iter__(self):
        return iter(self._value)

    def __contains__(self, value):
        return value in self._value

    def __str__(self):
        return self.prettyPrint()

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.prettyPrint())

    def index(self, suboid):
        return self._value.index(suboid)

    def isPrefixOf(self, value):
        """Indicates if caller is a prefix of passed *ObjectIdentifier*

        Parameters
        ----------
        value: :py:class:`~pyasn1.type.univ.ObjectIdentifier` object
            OBJECT IDENTIFIER object

        Returns
        -------
        : :class:`bool`
            :class:`True` if calling object represents a parent
            (prefix) OBJECT IDENTIFIER in regards to the passed one
            or :class:`False` otherwise.

        """
        l = len(self)
        if l <= len(value):
            if self._value[:l] == value[:l]:
                return True
        return False

    def prettyIn(self, value):
        if isinstance(value, tuple):
            pass
        elif isinstance(value, ObjectIdentifier):
            return tuple(value)
        elif octets.isStringType(value):
            r = []
            for element in [x for x in value.split('.') if x != '']:
                try:
                    r.append(int(element, 0))
                except ValueError:
                    raise error.PyAsn1Error(
                        'Malformed Object ID %s at %s: %s' %
                        (str(value), self.__class__.__name__, sys.exc_info()[1])
                    )
            value = tuple(r)
        else:
            try:
                value = tuple(value)
            except TypeError:
                raise error.PyAsn1Error(
                    'Malformed Object ID %s at %s: %s' %
                    (str(value), self.__class__.__name__, sys.exc_info()[1])
                )

        for x in value:
            if not isinstance(x, intTypes) or x < 0:
                raise error.PyAsn1Error(
                    'Invalid sub-ID in %s at %s' % (value, self.__class__.__name__)
                )

        return value

    def prettyOut(self, value):
        return '.'.join([str(x) for x in value])


class Real(base.AbstractSimpleAsn1Item):
    """Creates ASN.1 REAL type or object.

    The REAL type denotes a real number that is represented by mantissa,
    base and exponent. Objects of *Real* type can participate in all
    arithmetic operations but additionally can behave like a sequence
    in which case its elements are mantissa, base and exponent.

    Parameters
    ----------
    value : :class:`tuple`, :class:`float` or :py:class:`~pyasn1.type.univ.Real` object
        Python sequence of :class:`int` (representing mantissa, base and
        exponent) or float instance or *Real* class instance.

    tagSet: :py:class:`~pyasn1.type.tag.TagSet`
        Object representing non-default ASN.1 tag(s)

    subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
        Object representing non-default ASN.1 subtype constraint(s)

    Raises
    ------
    : :py:class:`pyasn1.error.PyAsn1Error`
        On constraint violation or bad initializer.

    """
    binEncBase = None  # binEncBase = 16 is recommended for large numbers

    try:
        _plusInf = float('inf')
        _minusInf = float('-inf')
        _inf = (_plusInf, _minusInf)
    except ValueError:
        # Infinity support is platform and Python dependent
        _plusInf = _minusInf = None
        _inf = ()

    #: Default :py:class:`~pyasn1.type.tag.TagSet` object for ASN.1
    #: *Real* objects
    tagSet = tag.initTagSet(
        tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 0x09)
    )
    baseTagSet = tagSet

    #: Default :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
    #: object imposing constraints on initialization values.
    subtypeSpec = constraint.ConstraintsIntersection()

    def clone(self, value=noValue, tagSet=None, subtypeSpec=None):
        """Creates a copy of REAL object representing ASN.1 type or value.

        If additional parameters are specified, they will be used
        in resulting object instead of corresponding parameters of
        current object.

        Parameters
        ----------
        value : :class:`tuple`, :class:`float` or :py:class:`~pyasn1.type.univ.Real` object
            Initialization value to pass to new ASN.1 object instead of 
            inheriting one from the caller.

        tagSet: :py:class:`~pyasn1.type.tag.TagSet`
            Object representing ASN.1 tag(s) to use in new object instead of inheriting from the caller

        subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
            Object representing ASN.1 subtype constraint(s) to use in new object instead of inheriting from the caller

        Returns
        -------
        : :py:class:`~pyasn1.type.univ.Real`
            new instance of REAL type/value

        """
        return base.AbstractSimpleAsn1Item.clone(self, value, tagSet, subtypeSpec)

    def subtype(self, value=noValue, implicitTag=None, explicitTag=None,
                subtypeSpec=None):
        """Creates a copy of REAL object representing ASN.1 subtype or a value.

        If additional parameters are specified, they will be merged
        with the ones of the caller, then applied to newly created object.

        Parameters
        ----------
        value : :class:`tuple`, :class:`float` or :py:class:`~pyasn1.type.univ.Real` object
            Initialization value to pass to new ASN.1 object instead of 
            inheriting one from the caller.

        implicitTag: :py:class:`~pyasn1.type.tag.Tag`
            Implicitly apply given ASN.1 tag object to caller's 
            :py:class:`~pyasn1.type.tag.TagSet`, then use the result as
            new object's ASN.1 tag(s).

        explicitTag: :py:class:`~pyasn1.type.tag.Tag`
            Explicitly apply given ASN.1 tag object to caller's 
            :py:class:`~pyasn1.type.tag.TagSet`, then use the result as
            new object's ASN.1 tag(s).

        subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
             Object representing ASN.1 subtype constraint(s) to use in new object instead of inheriting from the caller

        Returns
        -------
        : :py:class:`~pyasn1.type.univ.Real`
            new instance of REAL type/value

        """
        return base.AbstractSimpleAsn1Item.subtype(self, value, implicitTag, explicitTag)

    @staticmethod
    def __normalizeBase10(value):
        m, b, e = value
        while m and m % 10 == 0:
            m /= 10
            e += 1
        return m, b, e

    def prettyIn(self, value):
        if isinstance(value, tuple) and len(value) == 3:
            if not isinstance(value[0], numericTypes) or \
                    not isinstance(value[1], intTypes) or \
                    not isinstance(value[2], intTypes):
                raise error.PyAsn1Error('Lame Real value syntax: %s' % (value,))
            if isinstance(value[0], float) and \
                    self._inf and value[0] in self._inf:
                return value[0]
            if value[1] not in (2, 10):
                raise error.PyAsn1Error(
                    'Prohibited base for Real value: %s' % (value[1],)
                )
            if value[1] == 10:
                value = self.__normalizeBase10(value)
            return value
        elif isinstance(value, intTypes):
            return self.__normalizeBase10((value, 10, 0))
        elif isinstance(value, float) or octets.isStringType(value):
            if octets.isStringType(value):
                try:
                    value = float(value)
                except ValueError:
                    raise error.PyAsn1Error(
                        'Bad real value syntax: %s' % (value,)
                    )
            if self._inf and value in self._inf:
                return value
            else:
                e = 0
                while int(value) != value:
                    value *= 10
                    e -= 1
                return self.__normalizeBase10((int(value), 10, e))
        elif isinstance(value, Real):
            return tuple(value)
        raise error.PyAsn1Error(
            'Bad real value syntax: %s' % (value,)
        )

    def prettyOut(self, value):
        if value in self._inf:
            return '\'%s\'' % value
        else:
            return str(value)

    def prettyPrint(self, scope=0):
        if self.isInfinity():
            return self.prettyOut(self._value)
        else:
            return str(float(self))

    def isPlusInfinity(self):
        """Indicates PLUS-INFINITY object value

        Returns
        -------
        : :class:`bool`
            :class:`True` if calling object represents plus infinity
            or :class:`False` otherwise.

        """
        return self._value == self._plusInf

    def isMinusInfinity(self):
        """Indicates MINUS-INFINITY object value

        Returns
        -------
        : :class:`bool`
            :class:`True` if calling object represents minus infinity
            or :class:`False` otherwise.

        """
        return self._value == self._minusInf

    def isInfinity(self):
        return self._value in self._inf

    def __str__(self):
        return str(float(self))

    def __add__(self, value):
        return self.clone(float(self) + value)

    def __radd__(self, value):
        return self + value

    def __mul__(self, value):
        return self.clone(float(self) * value)

    def __rmul__(self, value):
        return self * value

    def __sub__(self, value):
        return self.clone(float(self) - value)

    def __rsub__(self, value):
        return self.clone(value - float(self))

    def __mod__(self, value):
        return self.clone(float(self) % value)

    def __rmod__(self, value):
        return self.clone(value % float(self))

    def __pow__(self, value, modulo=None):
        return self.clone(pow(float(self), value, modulo))

    def __rpow__(self, value):
        return self.clone(pow(value, float(self)))

    if sys.version_info[0] <= 2:
        def __div__(self, value):
            return self.clone(float(self) / value)

        def __rdiv__(self, value):
            return self.clone(value / float(self))
    else:
        def __truediv__(self, value):
            return self.clone(float(self) / value)

        def __rtruediv__(self, value):
            return self.clone(value / float(self))

        def __divmod__(self, value):
            return self.clone(float(self) // value)

        def __rdivmod__(self, value):
            return self.clone(value // float(self))

    def __int__(self):
        return int(float(self))

    if sys.version_info[0] <= 2:
        def __long__(self): return long(float(self))

    def __float__(self):
        if self._value in self._inf:
            return self._value
        else:
            return float(
                self._value[0] * pow(self._value[1], self._value[2])
            )

    def __abs__(self):
        return self.clone(abs(float(self)))

    def __pos__(self):
        return self.clone(+float(self))

    def __neg__(self):
        return self.clone(-float(self))

    def __round__(self, n=0):
        r = round(float(self), n)
        if n:
            return self.clone(r)
        else:
            return r

    def __floor__(self):
        return self.clone(math.floor(float(self)))

    def __ceil__(self):
        return self.clone(math.ceil(float(self)))

    if sys.version_info[0:2] > (2, 5):
        def __trunc__(self): return self.clone(math.trunc(float(self)))

    def __lt__(self, value):
        return float(self) < value

    def __le__(self, value):
        return float(self) <= value

    def __eq__(self, value):
        return float(self) == value

    def __ne__(self, value):
        return float(self) != value

    def __gt__(self, value):
        return float(self) > value

    def __ge__(self, value):
        return float(self) >= value

    if sys.version_info[0] <= 2:
        def __nonzero__(self):
            return bool(float(self))
    else:
        def __bool__(self):
            return bool(float(self))

        __hash__ = base.AbstractSimpleAsn1Item.__hash__

    def __getitem__(self, idx):
        if self._value in self._inf:
            raise error.PyAsn1Error('Invalid infinite value operation')
        else:
            return self._value[idx]


class Enumerated(Integer):
    """Creates ASN.1 ENUMERATED type or object.

    The ENUMERATED type denotes a bounded set of named integer values.
    Other than that, it is identical to
    :py:class:`~pyasn1.type.univ.Integer` type.

    Parameters
    ----------
    value : :class:`int`, :class:`str` or :py:class:`~pyasn1.type.univ.Enumerated` object
        Python integer or named value (as string literal) or *Enumerated* class instance.

    tagSet: :py:class:`~pyasn1.type.tag.TagSet`
        Object representing non-default ASN.1 tag(s)

    subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
        Object representing non-default ASN.1 subtype constraint(s)

    namedValues: :py:class:`~pyasn1.type.namedval.NamedValues`
        Object representing non-default symbolic aliases for numbers

    Raises
    ------
    : :py:class:`pyasn1.error.PyAsn1Error`
        On constraint violation or bad initializer.

    """
    #: Default :py:class:`~pyasn1.type.tag.TagSet` object for ASN.1
    #: *Enumerated* objects
    tagSet = tag.initTagSet(
        tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 0x0A)
    )
    baseTagSet = tagSet

    #: Default :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
    #: object imposing constraints on initialization values.
    subtypeSpec = constraint.ConstraintsIntersection()

    #: Default :py:class:`~pyasn1.type.namedval.NamedValues` object
    #: representing symbolic aliases for numbers
    namedValues = namedval.NamedValues()

    def clone(self, value=noValue, tagSet=None, subtypeSpec=None,
              namedValues=None):
        """Creates a copy of object representing ASN.1 ENUMERATED type or value.

        If additional parameters are specified, they will be used
        in resulting object instead of corresponding parameters of
        current object.

        Parameters
        ----------
        value : :class:`int`, :class:`str` or :py:class:`~pyasn1.type.univ.Enumerated` object
            Initialization value to pass to new ASN.1 object instead of 
            inheriting one from the caller.

        tagSet: :py:class:`~pyasn1.type.tag.TagSet`
            Object representing ASN.1 tag(s) to use in new object instead of inheriting from the caller

        subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
            Object representing ASN.1 subtype constraint(s) to use in new object instead of inheriting from the caller

        namedValues: :py:class:`~pyasn1.type.namedval.NamedValues`
            Object representing symbolic aliases for numbers to use instead of inheriting from caller

        Returns
        -------
        : :py:class:`~pyasn1.type.univ.Enumerated`
            new instance of ENUMERATED type/value

        """
        return Integer.clone(self, value, tagSet, subtypeSpec, namedValues)

    def subtype(self, value=noValue, implicitTag=None, explicitTag=None,
                subtypeSpec=None, namedValues=None):
        """Creates a copy of ENUMERATED object representing ASN.1 subtype or a value.

        If additional parameters are specified, they will be merged
        with the ones of the caller, then applied to newly created object.

        Parameters
        ----------
        value : :class:`int`, :class:`str` or :py:class:`~pyasn1.type.univ.Enumerated` object
            Initialization value to pass to new ASN.1 object instead of 
            inheriting one from the caller.

        implicitTag: :py:class:`~pyasn1.type.tag.Tag`
            Implicitly apply given ASN.1 tag object to caller's 
            :py:class:`~pyasn1.type.tag.TagSet`, then use the result as
            new object's ASN.1 tag(s).

        explicitTag: :py:class:`~pyasn1.type.tag.Tag`
            Explicitly apply given ASN.1 tag object to caller's 
            :py:class:`~pyasn1.type.tag.TagSet`, then use the result as
            new object's ASN.1 tag(s).

        subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
            Object representing ASN.1 subtype constraint(s) to use in new object instead of inheriting from the caller

        namedValues: :py:class:`~pyasn1.type.namedval.NamedValues`
            Add given object representing symbolic aliases for numbers
            to one of the caller, then use the result as new object's
            named numbers.

        Returns
        -------
        : :py:class:`~pyasn1.type.univ.Enumerated`
            new instance of ENUMERATED type/value

        """
        return Integer.subtype(self, value, implicitTag, explicitTag, subtypeSpec, namedValues)


# "Structured" ASN.1 types

class SetOf(base.AbstractConstructedAsn1Item):
    """Creates SET OF ASN.1 type.

     The SET OF type resembles a collection of elements of a single ASN.1 type.
     Ordering of the components is not preserved upon de/serialization.
     Objects of this type try to duck-type Python :class:`list` objects.

     Parameters
     ----------
     componentType : :py:class:`~pyasn1.type.base.PyAsn1Item` derivative
         A pyasn1 object representing ASN.1 type allowed within this collection

     tagSet: :py:class:`~pyasn1.type.tag.TagSet`
         Object representing non-default ASN.1 tag(s)

     subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
         Object representing non-default ASN.1 subtype constraint(s)

     sizeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
         Object representing collection size constraint
     """
    #: Default :py:class:`~pyasn1.type.tag.TagSet` object for ASN.1
    #: *SetOf* objects
    tagSet = tag.initTagSet(
        tag.Tag(tag.tagClassUniversal, tag.tagFormatConstructed, 0x11)
    )
    baseTagSet = tagSet

    #: Default :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
    #: object imposing constraints on collection contents
    subtypeSpec = constraint.ConstraintsIntersection()

    #: Default :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
    #: object imposing size constraint on collection contents
    sizeSpec = constraint.ConstraintsIntersection()

    #: Default pyasn1 object (e.g. :py:class:`~pyasn1.type.base.PyAsn1Item` derivative)
    #: representing ASN.1 type allowed within this collection
    componentType = None

    typeId = 1
    strictConstraints = False

    # Python list protocol

    def clear(self):
        self._componentValues = []
        self._componentValuesSet = 0

    def append(self, value):
        self[len(self)] = value

    def count(self, value):
        return self._componentValues.count(value)

    def extend(self, values):
        for value in values:
            self.append(value)

    def index(self, value, start=0, stop=None):
        if stop is None:
            stop = len(self)
        return self._componentValues.index(value, start, stop)

    def reverse(self):
        self._componentValues.reverse()

    def sort(self, key=None, reverse=False):
        self._componentValues.sort(key=key, reverse=reverse)

    def __iter__(self):
        return iter(self._componentValues)

    def _cloneComponentValues(self, myClone, cloneValueFlag):
        idx = 0
        l = len(self._componentValues)
        while idx < l:
            c = self._componentValues[idx]
            if c is not None:
                if isinstance(c, base.AbstractConstructedAsn1Item):
                    myClone.setComponentByPosition(
                        idx, c.clone(cloneValueFlag=cloneValueFlag)
                    )
                else:
                    myClone.setComponentByPosition(idx, c.clone())
            idx += 1

    def _verifyComponent(self, idx, value):
        t = self._componentType
        if t is None:
            return
        if not t.isSameTypeWith(value, matchConstraints=self.strictConstraints):
            raise error.PyAsn1Error('Component value is tag-incompatible: %r vs %r' % (value, t))
        if self.strictConstraints and \
                not t.isSuperTypeOf(value, matchTags=False):
            raise error.PyAsn1Error('Component value is constraints-incompatible: %r vs %r' % (value, t))

    def getComponentByPosition(self, idx):
        """Returns a component by index.

           Parameters
           ----------
           idx : :class:`int`
               component index (zero-based)

           Returns
           -------
           : :py:class:`~pyasn1.type.base.PyAsn1Item`
               a pyasn1 object

           Note
           ----
           Equivalent to Python sequence subscription operation (e.g. `[]`).
        """
        return self._componentValues[idx]

    def setComponentByPosition(self, idx, value=noValue, verifyConstraints=True):
        """Assign a component by position.

           Parameters
           ----------
           idx : :class:`int`
               component index (zero-based)

           value : :class:`object` or :py:class:`~pyasn1.type.base.PyAsn1Item` derivative
               A Python or pyasn1 object to assign

           verifyConstraints : :class:`bool`
                If `False`, skip constraints validation

           Returns
           -------
           self

           Note
           ----
           Equivalent to Python sequence item assignment operation (e.g. `[]`).
        """
        l = len(self._componentValues)
        if idx >= l:
            self._componentValues = self._componentValues + (idx - l + 1) * [None]
        if self.isNoValue(value):
            if self._componentValues[idx] is None:
                if self._componentType is None:
                    raise error.PyAsn1Error('Component type not defined')
                self._componentValues[idx] = self._componentType.clone()
                self._componentValuesSet += 1
            return self
        elif not isinstance(value, base.Asn1Item):
            if self._componentType is None:
                raise error.PyAsn1Error('Component type not defined')
            if isinstance(self._componentType, base.AbstractSimpleAsn1Item):
                value = self._componentType.clone(value=value)
            else:
                raise error.PyAsn1Error('Instance value required')
        if verifyConstraints:
            if self._componentType is not None:
                self._verifyComponent(idx, value)
            self._verifySubtypeSpec(value, idx)
        if self._componentValues[idx] is None:
            self._componentValuesSet += 1
        self._componentValues[idx] = value
        return self

    def getComponentTagMap(self):
        if self._componentType is not None:
            return self._componentType.getTagMap()

    def prettyPrint(self, scope=0):
        scope += 1
        r = self.__class__.__name__ + ':\n'
        for idx in range(len(self._componentValues)):
            r += ' ' * scope
            if self._componentValues[idx] is None:
                r += '<empty>'
            else:
                r = r + self._componentValues[idx].prettyPrint(scope)
        return r

    def prettyPrintType(self, scope=0):
        scope += 1
        r = '%s -> %s {\n' % (self.getTagSet(), self.__class__.__name__)
        if self._componentType is not None:
            r += ' ' * scope
            r = r + self._componentType.prettyPrintType(scope)
        return r + '\n' + ' ' * (scope - 1) + '}'


class SequenceOf(SetOf):
    """Creates SEQUENCE OF ASN.1 type.

      The SEQUENCE OF type resembles a collection of elements of a single ASN.1 type.
      Ordering of the components is preserved upon de/serialization.
      Objects of this type try to duck-type Python :class:`list` objects.

      Parameters
      ----------
      componentType : :py:class:`~pyasn1.type.base.PyAsn1Item` derivative
          A pyasn1 object representing ASN.1 type allowed within this collection

      tagSet: :py:class:`~pyasn1.type.tag.TagSet`
          Object representing non-default ASN.1 tag(s)

      subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
          Object representing non-default ASN.1 subtype constraint(s)

      sizeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
          Object representing collection size constraint
    """
    #: Default :py:class:`~pyasn1.type.tag.TagSet` object for ASN.1
    #: *SeeuqnceOf* objects
    tagSet = tag.initTagSet(
        tag.Tag(tag.tagClassUniversal, tag.tagFormatConstructed, 0x10)
    )
    baseTagSet = tagSet

    typeId = 2


class SequenceAndSetBase(base.AbstractConstructedAsn1Item):
    componentType = namedtype.NamedTypes()
    strictConstraints = False

    def __init__(self, componentType=None, tagSet=None,
                 subtypeSpec=None, sizeSpec=None):
        if componentType is None:
            componentType = self.componentType
        base.AbstractConstructedAsn1Item.__init__(
            self, componentType.clone(), tagSet, subtypeSpec, sizeSpec
        )
        self._componentTypeLen = len(self._componentType)

    def __getitem__(self, idx):
        if octets.isStringType(idx):
            return self.getComponentByName(idx)
        else:
            return base.AbstractConstructedAsn1Item.__getitem__(self, idx)

    def __setitem__(self, idx, value):
        if octets.isStringType(idx):
            self.setComponentByName(idx, value)
        else:
            base.AbstractConstructedAsn1Item.__setitem__(self, idx, value)

    def __contains__(self, key):
        return key in self._componentType

    def __iter__(self):
        return iter(self._componentType)

    # Python dict protocol

    def values(self):
        for idx in range(self._componentTypeLen):
            yield self[idx]

    def keys(self):
        return iter(self._componentType)

    def items(self):
        for idx in range(self._componentTypeLen):
            yield self._componentType[idx].getName(), self[idx]

    def update(self, *iterValue, **mappingValue):
        for k, v in iterValue:
            self[k] = v
        for k in mappingValue:
            self[k] = mappingValue[k]

    def clear(self):
        self._componentValues = []
        self._componentValuesSet = 0

    def _cloneComponentValues(self, myClone, cloneValueFlag):
        idx = 0
        l = len(self._componentValues)
        while idx < l:
            c = self._componentValues[idx]
            if c is not None:
                if isinstance(c, base.AbstractConstructedAsn1Item):
                    myClone.setComponentByPosition(
                        idx, c.clone(cloneValueFlag=cloneValueFlag)
                    )
                else:
                    myClone.setComponentByPosition(idx, c.clone())
            idx += 1

    def _verifyComponent(self, idx, value):
        if idx >= self._componentTypeLen:
            raise error.PyAsn1Error(
                'Component type error out of range'
            )
        t = self._componentType[idx].getType()
        if not t.isSameTypeWith(value, matchConstraints=self.strictConstraints):
            raise error.PyAsn1Error('Component value is tag-incompatible: %r vs %r' % (value, t))
        if self.strictConstraints and \
                not t.isSuperTypeOf(value, matchTags=False):
            raise error.PyAsn1Error('Component value is constraints-incompatible: %r vs %r' % (value, t))

    def getComponentByName(self, name):
        """Returns a component by name.

           Parameters
           ----------
           name : :class:`str`
               component name

           Returns
           -------
           : :py:class:`~pyasn1.type.base.PyAsn1Item`
               a pyasn1 object

           Note
           ----
           Equivalent to Python :class:`dict` subscription operation (e.g. `[]`).
        """
        return self.getComponentByPosition(
            self._componentType.getPositionByName(name)
        )

    def setComponentByName(self, name, value=noValue, verifyConstraints=True):
        """Assign a component by name.

           Parameters
           ----------
           name : :class:`str`
               component name

           value : :class:`object` or :py:class:`~pyasn1.type.base.PyAsn1Item` derivative
               A Python or pyasn1 object to assign

           verifyConstraints : :class:`bool`
                If `False`, skip constraints validation

           Returns
           -------
           self

           Note
           ----
           Equivalent to Python :class:`dict` item assignment operation (e.g. `[]`).
        """
        return self.setComponentByPosition(
            self._componentType.getPositionByName(name), value, verifyConstraints
        )

    def getComponentByPosition(self, idx):
        """Returns a component by index.

           Parameters
           ----------
           idx : :class:`int`
               component index (zero-based)

           Returns
           -------
           : :py:class:`~pyasn1.type.base.PyAsn1Item`
               a pyasn1 object

           Note
           ----
           Equivalent to Python sequence subscription operation (e.g. `[]`).
        """
        try:
            return self._componentValues[idx]
        except IndexError:
            if idx < self._componentTypeLen:
                return
            raise

    def setComponentByPosition(self, idx, value=noValue,
                               verifyConstraints=True,
                               exactTypes=False,
                               matchTags=True,
                               matchConstraints=True):
        """Assign a component by position.

           Parameters
           ----------
           idx : :class:`int`
               component index (zero-based)

           value : :class:`object` or :py:class:`~pyasn1.type.base.PyAsn1Item` derivative
               A Python or pyasn1 object to assign

           verifyConstraints : :class:`bool`
                If `False`, skip constraints validation

           Returns
           -------
           self

           Note
           ----
           Equivalent to Python sequence item assignment operation (e.g. `[]`).
        """
        l = len(self._componentValues)
        if idx >= l:
            self._componentValues = self._componentValues + (idx - l + 1) * [None]
        if self.isNoValue(value):
            if self._componentValues[idx] is None:
                self._componentValues[idx] = self._componentType.getTypeByPosition(idx).clone()
                self._componentValuesSet += 1
            return self
        elif not isinstance(value, base.Asn1Item):
            t = self._componentType.getTypeByPosition(idx)
            if isinstance(t, base.AbstractSimpleAsn1Item):
                value = t.clone(value=value)
            else:
                raise error.PyAsn1Error('Instance value required')
        if verifyConstraints:
            if self._componentTypeLen:
                self._verifyComponent(idx, value)
            self._verifySubtypeSpec(value, idx)
        if self._componentValues[idx] is None:
            self._componentValuesSet += 1
        self._componentValues[idx] = value
        return self

    def getNameByPosition(self, idx):
        if self._componentTypeLen:
            return self._componentType.getNameByPosition(idx)

    def getDefaultComponentByPosition(self, idx):
        if self._componentTypeLen and self._componentType[idx].isDefaulted:
            return self._componentType[idx].getType()

    def getComponentType(self):
        if self._componentTypeLen:
            return self._componentType

    def setDefaultComponents(self):
        """Assign default values to all defaulted components.

           Returns
           -------
           self
        """
        if self._componentTypeLen == self._componentValuesSet:
            return
        idx = self._componentTypeLen
        while idx:
            idx -= 1
            if self._componentType[idx].isDefaulted:
                if self.getComponentByPosition(idx) is None:
                    self.setComponentByPosition(idx)
            elif not self._componentType[idx].isOptional:
                if self.getComponentByPosition(idx) is None:
                    raise error.PyAsn1Error(
                        'Uninitialized component #%s at %r' % (idx, self)
                    )
        return self

    def prettyPrint(self, scope=0):
        """Return an object representation string.

           Returns
           -------
           : :class:`str`
               Human-friendly object representation.
        """
        scope += 1
        r = self.__class__.__name__ + ':\n'
        for idx in range(len(self._componentValues)):
            if self._componentValues[idx] is not None:
                r += ' ' * scope
                componentType = self.getComponentType()
                if componentType is None:
                    r += '<no-name>'
                else:
                    r = r + componentType.getNameByPosition(idx)
                r = '%s=%s\n' % (
                    r, self._componentValues[idx].prettyPrint(scope)
                )
        return r

    def prettyPrintType(self, scope=0):
        scope += 1
        r = '%s -> %s {\n' % (self.getTagSet(), self.__class__.__name__)
        for idx in range(len(self.componentType)):
            r += ' ' * scope
            r += '"%s"' % self.componentType.getNameByPosition(idx)
            r = '%s = %s\n' % (
                r, self._componentType.getTypeByPosition(idx).prettyPrintType(scope)
            )
        return r + '\n' + ' ' * (scope - 1) + '}'


class Sequence(SequenceAndSetBase):
    """Creates SEQUENCE ASN.1 type.

      The SEQUENCE type resembles an ordered collection of named ASN.1 values.
      Objects of this type try to duck-type Python :class:`dict` objects.

      Parameters
      ----------
      componentType : :py:class:`~pyasn1.type.namedtype.NamedType`
          Object holding named ASN.1 types allowed within this collection

      tagSet: :py:class:`~pyasn1.type.tag.TagSet`
          Object representing non-default ASN.1 tag(s)

      subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
          Object representing non-default ASN.1 subtype constraint(s)

      sizeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
          Object representing collection size constraint
    """
    #: Default :py:class:`~pyasn1.type.tag.TagSet` object for ASN.1
    #: *Sequence* objects
    tagSet = tag.initTagSet(
        tag.Tag(tag.tagClassUniversal, tag.tagFormatConstructed, 0x10)
    )
    baseTagSet = tagSet

    #: Default :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
    #: object imposing constraints on collection contents
    subtypeSpec = constraint.ConstraintsIntersection()

    #: Default :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
    #: object imposing size constraint on collection contents
    sizeSpec = constraint.ConstraintsIntersection()

    #: Default collection of ASN.1 types of component (e.g. :py:class:`~pyasn1.type.namedtype.NamedType`)
    #: representing ASN.1 types allowed within this collection
    componentType = namedtype.NamedTypes()

    typeId = 3

    def getComponentTagMapNearPosition(self, idx):
        if self._componentType:
            return self._componentType.getTagMapNearPosition(idx)

    def getComponentPositionNearType(self, tagSet, idx):
        if self._componentType:
            return self._componentType.getPositionNearType(tagSet, idx)
        else:
            return idx


class Set(SequenceAndSetBase):
    """Creates SET ASN.1 type.

      The SET type resembles an unordered collection of named ASN.1 values.
      Objects of this type try to duck-type Python :class:`dict` objects.

      Parameters
      ----------
      componentType : :py:class:`~pyasn1.type.namedtype.NamedType`
          Object holding named ASN.1 types allowed within this collection

      tagSet: :py:class:`~pyasn1.type.tag.TagSet`
          Object representing non-default ASN.1 tag(s)

      subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
          Object representing non-default ASN.1 subtype constraint(s)

      sizeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
          Object representing collection size constraint
    """
    #: Default :py:class:`~pyasn1.type.tag.TagSet` object for ASN.1
    #: *Set* objects
    tagSet = tag.initTagSet(
        tag.Tag(tag.tagClassUniversal, tag.tagFormatConstructed, 0x11)
    )
    baseTagSet = tagSet

    #: Default :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
    #: object imposing constraints on collection contents
    subtypeSpec = constraint.ConstraintsIntersection()

    #: Default :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
    #: object imposing size constraint on collection contents
    sizeSpec = constraint.ConstraintsIntersection()

    #: Default collection of ASN.1 types of component (e.g. :py:class:`~pyasn1.type.namedtype.NamedType`)
    #: representing ASN.1 types allowed within this collection
    componentType = namedtype.NamedTypes()

    typeId = 4

    def getComponent(self, innerFlag=0):
        return self

    def getComponentByType(self, tagSet, innerFlag=0):
        """Returns component by ASN.1 tag.

           Parameters
           ----------
           tagSet : :py:class:`~pyasn1.type.tag.TagSet`
               Object representing ASN.1 tags

           Returns
           -------
           : :py:class:`~pyasn1.type.base.PyAsn1Item`
               a pyasn1 object
        """
        c = self.getComponentByPosition(
            self._componentType.getPositionByType(tagSet)
        )
        if innerFlag and isinstance(c, Set):
            # get inner component by inner tagSet
            return c.getComponent(1)
        else:
            # get outer component by inner tagSet
            return c

    def setComponentByType(self, tagSet, value=noValue, innerFlag=0,
                           verifyConstraints=True):
        """Assign component by ASN.1 tag.

            Parameters
            ----------
            tagSet : :py:class:`~pyasn1.type.tag.TagSet`
               Object representing ASN.1 tags

            value : :class:`object` or :py:class:`~pyasn1.type.base.PyAsn1Item` derivative
                A Python or pyasn1 object to assign

            verifyConstraints : :class:`bool`
                 If `False`, skip constraints validation

            Returns
            -------
            self
        """
        idx = self._componentType.getPositionByType(tagSet)
        t = self._componentType.getTypeByPosition(idx)
        if innerFlag:  # set inner component by inner tagSet
            if t.getTagSet():
                return self.setComponentByPosition(
                    idx, value, verifyConstraints
                )
            else:
                t = self.setComponentByPosition(idx).getComponentByPosition(idx)
                return t.setComponentByType(
                    tagSet, value, innerFlag, verifyConstraints
                )
        else:  # set outer component by inner tagSet
            return self.setComponentByPosition(
                idx, value, verifyConstraints
            )

    def getComponentTagMap(self):
        if self._componentType:
            return self._componentType.getTagMap(True)

    def getComponentPositionByType(self, tagSet):
        if self._componentType:
            return self._componentType.getPositionByType(tagSet)


class Choice(Set):
    """Create CHOICE ASN.1 type.

      The CHOICE type can only hold a single component belonging
      to a list of allowed types.
      Objects of this type try to duck-type Python :class:`dict` objects except
      that they pretend to contain a single key-value at a time.

      Parameters
      ----------
      componentType : :py:class:`~pyasn1.type.namedtype.NamedType`
          Object holding named ASN.1 types allowed within this collection

      tagSet: :py:class:`~pyasn1.type.tag.TagSet`
          Object representing non-default ASN.1 tag(s)

      subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
          Object representing non-default ASN.1 subtype constraint(s)
    """
    #: Default :py:class:`~pyasn1.type.tag.TagSet` object for ASN.1
    #: *Choice* objects (untagged by default)
    tagSet = tag.TagSet()  # untagged
    baseTagSet = tagSet

    #: Default :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
    #: object imposing constraints on collection contents
    subtypeSpec = constraint.ConstraintsIntersection()

    sizeSpec = constraint.ConstraintsIntersection(
        constraint.ValueSizeConstraint(1, 1)
    )

    #: Default collection of ASN.1 types of component (e.g. :py:class:`~pyasn1.type.namedtype.NamedType`)
    #: representing ASN.1 types allowed within this collection
    componentType = namedtype.NamedTypes()

    typeId = 5

    _currentIdx = None

    def __eq__(self, other):
        if self._componentValues:
            return self._componentValues[self._currentIdx] == other
        return NotImplemented

    def __ne__(self, other):
        if self._componentValues:
            return self._componentValues[self._currentIdx] != other
        return NotImplemented

    def __lt__(self, other):
        if self._componentValues:
            return self._componentValues[self._currentIdx] < other
        return NotImplemented

    def __le__(self, other):
        if self._componentValues:
            return self._componentValues[self._currentIdx] <= other
        return NotImplemented

    def __gt__(self, other):
        if self._componentValues:
            return self._componentValues[self._currentIdx] > other
        return NotImplemented

    def __ge__(self, other):
        if self._componentValues:
            return self._componentValues[self._currentIdx] >= other
        return NotImplemented

    if sys.version_info[0] <= 2:
        def __nonzero__(self):
            return bool(self._componentValues)
    else:
        def __bool__(self):
            return bool(self._componentValues)

    def __len__(self):
        return self._currentIdx is not None and 1 or 0

    def __contains__(self, key):
        if self._currentIdx is None:
            return False
        return key == self._componentType[self._currentIdx].getName()

    def __iter__(self):
        if self._currentIdx is None:
            raise StopIteration
        yield self._componentType[self._currentIdx].getName()

    def verifySizeSpec(self):
        if self._currentIdx is None:
            raise error.PyAsn1Error('Component not chosen')
        else:
            self._sizeSpec(' ')

    def _cloneComponentValues(self, myClone, cloneValueFlag):
        try:
            c = self.getComponent()
        except error.PyAsn1Error:
            pass
        else:
            if isinstance(c, Choice):
                tagSet = c.getEffectiveTagSet()
            else:
                tagSet = c.getTagSet()
            if isinstance(c, base.AbstractConstructedAsn1Item):
                myClone.setComponentByType(
                    tagSet, c.clone(cloneValueFlag=cloneValueFlag)
                )
            else:
                myClone.setComponentByType(tagSet, c.clone())

    def setComponentByPosition(self, idx, value=noValue, verifyConstraints=True):
        """Assign a component by position.

             Parameters
             ----------
             idx : :class:`int`
                 component index (zero-based)

             value : :class:`object` or :py:class:`~pyasn1.type.base.PyAsn1Item` derivative
                 A Python or pyasn1 object to assign

             verifyConstraints : :class:`bool`
                  If `False`, skip constraints validation

             Returns
             -------
             self

             Note
             ----
             Equivalent to Python sequence item assignment operation (e.g. `[]`).
        """
        l = len(self._componentValues)
        if idx >= l:
            self._componentValues = self._componentValues + (idx - l + 1) * [None]
        if self._currentIdx is not None:
            self._componentValues[self._currentIdx] = None
        if self.isNoValue(value):
            if self._componentValues[idx] is None:
                self._componentValues[idx] = self._componentType.getTypeByPosition(idx).clone()
                self._componentValuesSet = 1
                self._currentIdx = idx
            return self
        elif not isinstance(value, base.Asn1Item):
            value = self._componentType.getTypeByPosition(idx).clone(
                value=value
            )
        if verifyConstraints:
            if self._componentTypeLen:
                self._verifyComponent(idx, value)
            self._verifySubtypeSpec(value, idx)
        self._componentValues[idx] = value
        self._currentIdx = idx
        self._componentValuesSet = 1
        return self

    def getMinTagSet(self):
        if self._tagSet:
            return self._tagSet
        else:
            return self._componentType.genMinTagSet()

    def getEffectiveTagSet(self):
        if self._tagSet:
            return self._tagSet
        else:
            c = self.getComponent()
            if isinstance(c, Choice):
                return c.getEffectiveTagSet()
            else:
                return c.getTagSet()

    def getTagMap(self):
        if self._tagSet:
            return Set.getTagMap(self)
        else:
            return Set.getComponentTagMap(self)

    def getComponent(self, innerFlag=0):
        """Return component being held.

            Returns
            -------
            : :py:class:`~pyasn1.type.base.PyAsn1Item`
                a pyasn1 object
        """
        if self._currentIdx is None:
            raise error.PyAsn1Error('Component not chosen')
        else:
            c = self._componentValues[self._currentIdx]
            if innerFlag and isinstance(c, Choice):
                return c.getComponent(innerFlag)
            else:
                return c

    def getName(self, innerFlag=0):
        if self._currentIdx is None:
            raise error.PyAsn1Error('Component not chosen')
        else:
            if innerFlag:
                c = self._componentValues[self._currentIdx]
                if isinstance(c, Choice):
                    return c.getName(innerFlag)
            return self._componentType.getNameByPosition(self._currentIdx)

    def setDefaultComponents(self):
        pass


class Any(OctetString):
    """Creates ASN.1 ANY type or object.

    The ANY type denotes an arbitrary value of an arbitrary type, where
    the arbitrary type is possibly defined by accompaning object identifier
    or an integer identifier. Usually ANY value holds a serialized
    representation of an opaque type.

    Parameters
    ----------
    value : :class:`str`, :class:`bytes` or :py:class:`~pyasn1.type.univ.Any` object
        Python string literal or bytes or *Any*
        class instance.

    tagSet: :py:class:`~pyasn1.type.tag.TagSet`
        Object representing non-default ASN.1 tag(s)

    subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
        Object representing ASN.1 subtype constraint(s) to use in new object instead of inheriting from the caller

    encoding: :py:class:`str`
        Unicode codec ID to encode/decode :class:`unicode` (Python 2) or
        :class:`str` (Python 3) the payload when *Any* object is used
        in string context.

    binValue: :py:class:`str`
        Binary string initializer. Example: '10110011'.
        
    hexValue: :py:class:`str`
        Hexadecimal string initializer. Example: 'DEADBEEF'.

    Raises
    ------
    : :py:class:`pyasn1.error.PyAsn1Error`
        On constraint violation or bad initializer.

    """
    #: Default :py:class:`~pyasn1.type.tag.TagSet` object for ASN.1
    #: *OctetString* objects (untagged by default)
    tagSet = tag.TagSet()  # untagged
    baseTagSet = tagSet
    typeId = 6

    #: Default :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
    #: object imposing constraints on initialization values.
    subtypeSpec = constraint.ConstraintsIntersection()

    def getTagMap(self):
        return tagmap.TagMap(
            {self.getTagSet(): self},
            {eoo.endOfOctets.getTagSet(): eoo.endOfOctets},
            self
        )

    def clone(self, value=noValue, tagSet=None, subtypeSpec=None,
              encoding=None, binValue=noValue, hexValue=noValue):
        """Creates a copy of ANY object representing ASN.1 type or value.

        If additional parameters are specified, they will be used
        in resulting object instead of corresponding parameters of
        current object.

        Parameters
        ----------
        value : :class:`str`, :class:`bytes` or :py:class:`~pyasn1.type.univ.Any` object
            Initialization value to pass to new ASN.1 object instead of 
            inheriting one from the caller.

        tagSet: :py:class:`~pyasn1.type.tag.TagSet`
            Object representing ASN.1 tag(s) to use in new object instead of inheriting from the caller

        subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
            Object representing ASN.1 subtype constraint(s) to use in new object instead of inheriting from the caller

        encoding: :py:class:`str`
            Unicode codec ID to encode/decode :class:`unicode` (Python 2)
            or :class:`str` (Python 3) the payload when *OctetString*
            object is used in string context.

        binValue: :py:class:`str`
            Binary string initializer. Example: '10110011'.
        
        hexValue: :py:class:`str`
            Hexadecimal string initializer. Example: 'DEADBEEF'.

        Returns
        -------
        : :py:class:`~pyasn1.type.univ.Any`
            new instance of ANY type/value

        """
        return OctetString.clone(self, value, tagSet, subtypeSpec, encoding, binValue, hexValue)

    def subtype(self, value=noValue, implicitTag=None, explicitTag=None,
                subtypeSpec=None, encoding=None, binValue=noValue,
                hexValue=noValue):
        """Creates a copy of ANY object representing ASN.1 subtype or a value.

        If additional parameters are specified, they will be merged
        with the ones of the caller, then applied to newly created object.

        Parameters
        ----------
        value : :class:`str`, :class:`bytes` or :py:class:`~pyasn1.type.univ.Any` object
            Initialization value to pass to new ASN.1 object instead of 
            inheriting one from the caller.

        implicitTag: :py:class:`~pyasn1.type.tag.Tag`
            Implicitly apply given ASN.1 tag object to caller's 
            :py:class:`~pyasn1.type.tag.TagSet`, then use the result as
            new object's ASN.1 tag(s).

        explicitTag: :py:class:`~pyasn1.type.tag.Tag`
            Explicitly apply given ASN.1 tag object to caller's 
            :py:class:`~pyasn1.type.tag.TagSet`, then use the result as
            new object's ASN.1 tag(s).

        subtypeSpec: :py:class:`~pyasn1.type.constraint.ConstraintsIntersection`
            Object representing ASN.1 subtype constraint(s) to use in new object instead of inheriting from the caller

        encoding: :py:class:`str`
            Unicode codec ID to encode/decode :class:`unicode` (Python 2)
            or :class:`str` (Python 3) the payload when *Any*
            object is used in string context.

        binValue: :py:class:`str`
            Binary string initializer. Example: '10110011'.
        
        hexValue: :py:class:`str`
            Hexadecimal string initializer. Example: 'DEADBEEF'.

        Returns
        -------
        : :py:class:`~pyasn1.type.univ.Any`
            new instance of ANY type/value

        """
        return OctetString.subtype(self, value, implicitTag, explicitTag,
                                   subtypeSpec, encoding, binValue, hexValue)

# XXX
# coercion rules?
