from enum import Enum
import protocol
import ctypes as ct
from pprint import pprint
import logging

class DirCode(Enum):
    BYE = 0         # Client
    LIST = 1        # Client
    RESPONSE = 2    # Server
    REGISTER = 3    # Client
    QUERY = 4       # Client

class DirPacket(ct.Structure):
    _fields_ = [("id", ct.c_int),
                ("action", ct.c_ubyte),
                ("name_len", ct.c_ubyte),
                ("name", ct.c_char * 255),
                ("description_len", ct.c_int),
                ("description", ct.c_char * 743),
                ("n_peers", ct.c_int),
                ("ip", ct.c_ubyte * 4),
                ("port", ct.c_ushort)]

class DirServer(protocol.ThreadedTCPServer):
    def __init__(self, addr=('', 50817)):
        protocol.ThreadedTCPServer.__init__(self, addr, DirHandler, DirPacket)
        self.file_list = []

class DirClient(protocol.TCPClient):
    def __init__(self):
        protocol.TCPClient.__init__(self, ('localhost', 50817), DirPacket)

class DirHandler(protocol.Handler):
    def setup(self):
        logging.debug("Connected %s:%d" % self.client_address)
    def handle(self):
        while True:
            logging.debug(self.server.file_list)
            # self.request is the TCP socket connected to the client
            self.data = self.recv()
            self.server.file_list.append(self.data.id)
            if self.data.id == 0:
                break
            # just send back the same data, but upper-cased
    def finish(self):
        logging.debug("Disconnected %s:%d" % self.client_address)

'''
p=DirPacket()
print("SIZE OF PACKET")
print(ct.sizeof(p))
p.id = 123
packed = protocol.pack(p)
unpacked = protocol.unpack(packed,DirPacket)
print(protocol.debug_hex(bytearray(protocol.pack(p))))

s = DirPacket()
s.id = 0
print(protocol.debug_hex(bytearray(protocol.pack(s))))
'''

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
