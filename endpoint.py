import queue
import threading
import pickle
from UdpTrackerServer import *
from UdpTrackerClient import *
from enum import Enum
import Puncher

CHUNK_SIZE = 1024

class ProtocolCodes(Enum):
    RECEIVE_REQUEST_FROM_PEER = 1
    SENDING_CHUNK_TO_PEER = 2


class P2pProtocol(object):
    '''
    @classmethod
    #def pack(cls, protocol, fileHash, fileName, chunkNum, data):
    def pack(cls, fileName, chunkNum):
        #chunk the file

        file = open(fileName, "rb")
        file.seek((chunkNum) * CHUNK_SIZE)
        dataBytes = file.read(CHUNK_SIZE)
        load = {
            'protocol' : ProtocolCodes.SENDING_CHUNK_TO_PEER,
            #'fileHash' : 0, #to change later
            #'fileName' : fileName,
            'chunkNum' : chunkNum,
            #hash
            'data' : dataBytes
        }
        packet = pickle.dumps(load)

        return packet
    '''
    @classmethod
    def pack(cls, dataBytes, chunkNum):
        # port is a 16 bit data
        protocol = ProtocolCodes.SENDING_CHUNK_TO_PEER.value
        data = struct.pack("H", protocol)
        # chunkNum is a 16 bit data
        data += struct.pack("H", chunkNum)
        data += dataBytes
        print("[p2p] Packed: %s" % str((protocol, chunkNum, dataBytes)))
        print(data)
        return data
    @classmethod
    def leechPack(cls, fileName, chunkNum):
        # port is a 16 bit data
        protocol = ProtocolCodes.RECEIVE_REQUEST_FROM_PEER.value
        data = struct.pack("H", protocol)
        # chunkNum is a 16 bit data
        data += struct.pack("H", chunkNum)
        print("[p2p] Lpacked: %s" % str((protocol, chunkNum, None)))
        print(data)
        return data
    '''
    @classmethod
    def unpack(cls, data):
        response = pickle.loads(data)
        #filepath = response["filename"] + ".part" + str(response["chunkNum"])
        #file = open(filepath, "wb")
        #file.write(response["data"])
        #file.close()
        #chunkAvail.update({response["chunkNum"] : True})

        return response
    '''
    @classmethod
    def unpack(cls, data):
        print(data)
        protocol, = struct.unpack("H", data[0:2])
        chunkNum, = struct.unpack("H", data[2:4])
        if len(data) == 4:
            print("[p2p] Unpacked: %s" % str((protocol, chunkNum, None)))
            return protocol, chunkNum, None
        else:
            print("[p2p] Unpacked: %s" % str((protocol, chunkNum, data[4:])))
            return protocol, chunkNum, data[4:]

import os
import math
import itertools
class DummyEndpoint(object):
    def __init__(self, apuncher_addr, clientObj=None):
        self.p_queue = queue.Queue()
        self.c_queue = queue.Queue()
        self.weaklingP = Puncher.WeaklingProtocol(apuncher_addr, self.p_queue, self.c_queue)
        self.t = threading.Thread(target=self.thread_job)
        self.t.daemon = True
        self.clientObj = clientObj
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
    def get_incomplete_chunks(self):
        incomplete_indices = []
        for i,is_complete in zip(self.total_chunks, self.completed_chunks):
            if not is_complete:
                incomplete_indices.append(i)
        return incomplete_indices
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
        print("===============")
        print(self.completed_chunks)
    def thread_job(self):
        while True:
            item = self.p_queue.get()

            if item == None:
                print("[Client] Endpoint Terminate")
                break
            data, addr = item
            print("=============")
            print(data)
            #data = data.decode('utf-8')
            protocol, chunkNum, file_data = P2pProtocol.unpack(data)

            # seeder receving request
            if protocol == ProtocolCodes.RECEIVE_REQUEST_FROM_PEER.value:
                chunk_i = chunkNum
                packet = P2pProtocol.pack(self.file_mem[chunk_i], chunk_i)

                conn = self.weaklingP.client.connect(*addr)
                conn.send(packet)


            # leecher receiving response
            elif protocol == ProtocolCodes.SENDING_CHUNK_TO_PEER.value:

                self.save_chunk(file_data, chunkNum)
                #clientObj.announce(NO_CHUNK, chunkNum)

            '''
            if data == "Send me chunk 1.":
                print("[Client] Send Data[Here is chunk 1.]")
                conn = self.weaklingP.client.connect(addr[0])
                conn.send("Here is chunk 1.".encode('utf-8'))
            '''

    def start(self):
        self.t.start()
        self.weaklingP.start()

    def shutdown(self):
        print("[Client] Terminate Queue by put in None")
        self.p_queue.put(None)
        self.weaklingP.shutdown()
        #self.t.join(1)

    def get_input(self):
        
        download_indices = self.get_incomplete_chunks()
        while len(download_indices) > 0:

            for chunk_num in download_indices:

                print ('Chunk wanted: ' + str(chunk_num))
                self.clientObj.announce(chunk_num, NO_CHUNK)
                response = self.clientObj.listen_for_response()
                print(response)

                if len(response) > 0:
                    #interval = response['response']['interval']
                    peer_list = response['response']['peers']

                    addr = peer_list[0]['addr'] 
                    #addr = "127.0.0.1"

                    request = P2pProtocol.leechPack(self.file_name, chunk_num)
                    conn = self.weaklingP.client.connect(addr)
                    print("[EndPoint] Request Packet: %s" % str(request))
                    conn.send(request)

                    time.sleep(10)

            download_indices = self.get_incomplete_chunks()
            print("[Endpoint] Incomplete Chunks %s" % str(download_indices))
        self.mem_to_file()
        '''
        while True:
            print(self.weaklingP.get_identity() + '>', end='', flush=True)
            data = sys.stdin.readline()
            if data == 'Q':
                break
            addr_raw = data.split(':')
            addr = (addr_raw[0], int(addr_raw[1]))
            print("[Client] Request chunk 1.")
            conn = self.weaklingP.client.connect(*addr)
            conn.send("Send me chunk 1.".encode('utf-8'))
        '''
            
            # Now we send data
            
            #self.c_queue.put(data)

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
