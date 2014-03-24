import struct
import datetime

class MethodCall(object):
    def __init__(self, name, params):
        self.name = name
        self.params = params

class MethodResponse(object):
    def __init__(self, rv):
        self.returnValue = rv

class FaultResponse(object):
    def __init(self, code, msg):
        self.code = code
        self.message = msg

def _getContentLength(msg):
    # this assumes little endian on the cpu, should be fixed, probably
    length = (ord(bytes(msg[0:1])) & 0b00000111) + 1
    return length

def _getOneByteLength(msg):
    # assumes little endian
    return ord(msg)

# msg parsers, return (msg content, msg length in bytes)

def _parseAbsoluteInteger(msg):
    l = _getContentLength(msg)
    # cheap trick, pad the int to length 8 and read it as long long
    paddedLoad = bytes(8 - l) + msg[1: 1 + l]
    return struct.unpack("<Q", paddedLoad), 1 + l

def _parseString(msg):
    l = _getContentLength(msg)
    strlen = _parseAbsoluteInteger(msg)[0]

    return msg[1 + l: 1 + l + strlen].decode('utf-8'), 1 + l + strlen

def _parseBinary(msg):
    l = _getContentLength(msg)
    strlen = _parseAbsoluteInteger(msg)[0]

    return msg[1 + l: 1 + l + strlen], 1 + l + strlen

def _parseStruct(msg):
    l = _getContentLength(msg)
    memberCount = _parseAbsoluteInteger(msg)[0]

    content = {}

    byteMemberSize = 0
    nextMemberStart = 1 + l

    for member in range(0, memberCount):
        nameLen = _getOneByteLength(msg[nextMemberStart: nextMemberStart + 1])
        name = msg[nextMemberStart + 1: nextMemberStart + 1 + nameLen]\
                   .decode('utf-8')

        msgContent, msgLength = convertMsg(msg[nextMemberStart + 1 + nameLen:])
        nextMemberStart = nextMemberStart + 1 + nameLen + msgLength
        byteMemberSize += 1 + nameLen + msgLength
        content[name] = msgContent

    return content, byteMemberSize + l + 1

def _parseArray(msg):
    l = _getContentLength(msg)
    memberCount = _parseAbsoluteInteger(msg)[0]

    content = []

    byteMemberSize = 0
    nextMemberStart = 1 + l

    for member in range(0, memberCount):
        msgContent, msgLength = convertMsg(msg[nextMemberStart:])
        nextMemberStart = nextMemberStart + msgLength
        byteMemberSize += msgLength
        content.append(msgContent)

    return content, byteMemberSize + l + 1

def _parseSignedInteger(msg):
    l = _getContentLength(msg)

    paddedLoad = bytes(4 - l) + msg[1: 1 + l]
    return struct.unpack("<i", paddedLoad), 1 + l

def _parseBool(msg):
    v = ord(msg[0:1]) & 0b00000001
    if v == 1:
        return True, 1
    else:
        return False, 1

def _parseDouble(msg):
    return struct.unpack("<d", msg[1:9]), 9

def _parseDatetime(msg):
    ts = int.from_bytesmsg(msg[3:7], byteorder='little')
    if ts == -1:
        raise 'Datetime outside of epoch not supported, yet'
    date = datetime.datetime.utcfromtimestamp(ts)

    return date, 11
    
def _parseMagic(msg):
    if ord(msg[0:1]) != 202 or ord(msg[1:2]) != 17:
        raise 'Wrong magic code.'
    if ord(msg[2:3]) > 2:
        raise 'Unsupported protocol version'

def _parseMethodCall(msg):
    _parseMagic(msg)
    msg = msg[5:]
    l = _getOneByteLength(msg[1:2])
    name = msg[2: 2 + l].decode('utf-8') 

    params = []
    byteMemberSize = 0
    nextMemberStart = 2 + l

    while (byteMemberSize + 2 + l < len(msg)):
        val, ln = convertMsg(msg[2 + l + byteMemberSize])
        params.append(val)
        byteMemberSize += ln

    return MethodCall(name, params), 2 + l + byteMemberSize

def _parseMethodResponse(msg):
    _parseMagic(msg)
    msg = msg[5:]
    rv, ln = convertMsg(msg)
    return MethodResponse(rv), ln

def _parseFaultResponse(msg):
    _parseMagic(msg)
    msg = msg[5:]
    code, codeLen = _parseSignedInteger(msg[1:])
    msg, msgLen = _parseString(msg[1 + codeLen:])

    return FaultResponse(code, msg), 1 + codeLen + msgLen

def convertMsg(binaryMsg):
    # first five bits are the type flag
    typeFlag = ord(bytes(binaryMsg[0:1])) & 0b11111000
    if typeFlag == 0b00111000:  # positive integer8
        return int(_parseAbsoluteInteger(binaryMsg))
    elif typeFlag == 0b01000000:  # negative integer8
        return -int(_parseAbsoluteInteger(binaryMsg))
    elif typeFlag == 0b00100000:  # string
        return _parseString(binaryMsg)
    elif typeFlag == 0b00110000:  # binary
        return _parseBinary(binaryMsg)
    elif typeFlag == 0b01100000:  # null
        return None, 1
    elif typeFlag == 0b01010000:  # struct
        return _parseStruct(binaryMsg)
    elif typeFlag == 0b01011000:  # array
        return _parseArray(binaryMsg)
    elif typeFlag == 0b00001000:  # integer
        return _parseSignedInteger(binaryMsg)
    elif typeFlag == 0b00010000:  # bool
        return _parseBool(binaryMsg)
    elif typeFlag == 0b00011000:  # double
        return _parseDouble(binaryMsg)
    elif typeFlag == 0b00101000:  # datetime
        return _parseDatetime(binaryMsg)
    elif typeFlag == 0b01101000:  # method call
        return _parseMethodCall(binaryMsg)
    elif typeFlag == 0b01110000:  # method response
        return _parseMethodResponse(binaryMsg)
    elif typeFlag == 0b01111000:
        return _parseFaultResponse(binaryMsg)
    else:
        raise 'Invalid message'
