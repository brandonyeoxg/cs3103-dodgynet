import puncher
from enum import Enum
import ctypes as ct
import logging
import commons

class P2pCode(Enum):
    REQUEST = 1
    DATA = 2

class P2pPacket(ct.Structure):
    _fields_ = [("action", ct.c_ushort),
                ("chunk_id", ct.c_ushort),
                ("md5_digest", ct.c_ubyte * 16),
                ("data", ct.c_ubyte * 1000)]
    def set_action(self, action):
        self.action = action.value
    def get_action(self):
        return PuncherCode(self.action)
    def __str__(self):
        return "%s:%s:%s" % (self.get_action(),
            self.chunk_id,
            str(self.id))
    def set_md5(self, bytes):
        self.md5_digest = protocol.b2cb(bytes, 16)
    def get_md5(self):
        return protocol.cb2b(self.md5_digest)
    def compute_md5(self):
        pass
    def check_md5(self):
        commons.md5sum(self.data)

class P2pEndpointClient(puncher.PuncherConnClient):
    def __init__(self, r, _id, server_addr=(puncher.PUB_IP, puncher.PORT)):
        puncher.PuncherConnClient.__init__(r, _id, server_addr)
        self.set_type(self.addr, P2pPacket)
    def incoming_endpoint(self, p):
        logging.fatal("Endpoint, processing new packet.")
        if p.get_action() != P2pCode.REQUEST:
            logging.fatal("Cannot process anything else but request messages!")
        
        p.id = self.n_incoming
        return p
    def send_data(self, bytes, chunk_id):
        p = P2pPacket()
        p.set_action(P2pCode.REQUEST)
        p.chunk_id
    def file_to_mem(self, file_name):
        self.file_name = file_name
        self.file_size = os.path.getsize(file_name)
        self.num_chunks = math.ceil(self.file_size/CHUNK_SIZE)
        self.total_chunks = []
        self.completed_chunks = []
        for count in range(self.num_chunks):
              self.total_chunks.append(count)
              self.completed_chunks.append(True)

        fd = open(file_name, "rb")
        
        self.file_mem = []
        for chunk_num in self.total_chunks:
            fd.seek(chunk_num * CHUNK_SIZE)
            self.file_mem.append(fd.read(CHUNK_SIZE))
    def init_mem(self, file_name, file_size, total_chunks):
        self.file_name = file_name
        self.file_size = file_size
        self.num_chunks = len(total_chunks)
        self.total_chunks = total_chunks
        self.completed_chunks = [False] * self.num_chunks
        self.file_mem = [bytes()] * self.num_chunks 
    def mem_to_file(self):
        assert(self.get_incomplete_chunks() == [])
        fd = open(self.file_name, "wb")
        print(self.file_mem)
        file_mem_contiguous = bytes()
        for ea_b in self.file_mem:
            file_mem_contiguous+= ea_b
        file_mem_contiguous = file_mem_contiguous[:self.file_size]
        fd.write(file_mem_contiguous)
        fd.close()
    def save_chunk(self, data, chunk_num):
        self.file_mem[chunk_num] = data
        self.completed_chunks[chunk_num] = True


# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
