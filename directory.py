from enum import Enum
import protocol
import ctypes as ct
from pprint import pprint
import logging
from tabulate import tabulate
import pickle
import os
import hashlib

class DirCode(Enum):
    BYE = 0         # Client
    LIST = 1        # Client
    REGISTER = 2    # Client
    QUERY = 3       # Client

# Add number of chunks
# Add file hash
class DirPacket(ct.Structure):
    NAME_LEN = 255
    DESC_LEN = 723
    _fields_ = [("id", ct.c_int),
                ("action", ct.c_ubyte),
                ("name_len", ct.c_ubyte),
                ("name", ct.c_char * NAME_LEN),
                ("desc_len", ct.c_int),
                ("desc", ct.c_char * DESC_LEN),
                ("md5_digest", ct.c_ubyte * 16),
                ("file_size", ct.c_int),
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
    def set_md5(self, bytes):
        self.md5_digest = protocol.b2cb(bytes, 16)
    def get_md5(self):
        return protocol.cb2b(self.md5_digest)
    def __str__(self):
        return self.get_name()

class DirServer(protocol.ThreadedTCPServer):
    def __init__(self, file_lookup={}, addr=('', 50817)):
        logging.debug("Starting DirServer.")
        protocol.ThreadedTCPServer.__init__(self, addr, DirHandler, DirPacket)
        self.file_lookup = file_lookup
        self.tracker_lookup = {}
        for f in self.file_lookup.values():
            self.start_tracker(f.port)
    def get_state(self):
        return self.file_lookup
    def start_tracker(self, port):
        logging.debug("[STUB]Create new Tracker at port=%d" % port)

class DirClient(protocol.TCPClient):
    headers = ["#", "File Name", "Description", "#Peers", 
                "Tracker Address", "MD5", "Size"]
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
            table.append([ p.id, p.get_name(), p.get_desc(), p.n_peers,
                            "%s:%d" % p.get_addr(), protocol.hex(p.get_md5(), ''),
                            p.file_size])
            p = self.recv()
        if len(table) == 0:
            logging.info("There are no files in the directory!")
        else:
            logging.info(tabulate(table, DirClient.headers, tablefmt=tablefmt))
        logging.debug("Listing successful.")
    def query(self, q_name, dodgy_file):
        p = DirPacket()
        p.action = DirCode.QUERY.value
        p.set_name(q_name)
        self.send(p)
        p = self.recv()
        # If name exist, write to disk
        if p.id != 0:
            if dodgy_file == None:
                dodgy_file = open(q_name+".dodgy", "wb")
            pickle.dump(p, dodgy_file)
            logging.info("Dodgy file downloaded and saved at [%s]." % 
                os.path.realpath(dodgy_file.name))
        else:
            logging.info("File %s does not exist on the directory!" % p.get_name())
    def register(self, file_upload, description):
        p = DirPacket()
        p.set_action(DirCode.REGISTER)
        p.set_name(os.path.basename(file_upload.name))
        p.set_desc(description)
        p.set_md5(self.md5sum(file_upload))
        p.file_size = self.get_size(file_upload)
        self.send(p)
        p = self.recv()
        if p.id != 0:
            logging.info("Registration of %s successful!" % p.get_name())
        else:
            logging.info("Registration %s not successful, file with name exist!" 
                % p.get_name())
    def md5sum(self, fd):
        md5 = hashlib.md5()
        length = md5.block_size * 128
        for chunk in iter(lambda: fd.read(length), b''):
            md5.update(chunk)
        digest = md5.digest()
        logging.debug("Digest: %s" % md5.hexdigest())
        return digest
    def get_size(self, fd):
        return os.path.getsize(os.path.realpath(fd.name))

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
                logging.debug("Client wants the listing of files!")
                for f in self.server.file_lookup.values():
                    logging.debug("Sending file record: %s" % str(f))
                    self.send(f)
                logging.debug("Sending the empty record to signal end!")
                self.send(DirPacket())
            elif action == DirCode.QUERY:
                q_name = r.get_name()
                logging.debug("Client wants to query a file: %s" % q_name)
                if q_name in self.server.file_lookup:
                    logging.debug("File exist, returning record.")
                    self.send(self.server.file_lookup[q_name])
                else:
                    r.id = 0
                    self.send(r)
            elif action == DirCode.REGISTER:
                if r.get_name() in self.server.file_lookup:
                    r.id = 0
                    self.send(r)
                else:
                    r.id = len(self.server.file_lookup) + 1
                    self.server.file_lookup[r.get_name()] = r
                    self.send(r)
                #self.id 
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
