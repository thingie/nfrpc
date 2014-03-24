import struct
import datetime.datetime
import math

class InvalidTypeError(Exception):
    def __init__(self, msg):
        self.value = msg

    def __str__(self):
        return repr(self.value)

def _writeUnsignedInt(data):
    bitneed = math.ceil(math.ceil(math.log(data) / math.log(2)) / 8.0)
    # we can easily use 1, 2, 4 and 8 bytes
    # that's precise enough
    rdata = None

    if bitneed == 1:
        rdata = struct.pack("<B", data)
    elif bitneed == 2:
        rdata = struct.pack("<H", data)
    elif bitneed <= 4:
        rdata = struct.pack("<I", data)
    elif bitneed <= 8:
        rdata = struct.pack("<Q", data)
    else:
        raise 'integer too large'

    return rdata

def _writeSignedInt(data):
    bitneed = math.ceil((math.ceil(math.log(data) / math.log(2)) + 1) / 8.0)
    rdata = None

    if bitneed == 1:
        rdata = struct.pack("<b", data)
    elif bitneed == 2:
        rdata = struct.pack("<h", data)
    elif bitneed <= 4:
        rdata = struct.pack("<i", data)
    elif bitneed <= 8:
        rdata = struct.pack("<q", data)
    else:
        raise 'integer too large'

    return rdata

def _writeMagic(data):
    return struct.pack("<B<B<B<B", 0xCA, 0x11, 2, 0)

def _writePositiveInteger(data):
    byteload = _writeUnsignedInt(data)
    return chr(0b00111000 | len(byteload)).encode('ascii') + byteload

def _writeNegativeInteger(data):
    byteload = _writeUnsignedInt(math.fabs(data))
    return chr(0b01000000 | len(byteload)).encode('ascii') + byteload

def _writeString(data):
    bytedata = data.encode('utf-8')
    bytelen = len(bytedata)

    lenlen = _writeUnsignedInt(bytelen)

    return chr(0b00100000 | (len(lenlen) - 1)).encode('ascii') + lenlen + bytedata

def _writeBinary(data):
    bytelen = len(data)

    lenlen = _writeUnsignedInt(bytelen)

    return chr(0b00100000 | (len(lenlen) - 1)).encode('ascii') + lenlen + data

def _writeNull():
    return chr(0b01100000).encode('ascii')

def _writeStruct(data):
    members = len(data)
    memberLenBytes = _writePositiveInteger(members)

    innerBytes = bytes()
    for key in data:
        dName = key.encode('utf-8')
        dNameLen = len(dName)
        dValue = _encodeValue(data[key])
        innerBytes += struct.pack("<B", dNameLen) + dName + dValue

    return chr(0b01010000 | (len(memberLenBytes) - 1)).encode('ascii') +\
        innerBytes

def _writeArray(data):
    members = len(data)
    memberLenBytes = _writePositiveInteger(members)

    innerBytes = bytes()
    for d in data:
        innerBytes += _encodeValue(d)

    return chr(0b01011000 | (len(memberLenBytes) - 1)).encode('ascii') +\
        innerBytes

# we don't implement writing of 1.0 integer, later, if needed

def _writeBoolean(data):
    if data == True:
        return chr(0b00010001).encode('ascii')
    else:
        return chr(0b00010000).encode('ascii')

def _writeDouble(data):
    bytedata = struct.pack("<d", data)

    return chr(0b00011000).encode('ascii') + bytedata

def _writeDatetime(data):
    # fuck this shit
    pass

def _writeMethodCall(name, data):
    nameEnc = name.encode('utf-8')
    params = bytes()

    if data is None:
        params = _writeNull()
    else:
        for param in data:
            params += _encodeValue(data)
    return _writeMagic() + chr(0b01101000).encode('ascii') +\
        struct.pack("<B", len(nameEnc)) + nameEnc + params

def _writeMethodResponse(data):
    return _writeMagic() + chr(0b01110000).encode('ascii') + _encodeValue(data)

def _writeFaultResponse(code, msg):
    return _writeMagic() + chr(0b01111000).encode('ascii') +\
        _writePositiveInteger(code) + _writeString(msg)

def _encodeValue(data):
    if type(data) == int:
        if data < 0:
            return _writeNegativeInteger(data)
        else:
            return _writePositiveInteger(data)
    elif type(data) == str:
        return _writeString(data)
    elif type(data) == bytes:
        return _writeBinary(data)
    elif data is None:
        return _writeNull()
    elif type(data) == dict:
        return _writeStruct(data)
    elif type(data) == list:
        return _writeArray(data)
    elif type(data) == datetime.datetime:
        return _writeDatetime(data)
    elif type(data) == bool:
        return _writeBool(data)
    elif type(data) == float:
        return _writeDouble(data)
    else:
        raise InvalidTypeError("Unusable type \"%s\"" % (type(data)))
