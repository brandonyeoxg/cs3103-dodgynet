from enum import Enum
import protocol
import ctypes as ct
from pprint import pprint
import logging
from tabulate import tabulate

class DirCode(Enum):
    BYE = 0         # Client
    LIST = 1        # Client
    REGISTER = 2    # Client
    QUERY = 3       # Client

# Add number of chunks
class DirPacket(ct.Structure):
    NAME_LEN = 255
    DESC_LEN = 743
    _fields_ = [("id", ct.c_int),
                ("action", ct.c_ubyte),
                ("name_len", ct.c_ubyte),
                ("name", ct.c_char * NAME_LEN),
                ("desc_len", ct.c_int),
                ("desc", ct.c_char * DESC_LEN),
                ("n_peers", ct.c_int),
                ("ip", ct.c_ubyte * 4),
                ("port", ct.c_ushort)]
    def set_action(self, action):
        self.action = action.value
    def get_action(self):
        return DirCode(self.action)
    def set_name(self, name):
        self.name = protocol.pack_str(name, DirPacket.NAME_LEN)
        self.name_len = len(name)
    def get_name(self):
        return protocol.unpack_str_s(self.name, DirPacket.NAME_LEN, self.name_len)
    def set_desc(self, desc):
        self.desc = protocol.pack_str(desc, DirPacket.DESC_LEN)
        self.desc_len = len(desc)
    def get_desc(self):
        return protocol.unpack_str_s(self.desc, DirPacket.DESC_LEN, self.desc_len)
    def set_addr(self, addr):
        self.ip = protocol.pack_ip(addr[0])
        self.port = addr[1]
    def get_addr(self):
        return (protocol.unpack_ip(self.ip), self.port)
    def __str__(self):
        return self.get_name()

class DirServer(protocol.ThreadedTCPServer):
    def __init__(self, file_list=[], addr=('', 50817)):
        logging.debug("Starting DirServer.")
        protocol.ThreadedTCPServer.__init__(self, addr, DirHandler, DirPacket)
        self.file_list = file_list
    def get_state(self):
        return self.file_list

class DirClient(protocol.TCPClient):
    headers = ["File Name", "Description", "Number of Peers", "Tracker Address"]
    def __init__(self):
        logging.debug("Starting DirClient.")
        protocol.TCPClient.__init__(self, ('localhost', 50817), DirPacket)
    def bye(self):
        logging.debug("Initiate shutdown.")
        p = DirPacket()
        p.action = DirCode.BYE.value
        self.send(p)
        p = self.recv()
        if DirCode(p.action) == DirCode.BYE:
            self.close()
            logging.debug("Shutdown successful.")
    def list(self, tablefmt="grid"):
        logging.debug("Initiate listing.")
        p = DirPacket()
        p.action = DirCode.LIST.value
        self.send(p)
        
        table = []
        p = self.recv()
        while p.id > 0:
            table.append([  p.get_name(),
                            p.get_desc(),
                            p.n_peers,
                            "%s:%d" % p.get_addr()])
            p = self.recv()
        if len(table) == 0:
            print("There are no files in the directory!")
        else:
            print(tabulate(table, DirClient.headers, tablefmt=tablefmt))
        logging.debug("Listing successful.")
    def register(self):
        p = DirPacket()
        p.action = DirCode.REGISTER.value
    def query(self):
        p = DirPacket()
        p.action = DirCode.QUERY.value

class DirHandler(protocol.Handler):
    def setup(self):
        logging.debug("Connected %s:%d" % self.client_address)
    def handle(self):
        while True:
            r = self.recv()
            action = r.get_action()
            if action == DirCode.BYE:
                logging.debug("Client says bye, we say bye back and quit!")
                self.send(r)
                break
            elif action == DirCode.LIST:
                logging.debug("Client says wants the listing of files!")
                for f in self.server.file_list:
                    logging.debug("Sending file record: %s" % str(f))
                    self.send(f)
                logging.debug("Sending the empty record to signal end!")
                self.send(DirPacket())
            # just send back the same data, but upper-cased
    def finish(self):
        logging.debug("Disconnected %s:%d" % self.client_address)

#self.server.file_list.append(self.data.id)

'''
p=DirPacket()
print("SIZE OF PACKET")
print(ct.sizeof(p))
print(DirCode.BYE.value)
print(DirCode(0) == DirCode.BYE)
p.id = 123
packed = protocol.pack(p)
unpacked = protocol.unpack(packed,DirPacket)
print(protocol.debug_hex(bytearray(protocol.pack(p))))

s = DirPacket()
s.id = 0
print(protocol.debug_hex(bytearray(protocol.pack(s))))
'''

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
