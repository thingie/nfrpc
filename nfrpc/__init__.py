from . import frpc
from . import writer

class ParseErrorException(Exception):
    def __init__(self, msg):
        self.value = msg
    def __str__(self):
        return repr(self.value)

def parseFRPCMessage(msg):
    try:
        msg, len = frpc.convertMsg(msg)
        return msg
    except Exception as e:
        raise ParseErrorException(e)

def createFRPCMessage(msg):
    msg = writer._encodeValue(msg)
    return msg
