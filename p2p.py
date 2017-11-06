import puncher
from enum import Enum
import ctypes as ct
import logging
import commons
import math
import random
import pickle
import tracker
import protocol

class P2pCode(Enum):
    REQUEST = 1
    DATA = 2

CHUNK_SIZE = 1000

class P2pPacket(ct.Structure):
    _fields_ = [("action", ct.c_ushort),
                ("chunk_id", ct.c_ushort),
                ("md5_digest", ct.c_ubyte * 16),
                ("data", ct.c_ubyte * CHUNK_SIZE)]
    def set_action(self, action):
        self.action = action.value
    def get_action(self):
        return P2pCode(self.action)
    def __str__(self):
        return "%s:%s" % (self.get_action(),
            self.chunk_id)
    def set_md5(self, bytes):
        self.md5_digest = protocol.b2cb(bytes, 16)
    def get_md5(self):
        return protocol.cb2b(self.md5_digest)
    def compute_md5(self):
        self.md5_digest = commons.md5sum_bytes(self.data)
    def check_md5(self):
        return self.md5_digest == commons.md5sum_bytes(self.data)
    def set_data(self, bytes):
        self.data = protocol.b2cb(bytes, CHUNK_SIZE)
    def get_data(self):
        return protocol.cb2b(self.data)

class P2pEndpointClient(puncher.PuncherConnClient):
    def __init__(self, r, _id, server_addr=(puncher.PUB_IP, puncher.PORT)):
        puncher.PuncherConnClient.__init__(self, r, _id, server_addr)
        self.set_type(self.addr, P2pPacket)
    def incoming_endpoint(self, p):
        logging.fatal("Endpoint, processing new packet.")
        if p.get_action() != P2pCode.REQUEST:
            logging.fatal("Cannot process anything else but request messages!")

        p.set_data(self.fs.get_chunk(p.chunk_id))
        p.set_action(P2pCode.DATA)
        
        return p
    @classmethod
    def init_file_service(cls, fs):
        cls.fs = fs
    def request(self, chunk_id):
        p = P2pPacket()
        p.set_action(P2pCode.REQUEST)
        p.chunk_id = chunk_id
        self.send(p)
        p = self.recv()
        self.fs.save_chunk(p.data, p.chunk_id)

class P2pClient(object):
    def __init__(self, dodgy_p, server_ip, in_fd=None):
        self.fs = FileService(dodgy_p, in_fd)
        self.t_client = tracker.TrackerClient(dodgy_p.get_addr())
        self.my_id = self.t_client.join()
        logging.info("Client joined with id=%d" % self.my_id)
        P2pEndpointClient.init_file_service(self.fs)
        # Now we start the puncher
        self.p_client = puncher.PuncherClient(self.my_id, P2pEndpointClient, 
            (server_ip, puncher.PORT))
        self.p_client.join()
    def download(self, out_fd):
    
        if out_fd == None:
            out_fd = open(dodgy_p.get_name(), "wb")
        
        download_indices = self.fs.get_incomplete_chunks()
        while len(download_indices) > 0:

            for chunk_id in download_indices:

                logging.debug("Want chunk_id=%d" % chunk_id)
                peer_l = self.t_client.want(chunk_id)
                peer_id = random.choice(peer_l)
                
                # Now we connect to that peer
                peer = self.p_client.connect_cached(peer_id)
                peer.request(chunk_id)
                
                # Now we announce
                self.t_client.announce(chunk_id)

            download_indices = self.fs.get_incomplete_chunks()
        self.fs.mem_to_file(out_fd)
    def upload(self):
        n_chunks = self.fs.num_chunks
        logging.info("There are %d chunks in this file, announcing all of them." % n_chunks)
        # Now we announce the chunk_ids
        for chunk_id in range(1, n_chunks+1):
            self.t_client.announce(chunk_id)
    def shutdown(self):
        self.t_client.bye()
        self.p_client.bye()

class FileService(object):
    def __init__(self, dodgy_p, fd=None):
        self.file_name = dodgy_p.get_name()
        self.file_size = dodgy_p.file_size
        self.num_chunks = int(math.ceil(self.file_size/CHUNK_SIZE))
        self.total_chunks = []
        self.is_completed_chunks = []
        if fd==None:
            self.init_mem(dodgy_p)
        else:
            self.file_to_mem(dodgy_p, fd)
    def file_to_mem(self, dodgy_p, fd):
        self.file_mem = []
        for count in range(self.num_chunks):
            self.total_chunks.append(count)
            self.is_completed_chunks.append(True)
            fd.seek(count * CHUNK_SIZE)
            self.file_mem.append(fd.read(CHUNK_SIZE))
    def init_mem(self, dodgy_p):
        for count in range(1, self.num_chunks+1):
              self.total_chunks.append(count)
              self.is_completed_chunks.append(False)

        self.file_mem = [bytes()] * self.num_chunks 
    def mem_to_file(self, fd):
        assert(self.get_incomplete_chunks() == [])
        logging.info("Saving to file: %s" % fd.name)
        file_mem_contiguous = bytes()
        for ea_b in self.file_mem:
            file_mem_contiguous+= ea_b
        file_mem_contiguous = file_mem_contiguous[:self.file_size]
        fd.write(file_mem_contiguous)
        fd.close()
    def save_chunk(self, data, chunk_num):
        logging.debug("Save chunk_id=%d: %s" % (chunk_num, str(data)))
        self.file_mem[chunk_num-1] = data
        self.is_completed_chunks[chunk_num-1] = True
    def get_chunk(self, chunk_id):
        data = self.file_mem[chunk_id-1]
        logging.debug("Get chunk_id=%d: %s" % (chunk_id, str(data)))
        return data
    def get_incomplete_chunks(self):
        incomplete_indices = []
        for i,is_complete in zip(self.total_chunks, self.is_completed_chunks):
            if not is_complete:
                incomplete_indices.append(i)
        return incomplete_indices
# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
